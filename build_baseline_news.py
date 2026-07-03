#!/usr/bin/env python3
"""
build_baseline_news.py — fill news_analysis.json with rating-baseline entries
for every state that has a 2026 race but no scored news coverage.

Parses the DEFAULT_SENATE / DEFAULT_GOVS / DEFAULT_HOUSE arrays in index.html
(the dashboard's own race data), and for any state not already present in
news_analysis.json adds an entry per Senate/Governor race with:
  - sentiment derived from the forecaster rating (NOT scored news)
  - baseline: true  (the UI labels these "Rating baseline")
House-only states get a single "House" summary race listing the districts.

Scored entries (from the weekly Cowork collection) are never overwritten.
Run after each weekly scoring pass:  python3 build_baseline_news.py
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML = (HERE / "index.html").read_text()
OUT = HERE / "news_analysis.json"

RATING_BASELINE = {
    "Solid D": 75, "Likely D": 65, "Lean D": 58, "Toss-up": 50,
    "Lean R": 42, "Likely R": 35, "Solid R": 25,
}


def extract_array(name):
    m = re.search(name + r"\s*=\s*\[(.*?)\n\];", HTML, re.S)
    if not m:
        raise SystemExit(f"could not find {name} in index.html")
    entries = []
    for obj in re.finditer(r"\{([^}]*)\}", m.group(1)):
        d = dict(re.findall(r'(\w+):"([^"]*)"', obj.group(1)))
        if d.get("state"):
            entries.append(d)
    return entries


def baseline_race(rtype, r):
    rating = r.get("rating", "Toss-up")
    matchup = r.get("incumbent", "")
    if r.get("challenger"):
        matchup += f" vs. {r['challenger']}"
    return {
        "type": rtype,
        "matchup": matchup,
        "sentiment": RATING_BASELINE.get(rating, 50),
        "baseline": True,
        "summary": f"Rated {rating}. This race isn't in the weekly news collection yet — "
                   "the tone shown is a baseline from the forecaster rating, not scored coverage. "
                   "Ask Claude to add it to news_config.json if it heats up.",
        "candidates": [],
        "outlets": [],
        "articles": [],
    }


def main():
    senate = extract_array("const DEFAULT_SENATE")
    govs = extract_array("const DEFAULT_GOVS")
    house = extract_array("const DEFAULT_HOUSE")

    analysis = json.loads(OUT.read_text())
    scored = set(analysis["states"].keys())

    by_state = {}
    for r in senate:
        by_state.setdefault(r["state"], []).append(baseline_race("Senate", r))
    for r in govs:
        by_state.setdefault(r["state"], []).append(baseline_race("Governor", r))

    house_by_state = {}
    for r in house:
        house_by_state.setdefault(r["state"], []).append(r)
    for st, races in house_by_state.items():
        if st in by_state or st in scored:
            continue  # house races surface via the Seats Up list; no separate entry needed
        dists = ", ".join(f"{st}-{r.get('district','?')}" for r in races)
        avg = round(sum(RATING_BASELINE.get(r.get("rating", "Toss-up"), 50) for r in races) / len(races))
        by_state[st] = [{
            "type": "House",
            "matchup": f"Competitive districts: {dists}",
            "sentiment": avg,
            "baseline": True,
            "summary": f"Rated House battleground(s) only ({dists}). Baseline tone from ratings, not scored coverage.",
            "candidates": [], "outlets": [], "articles": [],
        }]

    added = 0
    for st, races in sorted(by_state.items()):
        if st in scored:
            continue
        analysis["states"][st] = {"races": races, "baseline": True}
        added += 1

    OUT.write_text(json.dumps(analysis, indent=2))
    print(f"Scored states: {len(scored)} · baseline states added: {added} · total: {len(analysis['states'])}")


if __name__ == "__main__":
    main()
