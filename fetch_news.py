#!/usr/bin/env python3
"""
fetch_news.py — RSS collector for the State News feature.

Pulls Google News RSS for each competitive race in news_config.json,
dedupes, tags candidate mentions and outlet lean, and writes news_raw.json.

Sentiment scoring is NOT done here — that happens in the Monday Cowork
routine (Claude reads news_raw.json, scores entity sentiment, and writes
news_analysis.json). This script is deterministic and dependency-free
(stdlib only) so it runs anywhere.

Usage:
    python3 fetch_news.py                # writes news_raw.json
    python3 fetch_news.py --states CO,OH # limit to specific states
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "news_config.json"
OUT_PATH = HERE / "news_raw.json"

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
USER_AGENT = "Mozilla/5.0 (ElectoralDashboard news collector; +https://ppothiawala-afk.github.io/electoral-dashboard/)"


def fetch_feed(query: str, retries: int = 2) -> str:
    url = GOOGLE_NEWS_RSS.format(query=urllib.parse.quote(query))
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            if attempt == retries:
                print(f"  ! feed failed after {retries+1} tries: {e}", file=sys.stderr)
                return ""
            time.sleep(2 * (attempt + 1))
    return ""


def parse_feed(xml_text: str):
    """Yield dicts: title, url, source, published (ISO date or '')."""
    if not xml_text:
        return
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as e:
        print(f"  ! XML parse error: {e}", file=sys.stderr)
        return
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        source = (item.findtext("source") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        iso = ""
        if pub:
            try:
                iso = parsedate_to_datetime(pub).astimezone(timezone.utc).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                iso = ""
        # Google News titles are usually "Headline - Outlet"; strip the outlet suffix
        if source and title.endswith(f" - {source}"):
            title = title[: -(len(source) + 3)].strip()
        if title:
            yield {"headline": title, "url": link, "source": source, "date": iso}


def find_mentions(text: str, candidates):
    """Return candidate names whose alias appears as a whole word in text."""
    hits = []
    low = text.lower()
    for c in candidates:
        for alias in [c["name"]] + c.get("aliases", []):
            if re.search(r"\b" + re.escape(alias.lower()) + r"\b", low):
                hits.append(c["name"])
                break
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", help="Comma-separated state codes to limit collection")
    args = ap.parse_args()

    config = json.loads(CONFIG_PATH.read_text())
    lean_table = config.get("outlet_lean", {})
    max_per_race = int(config.get("max_articles_per_race", 20))
    lookback = int(config.get("lookback_days", 21))
    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback)).strftime("%Y-%m-%d")

    only = {s.strip().upper() for s in args.states.split(",")} if args.states else None

    out = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lookback_days": lookback,
        "states": {},
    }
    seen_urls = set()

    for state, sconf in config["states"].items():
        if only and state not in only:
            continue
        print(f"{state}:")
        state_out = {"races": []}
        for race in sconf["races"]:
            print(f"  {race['type']} — \"{race['query']}\"")
            xml_text = fetch_feed(race["query"])
            articles = []
            for art in parse_feed(xml_text):
                if art["date"] and art["date"] < cutoff:
                    continue
                key = art["url"] or art["headline"]
                if key in seen_urls:
                    continue
                seen_urls.add(key)
                art["mentions"] = find_mentions(art["headline"], race.get("candidates", []))
                art["outletLean"] = lean_table.get(art["source"])  # None if unknown
                articles.append(art)
                if len(articles) >= max_per_race:
                    break
            print(f"    {len(articles)} articles kept")
            state_out["races"].append({
                "type": race["type"],
                "candidates": race.get("candidates", []),
                "articles": articles,
            })
            time.sleep(1)  # be polite to Google News
        out["states"][state] = state_out

    OUT_PATH.write_text(json.dumps(out, indent=2))
    total = sum(len(r["articles"]) for s in out["states"].values() for r in s["races"])
    print(f"\nWrote {OUT_PATH.name}: {len(out['states'])} states, {total} articles")


if __name__ == "__main__":
    main()
