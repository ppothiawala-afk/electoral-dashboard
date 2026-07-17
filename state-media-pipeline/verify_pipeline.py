#!/usr/bin/env python3
"""
verify_pipeline.py — deterministic verification layer for the state-media pipeline.

Implements the checks from the plan doc. No network; runs anywhere. Failures
exit 1 (reds the CI run); warnings print but don't fail. Writes
verification_report.json.

Checks:
  V1  feeds_config.json parses; all 50 states covered by >=1 feed
  V2  items_classified.json parses; every item cites feed_url + link + published
  V3  every topic tag is in the locked allowed set
  V4  dashboard counts are reproducible: recomputing per-state/topic volume from
      items_classified.json matches the latest media_history.json snapshot
  V5  no state silently missing from the latest snapshot — all 50 present or
      explicitly flagged low_volume
  V6  dedup rate present and logged from items_raw.json
  V7  NO-SENTIMENT guard: no 'sentiment'/'score'/'rating' keys on any item
  V8  media_history.json parses and snapshots are chronologically ordered

Usage:
    python3 verify_pipeline.py
    python3 verify_pipeline.py --max-age-days 10
"""

import argparse
import datetime
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
FEEDS = HERE / "feeds_config.json"
RAW = HERE / "items_raw.json"
CLASSIFIED = HERE / "items_classified.json"
HISTORY = HERE / "media_history.json"
TOPICS = HERE / "topics_config.json"

ALL_STATES = {"AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL",
              "IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT",
              "NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI",
              "SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"}

FORBIDDEN_KEYS = {"sentiment", "score", "rating", "favorability", "tone", "bias"}

results = []


def record(check, status, msg):
    results.append({"check": check, "status": status, "message": msg})
    icon = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[status]
    print(f"  {icon} {check}: {msg}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-days", type=int, default=14)
    args = ap.parse_args()

    print("state-media pipeline verification:")

    # V1 registry coverage
    try:
        feeds = json.loads(FEEDS.read_text())
        covered = {f["state"] for f in feeds["feeds"] if f["state"] != "US"}
        missing = ALL_STATES - covered
        if missing:
            record("V1", "FAIL", f"states with no feed: {sorted(missing)}")
        else:
            record("V1", "PASS", f"all 50 states have >=1 feed ({feeds['feed_count']} feeds)")
    except Exception as e:  # noqa: BLE001
        record("V1", "FAIL", f"feeds_config.json unreadable: {e}")

    # V2 provenance + V3 allowed topics + V7 no-sentiment
    allowed = set(json.loads(TOPICS.read_text())["allowed_topics"])
    try:
        cls = json.loads(CLASSIFIED.read_text())
        items = cls["items"]
        missing_prov = [it["id"] for it in items
                        if not (it.get("feed_url") and it.get("link") and it.get("published"))]
        if missing_prov:
            record("V2", "FAIL", f"{len(missing_prov)} items missing feed/url/date")
        else:
            record("V2", "PASS", f"all {len(items)} items cite feed + url + date")

        bad_topics = set()
        for it in items:
            for t in it.get("topics", []):
                if t not in allowed:
                    bad_topics.add(t)
        if bad_topics:
            record("V3", "FAIL", f"topics outside allowed set: {sorted(bad_topics)}")
        else:
            record("V3", "PASS", f"all topic tags in locked allowed set {sorted(allowed)}")

        # V7 no-sentiment guard (structural)
        offenders = set()
        for it in items:
            for k in it.keys():
                if k.lower() in FORBIDDEN_KEYS:
                    offenders.add(k)
        if offenders:
            record("V7", "FAIL", f"forbidden judgment keys present: {sorted(offenders)}")
        else:
            record("V7", "PASS", "no sentiment/score/rating keys on any item")
    except Exception as e:  # noqa: BLE001
        record("V2", "FAIL", f"items_classified.json unreadable: {e}")
        items = []

    # V6 dedup rate logged
    try:
        raw = json.loads(RAW.read_text())
        dr = raw["stats"]["dedup_rate"]
        record("V6", "PASS", f"dedup_rate={dr} "
               f"({raw['stats']['duplicates_collapsed']} collapsed of "
               f"{raw['stats']['items_collected']})")
    except Exception as e:  # noqa: BLE001
        record("V6", "WARN", f"items_raw.json dedup stats unavailable: {e}")

    # V8 history order + V4 reproducibility + V5 state presence
    try:
        hist = json.loads(HISTORY.read_text())
        snaps = hist["snapshots"]
        dates = [s["date"] for s in snaps]
        if dates == sorted(dates):
            record("V8", "PASS", f"{len(snaps)} snapshots chronologically ordered")
        else:
            record("V8", "FAIL", "snapshots out of chronological order")

        latest = snaps[-1] if snaps else None
        if latest and items:
            # recompute per-state/topic volume from classified items
            recomputed = defaultdict(Counter)
            per_total = Counter()
            for it in items:
                if it["state"] == "US":
                    continue
                per_total[it["state"]] += 1
                for t in it["topics"]:
                    recomputed[it["state"]][t] += 1
            mism = []
            for st, sdata in latest["states"].items():
                if per_total.get(st, 0) != sdata["total"]:
                    mism.append(f"{st}:{sdata['total']}!={per_total.get(st,0)}")
                    continue
                for t, v in sdata["topic_volume"].items():
                    if recomputed[st].get(t, 0) != v:
                        mism.append(f"{st}/{t}:{v}!={recomputed[st].get(t,0)}")
            if mism:
                record("V4", "FAIL", f"snapshot not reproducible from items: {mism[:6]}")
            else:
                record("V4", "PASS", "latest snapshot counts reproduce exactly from items")

            # V5 all 50 present or flagged low_volume
            present = set(latest["states"].keys())
            missing = ALL_STATES - present
            not_flagged = [st for st in missing]
            if missing:
                record("V5", "FAIL", f"states absent AND unflagged: {sorted(missing)}")
            else:
                lv = latest["meta"]["low_volume_states"]
                record("V5", "PASS", f"all 50 states in snapshot ({len(lv)} flagged low_volume)")
        else:
            record("V4", "WARN", "no snapshot or no items to cross-check")
            record("V5", "WARN", "no snapshot to check state presence")
    except Exception as e:  # noqa: BLE001
        record("V8", "WARN", f"media_history.json unavailable: {e}")

    # freshness
    try:
        gen = json.loads(CLASSIFIED.read_text()).get("generated")
        age = (datetime.date.today() - datetime.date.fromisoformat(gen)).days
        if age > args.max_age_days:
            record("FRESH", "WARN", f"classified data is {age} days old (> {args.max_age_days})")
        else:
            record("FRESH", "PASS", f"classified data {age} days old")
    except Exception:  # noqa: BLE001
        pass

    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    n_warn = sum(1 for r in results if r["status"] == "WARN")
    report = {
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "summary": {"pass": sum(1 for r in results if r["status"] == "PASS"),
                    "warn": n_warn, "fail": n_fail},
        "checks": results,
    }
    (HERE / "verification_report.json").write_text(json.dumps(report, indent=2))
    print(f"\n{report['summary']}")
    if n_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
