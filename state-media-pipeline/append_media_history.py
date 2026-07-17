#!/usr/bin/env python3
"""
append_media_history.py — build the weekly media time-series (the lookback product).

Reads items_classified.json and appends ONE snapshot per generated-date to
media_history.json. Each snapshot records, per state and per topic, the
coverage VOLUME (item counts) plus the top entities. Counts only — no
sentiment, no judgment.

Snapshot schema:
  {"date": "2026-07-17",
   "national": {"topic_volume": {"climate": 12, ...}, "total_items": 40},
   "states": {
     "CO": {"total": 6,
            "topic_volume": {"climate": 3, "politics": 4, ...},
            "top_entities": [["Jared Polis", 3], ["EPA", 2]],
            "low_volume": false},
     ... },
   "meta": {"states_present": 8, "low_volume_states": [...]}}

Idempotent: re-running for a date REPLACES that date's snapshot (a same-week
re-run won't duplicate). Every skipped week is a hole in the trend charts, so
run this after every classification pass.

Usage:
    python3 append_media_history.py
    python3 append_media_history.py --low-volume-threshold 2
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASSIFIED = HERE / "items_classified.json"
HISTORY = HERE / "media_history.json"
TOPICS_PATH = HERE / "topics_config.json"

ALL_STATES = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL",
              "IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT",
              "NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI",
              "SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"]


def main():
    ap = argparse.ArgumentParser(description="Append a weekly media-coverage snapshot.")
    ap.add_argument("--low-volume-threshold", type=int, default=3,
                    help="states with fewer than N items are flagged low_volume")
    args = ap.parse_args()

    data = json.loads(CLASSIFIED.read_text())
    date = data.get("generated")
    if not date:
        raise SystemExit("items_classified.json has no 'generated' date — aborting.")
    allowed = json.loads(TOPICS_PATH.read_text())["allowed_topics"]

    per_state_topics = defaultdict(Counter)   # state -> topic -> count
    per_state_total = Counter()               # state -> item count
    per_state_entities = defaultdict(Counter)  # state -> entity -> count
    national_topics = Counter()

    for it in data["items"]:
        st = it["state"]
        if st == "US":
            # national source: count into national totals only, not a state cell
            for t in it["topics"]:
                national_topics[t] += 1
            continue
        per_state_total[st] += 1
        for t in it["topics"]:
            per_state_topics[st][t] += 1
            national_topics[t] += 1
        for e in it["entities"]:
            per_state_entities[st][e] += 1

    states_block = {}
    low_volume = []
    present = []
    for st in ALL_STATES:
        total = per_state_total.get(st, 0)
        if total == 0:
            # state absent from this snapshot — record explicitly, flag low_volume
            states_block[st] = {"total": 0,
                                "topic_volume": {t: 0 for t in allowed},
                                "top_entities": [], "low_volume": True}
            low_volume.append(st)
            continue
        present.append(st)
        is_low = total < args.low_volume_threshold
        if is_low:
            low_volume.append(st)
        states_block[st] = {
            "total": total,
            "topic_volume": {t: per_state_topics[st].get(t, 0) for t in allowed},
            "top_entities": per_state_entities[st].most_common(8),
            "low_volume": is_low,
        }

    snapshot = {
        "date": date,
        "national": {
            "topic_volume": {t: national_topics.get(t, 0) for t in allowed},
            "total_items": sum(per_state_total.values()),
        },
        "states": states_block,
        "meta": {
            "states_present": len(present),
            "states_all": len(ALL_STATES),
            "low_volume_states": low_volume,
            "backend": data.get("backend"),
        },
    }

    if HISTORY.exists():
        hist = json.loads(HISTORY.read_text())
    else:
        hist = {"_comment": "Weekly per-state, per-topic coverage-VOLUME snapshots "
                            "(counts only, no sentiment). Appended by "
                            "append_media_history.py. History is the product.",
                "snapshots": []}

    before = len(hist["snapshots"])
    hist["snapshots"] = [s for s in hist["snapshots"] if s["date"] != date]
    replaced = before != len(hist["snapshots"])
    hist["snapshots"].append(snapshot)
    hist["snapshots"].sort(key=lambda s: s["date"])

    HISTORY.write_text(json.dumps(hist, indent=1))
    verb = "replaced" if replaced else "appended"
    print(f"{verb} snapshot {date}: {len(present)} states present, "
          f"{len(low_volume)} low_volume, {snapshot['national']['total_items']} items "
          f"· {len(hist['snapshots'])} total snapshots -> {HISTORY.name}")


if __name__ == "__main__":
    main()
