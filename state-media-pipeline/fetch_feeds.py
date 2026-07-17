#!/usr/bin/env python3
"""
fetch_feeds.py — RSS/Atom collector for the state-media pipeline (Layer 0).

Walks the feed registry (feeds_config.json), fetches each feed with
feedparser, normalizes items to a flat schema, dedupes across outlets
(hash of normalized title + published date, so the same AP story carried
by 30 outlets collapses to one), and writes items_raw.json.

NO sentiment, NO classification here — this stage only collects countable
facts (title, link, published, outlet, state, feed_url). Classification is
classify.py's job.

Offline mode: --fixtures DIR reads saved feed XML files instead of the
network. Fixture filenames must match the pattern <STATE>__<slug>.xml so the
collector can attribute each fixture to a registry feed. This is how the
pipeline is tested in a no-network sandbox.

Usage:
    python3 fetch_feeds.py                       # live network fetch
    python3 fetch_feeds.py --states CO,OH,HI     # limit to states
    python3 fetch_feeds.py --fixtures fixtures/  # offline, read saved XML
    python3 fetch_feeds.py --max-items 40        # cap items per feed
"""

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import feedparser
except ImportError:  # pragma: no cover
    print("feedparser is required: pip install feedparser", file=sys.stderr)
    raise

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "feeds_config.json"
OUT_PATH = HERE / "items_raw.json"
USER_AGENT = "Mozilla/5.0 (StateMediaPipeline collector; +https://parvezpothiawala.com)"


def slugify(outlet: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", outlet.lower()).strip("-")


def normalize_title(title: str) -> str:
    """Lowercase, strip an outlet-name suffix after a bullet/pipe, collapse
    whitespace and punctuation. This is the dedup key basis — the SAME wire
    story reprinted by many outlets normalizes identically."""
    t = title or ""
    # WordPress/States Newsroom titles often end with " • Outlet Name"
    t = re.split(r"\s+[•|•]\s+", t)[0]
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def item_date(entry) -> str:
    """Return an ISO date (YYYY-MM-DD) from whatever the feed provided."""
    for key in ("published_parsed", "updated_parsed"):
        tp = entry.get(key)
        if tp:
            return datetime(*tp[:6], tzinfo=timezone.utc).date().isoformat()
    # fall back to raw string date fields
    for key in ("published", "updated", "date"):
        raw = entry.get(key)
        if raw:
            return str(raw)[:10]
    return ""


def dedup_hash(norm_title: str, date: str) -> str:
    return hashlib.sha1(f"{norm_title}|{date}".encode("utf-8")).hexdigest()[:16]


def parse_feed_source(source, is_fixture: bool):
    """feedparser accepts a URL or a file path/bytes. Returns parsed struct."""
    if is_fixture:
        return feedparser.parse(str(source))
    return feedparser.parse(source, agent=USER_AGENT)


def collect_from_entries(parsed, feed_meta, max_items):
    rows = []
    for entry in parsed.entries[:max_items]:
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue
        summary = re.sub(r"<[^>]+>", " ", entry.get("summary", "") or "")
        summary = re.sub(r"\s+", " ", summary).strip()
        norm = normalize_title(title)
        date = item_date(entry)
        rows.append({
            "id": dedup_hash(norm, date),
            "title": title,
            "norm_title": norm,
            "summary": summary[:600],
            "link": link,
            "published": date,
            "state": feed_meta["state"],
            "outlet": feed_meta["outlet"],
            "feed_url": feed_meta["feed_url"],
        })
    return rows


def load_fixture_map(fixtures_dir: Path):
    """Map fixture files (STATE__slug.xml) to their path."""
    out = {}
    for p in sorted(fixtures_dir.glob("*.xml")):
        stem = p.stem  # e.g. CO__colorado-newsline
        state = stem.split("__", 1)[0].upper()
        out.setdefault(state, []).append(p)
    return out


def main():
    ap = argparse.ArgumentParser(description="Collect state-media RSS items.")
    ap.add_argument("--states", help="comma-separated 2-letter states to limit to")
    ap.add_argument("--fixtures", help="offline: directory of saved feed XML files")
    ap.add_argument("--max-items", type=int, default=60, help="cap items per feed")
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args()

    config = json.loads(CONFIG_PATH.read_text())
    feeds = config["feeds"]
    only = {s.strip().upper() for s in args.states.split(",")} if args.states else None
    if only:
        feeds = [f for f in feeds if f["state"] in only]

    fixtures_dir = Path(args.fixtures) if args.fixtures else None
    fixture_map = load_fixture_map(fixtures_dir) if fixtures_dir else {}
    offline = fixtures_dir is not None

    all_rows = []
    per_feed_counts = []
    feeds_ok = feeds_err = 0

    for f in feeds:
        state = f["state"]
        if offline:
            paths = fixture_map.get(state, [])
            if not paths:
                continue
            sources = [(p, True) for p in paths]
        else:
            sources = [(f["feed_url"], False)]

        for src, is_fix in sources:
            try:
                parsed = parse_feed_source(src, is_fix)
                rows = collect_from_entries(parsed, f, args.max_items)
                all_rows.extend(rows)
                per_feed_counts.append({"state": state, "outlet": f["outlet"],
                                        "source": str(src), "items": len(rows)})
                feeds_ok += 1
                print(f"  + {state} {f['outlet']}: {len(rows)} items")
                if not offline:
                    time.sleep(0.5)  # be polite to servers
            except Exception as e:  # noqa: BLE001
                feeds_err += 1
                print(f"  ! {state} {f['outlet']} failed: {e}", file=sys.stderr)

    # Dedup across outlets on (norm_title, published) -> keep first, record collapse
    seen = {}
    deduped = []
    collapsed = 0
    for r in all_rows:
        key = r["id"]
        if key in seen:
            collapsed += 1
            seen[key]["also_in"].append({"outlet": r["outlet"], "state": r["state"]})
            continue
        r = dict(r)
        r["also_in"] = []
        seen[key] = r
        deduped.append(r)

    total_in = len(all_rows)
    dedup_rate = round(collapsed / total_in, 4) if total_in else 0.0

    out = {
        "_comment": "Raw collected + deduped state-media items. No classification. "
                    "Dedup key = sha1(normalized_title | published_date).",
        "generated": datetime.now(timezone.utc).date().isoformat(),
        "mode": "fixtures" if offline else "live",
        "stats": {
            "feeds_ok": feeds_ok,
            "feeds_err": feeds_err,
            "items_collected": total_in,
            "items_after_dedup": len(deduped),
            "duplicates_collapsed": collapsed,
            "dedup_rate": dedup_rate,
        },
        "per_feed": per_feed_counts,
        "items": deduped,
    }
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"\n{len(deduped)} items ({total_in} collected, {collapsed} collapsed, "
          f"dedup_rate={dedup_rate}) -> {args.out}")


if __name__ == "__main__":
    main()
