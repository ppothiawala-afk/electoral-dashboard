#!/usr/bin/env python3
"""
classify.py — topic tagging + entity extraction for the state-media pipeline.

Pipeline stage 2. Reads items_raw.json, runs a KEYWORD PRE-FILTER first
(cheap, deterministic, and the cost-control gate), then tags the survivors
with the four locked topics and extracts entities. Writes items_classified.json.

Two tagging backends:
  * default  — batched calls to the Anthropic API (model
               claude-haiku-4-5-20251001), ANTHROPIC_API_KEY required.
               ONLY items that pass the keyword pre-filter are ever sent, so
               API volume is bounded.
  * --offline — no API. Topics come straight from which keyword lists matched;
               entities come from a lightweight proper-noun + gazetteer
               heuristic. Lets the demo run with no key.

HARD RULE: outputs are countable facts only — topic tags (from the locked
allowed set), entities, state, outlet, feed, url, date. NO sentiment, NO
judgment scores anywhere.

Logs skip/score ratios (pre-filter skip rate, API vs offline counts).

Usage:
    python3 classify.py --offline
    python3 classify.py                 # API mode (needs ANTHROPIC_API_KEY)
    python3 classify.py --batch-size 20 --max-api-items 500
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW_PATH = HERE / "items_raw.json"
TOPICS_PATH = HERE / "topics_config.json"
OUT_PATH = HERE / "items_classified.json"


def load_topics():
    cfg = json.loads(TOPICS_PATH.read_text())
    return cfg


def prefilter_match(text: str, keyword_lists: dict):
    """Return the set of topics whose keyword lists match `text`."""
    low = text.lower()
    matched = set()
    for topic, words in keyword_lists.items():
        for w in words:
            if w.lower() in low:
                matched.add(topic)
                break
    return matched


# ── offline entity extraction (heuristic, no judgment) ──────────────────────

STOPWORD_CAPS = {"The", "A", "An", "This", "That", "It", "He", "She", "They",
                 "In", "On", "At", "For", "And", "But", "Or", "Of", "To",
                 "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday", "January", "February", "March", "April",
                 "May", "June", "July", "August", "September", "October",
                 "November", "December"}


def extract_entities_offline(text: str, gazetteer):
    """Grab capitalized multi-word proper nouns + known gazetteer terms.
    Purely a mention list — no scoring, no ranking by importance."""
    ents = set()
    # capitalized runs of 1-4 words (e.g. "Sierra Club", "Gov. Jared Polis")
    for m in re.finditer(r"\b([A-Z][a-zA-Z.]+(?:\s+[A-Z][a-zA-Z.]+){0,3})\b", text):
        phrase = m.group(1).strip(".")
        first = phrase.split()[0]
        if first in STOPWORD_CAPS and " " not in phrase:
            continue
        if len(phrase) < 3:
            continue
        ents.add(phrase)
    for g in gazetteer:
        if g.lower() in text.lower():
            ents.add(g)
    # cap to keep noise down
    return sorted(ents)[:12]


# ── API tagging ─────────────────────────────────────────────────────────────

def classify_batch_api(client, model, batch, allowed_topics):
    """Send a batch of items to Claude; return list of {topics, entities}."""
    lines = []
    for i, it in enumerate(batch):
        lines.append(f"[{i}] TITLE: {it['title']}\n    SUMMARY: {it['summary'][:300]}")
    joined = "\n".join(lines)
    prompt = (
        "You are a classification function. For each numbered news item, return "
        "ONLY objective, countable facts. Do NOT assess sentiment, tone, bias, or "
        "importance.\n\n"
        f"Allowed topic tags (choose all that apply, may be empty): {allowed_topics}\n"
        "Definitions are locked; tag on the substance of the item.\n"
        "Also list proper-noun ENTITIES mentioned (people, organizations, agencies, "
        "companies, industries, places) — mentions only, no ranking.\n\n"
        "Return STRICT JSON: {\"results\":[{\"i\":0,\"topics\":[...],\"entities\":[...]}, ...]}\n\n"
        f"ITEMS:\n{joined}"
    )
    msg = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    data = json.loads(text)
    out = {}
    for r in data.get("results", []):
        idx = r.get("i")
        topics = [t for t in r.get("topics", []) if t in allowed_topics]
        out[idx] = {"topics": topics, "entities": r.get("entities", [])[:12]}
    return out


def main():
    ap = argparse.ArgumentParser(description="Topic-tag + entity-extract state-media items.")
    ap.add_argument("--offline", action="store_true",
                    help="no API: tag from keyword matches, heuristic entities")
    ap.add_argument("--batch-size", type=int, default=20, help="items per API call")
    ap.add_argument("--max-api-items", type=int, default=1000,
                    help="hard cap on items sent to the API (cost control)")
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--in", dest="infile", default=str(RAW_PATH))
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args()

    raw = json.loads(Path(args.infile).read_text())
    topics_cfg = load_topics()
    allowed = topics_cfg["allowed_topics"]
    keyword_lists = topics_cfg["keyword_prefilter"]
    keyword_lists = {k: v for k, v in keyword_lists.items() if not k.startswith("_")}
    gazetteer = topics_cfg["entity_extraction"]["gazetteer_hint"]

    items = raw["items"]
    total = len(items)

    # Stage A: keyword pre-filter (the cost gate)
    survivors = []
    skipped = 0
    for it in items:
        text = f"{it['title']} {it['summary']}"
        matched = prefilter_match(text, keyword_lists)
        it["_prefilter_topics"] = sorted(matched)
        if matched:
            survivors.append(it)
        else:
            skipped += 1

    print(f"pre-filter: {total} items -> {len(survivors)} survive, {skipped} skipped "
          f"(skip_rate={round(skipped/total,4) if total else 0})")

    classified = []
    api_calls = 0
    api_items = 0

    if args.offline:
        for it in survivors:
            text = f"{it['title']} {it['summary']}"
            entry = build_entry(it, it["_prefilter_topics"],
                                extract_entities_offline(text, gazetteer))
            classified.append(entry)
        backend = "offline_keyword"
    else:
        try:
            import anthropic
        except ImportError:
            print("anthropic package required for API mode: pip install anthropic",
                  file=sys.stderr)
            sys.exit(2)
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            print("ANTHROPIC_API_KEY not set. Use --offline for a key-free run.",
                  file=sys.stderr)
            sys.exit(2)
        client = anthropic.Anthropic(api_key=key)
        to_send = survivors[:args.max_api_items]
        overflow = survivors[args.max_api_items:]
        for start in range(0, len(to_send), args.batch_size):
            batch = to_send[start:start + args.batch_size]
            try:
                results = classify_batch_api(client, args.model, batch, allowed)
            except Exception as e:  # noqa: BLE001
                print(f"  ! API batch failed ({e}); falling back to keyword tags",
                      file=sys.stderr)
                results = {}
            api_calls += 1
            api_items += len(batch)
            for i, it in enumerate(batch):
                r = results.get(i)
                if r is None:
                    topics = it["_prefilter_topics"]
                    ents = extract_entities_offline(f"{it['title']} {it['summary']}", gazetteer)
                else:
                    topics = r["topics"] or it["_prefilter_topics"]
                    ents = r["entities"]
                classified.append(build_entry(it, topics, ents))
        # overflow beyond cap: keyword-tag so nothing is silently dropped
        for it in overflow:
            classified.append(build_entry(
                it, it["_prefilter_topics"],
                extract_entities_offline(f"{it['title']} {it['summary']}", gazetteer)))
        backend = f"anthropic:{args.model}"

    out = {
        "_comment": "Topic-tagged + entity-extracted items. Counts, not judgments: "
                    "no sentiment anywhere. topics from locked allowed set only.",
        "generated": datetime.now(timezone.utc).date().isoformat(),
        "backend": backend,
        "allowed_topics": allowed,
        "stats": {
            "items_in": total,
            "prefilter_survivors": len(survivors),
            "prefilter_skipped": skipped,
            "skip_rate": round(skipped / total, 4) if total else 0,
            "api_calls": api_calls,
            "api_items": api_items,
            "classified": len(classified),
        },
        "items": classified,
    }
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"classified {len(classified)} items via {backend} "
          f"(api_calls={api_calls}, api_items={api_items}) -> {args.out}")


def build_entry(it, topics, entities):
    return {
        "id": it["id"],
        "title": it["title"],
        "link": it["link"],
        "published": it["published"],
        "state": it["state"],
        "outlet": it["outlet"],
        "feed_url": it["feed_url"],
        "topics": sorted(set(topics)),
        "entities": entities,
        "also_in": it.get("also_in", []),
    }


if __name__ == "__main__":
    main()
