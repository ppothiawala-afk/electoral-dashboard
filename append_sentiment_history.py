#!/usr/bin/env python3
"""
append_sentiment_history.py — build the sentiment time-series.

Reads news_analysis.json and appends one compact snapshot per generated-date
to sentiment_history.json:

  {"snapshots": [
    {"date": "2026-07-03",
     "states": {"OH": [{"type": "Senate", "sentiment": 51, "baseline": false,
                        "candidates": {"Sherrod Brown": 53, "Jon Husted": 50}}, ...]},
     ...}
  ]}

Idempotent: re-running for a date that's already recorded REPLACES that
snapshot (so a same-day re-score doesn't duplicate). Run after every weekly
news refresh — each skipped week is a hole in the trend charts.

Usage: python3 append_sentiment_history.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "news_analysis.json"
HISTORY = HERE / "sentiment_history.json"


def main():
    analysis = json.loads(ANALYSIS.read_text())
    date = analysis.get("generated")
    if not date:
        raise SystemExit("news_analysis.json has no 'generated' date — aborting.")

    snapshot = {"date": date, "states": {}}
    for st, sdata in analysis.get("states", {}).items():
        races = []
        for r in sdata.get("races", []):
            races.append({
                "type": r.get("type"),
                "sentiment": r.get("sentiment"),
                "baseline": bool(r.get("baseline")),
                "candidates": {c["name"]: c["sentiment"] for c in r.get("candidates", [])},
            })
        snapshot["states"][st] = races

    if HISTORY.exists():
        hist = json.loads(HISTORY.read_text())
    else:
        hist = {"_comment": "Weekly sentiment snapshots appended by append_sentiment_history.py. "
                            "sentiment = 0-100 D-favorability; baseline = rating-derived, not scored news.",
                "snapshots": []}

    before = len(hist["snapshots"])
    hist["snapshots"] = [s for s in hist["snapshots"] if s["date"] != date]
    replaced = before != len(hist["snapshots"])
    hist["snapshots"].append(snapshot)
    hist["snapshots"].sort(key=lambda s: s["date"])

    HISTORY.write_text(json.dumps(hist, indent=1))
    verb = "replaced" if replaced else "appended"
    print(f"{verb} snapshot {date}: {len(snapshot['states'])} states · "
          f"{len(hist['snapshots'])} total snapshots in {HISTORY.name}")


if __name__ == "__main__":
    main()
