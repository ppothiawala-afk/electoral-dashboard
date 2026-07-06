#!/usr/bin/env python3
"""
sync_fallbacks.py — regenerate index.html's DEFAULT_* fallback arrays from the
live Google Sheet, eliminating the two-sources-of-truth drift (the bug class
that kept "Open (Abbott term-limited)" alive after Abbott declared).

Runs in GitHub Actions after the weekly apply+verify (has Sheet credentials);
the workflow commits the refreshed index.html, so the fallback data is never
more than a week older than the Sheet.

Safety guards — the script ABORTS WITHOUT WRITING if:
  - any tab returns fewer rows than expected (Senate>=30, Governors>=30, House>=25)
  - any rating is outside the 7-point enum
  - a generated array block fails to round-trip (marker not found exactly once)

Usage: python3 sync_fallbacks.py --sheet-id <ID> [--dry-run]
"""

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

RATINGS = {"Solid D", "Likely D", "Lean D", "Toss-up", "Lean R", "Likely R", "Solid R"}
MIN_ROWS = {"Senate": 30, "Governors": 30, "House": 25}


def js(s):
    """Escape a string for a double-quoted JS literal."""
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def as_dicts(service, sheet_id, tab):
    rows = read_sheet(service, sheet_id, tab)
    if not rows:
        return []
    header = rows[0]
    return [dict(zip(header, r + [""] * (len(header) - len(r)))) for r in rows[1:]]


def build_senate(rows):
    out = []
    for r in rows:
        if str(r.get("Up in 2026", "")).strip().upper() != "YES":
            continue
        rating = str(r.get("Rating", "")).strip()
        if rating not in RATINGS:
            raise SystemExit(f"ABORT: Senate {r.get('State')} bad rating {rating!r}")
        open_ = str(r.get("Open", "")).strip().lower() == "true" or "open" in str(r.get("Incumbent", "")).lower()
        out.append(
            f'  {{state:"{js(r["State"].strip())}",incumbent:"{js(r.get("Incumbent","").strip())}",'
            f'party:"{js(r.get("Party","").strip())}",rating:"{rating}",open:{str(open_).lower()},'
            f'note:"{js(r.get("Notes", r.get("Note","")).strip())}",'
            f'challenger:"{js(r.get("Challenger","").strip())}"}},'
        )
    return out


def build_govs(rows):
    out = []
    for r in rows:
        if str(r.get("Election 2026", "")).strip().upper() != "YES":
            continue
        rating = str(r.get("Rating", "")).strip()
        if rating not in RATINGS:
            raise SystemExit(f"ABORT: Governors {r.get('State')} bad rating {rating!r}")
        open_ = str(r.get("Open", "")).strip().lower() == "true" or "open" in str(r.get("Incumbent", "")).lower()
        out.append(
            f'  {{state:"{js(r["State"].strip())}",incumbent:"{js(r.get("Incumbent","").strip())}",'
            f'party:"{js(r.get("Party","").strip())}",rating:"{rating}",open:{str(open_).lower()},'
            f'note:"{js(r.get("Notes", r.get("Note","")).strip())}"}},'
        )
    return out


def build_house(rows):
    out = []
    for r in rows:
        if not str(r.get("State", "")).strip():
            continue
        rating = str(r.get("Rating", "")).strip()
        if rating not in RATINGS:
            raise SystemExit(f"ABORT: House {r.get('State')}-{r.get('District')} bad rating {rating!r}")
        dist = str(r.get("District", "")).strip().zfill(2)
        out.append(
            f'  {{state:"{js(r["State"].strip())}",district:"{dist}",'
            f'incumbent:"{js(r.get("Incumbent","").strip())}",party:"{js(r.get("Party","").strip())}",'
            f'rating:"{rating}",note:"{js(r.get("Notes", r.get("Note","")).strip())}"}},'
        )
    return out


def replace_array(html, name, lines):
    pattern = re.compile(r"(const " + name + r" = \[\n).*?(\n\];)", re.S)
    if len(pattern.findall(html)) != 1:
        raise SystemExit(f"ABORT: marker for {name} not found exactly once in index.html")
    return pattern.sub(lambda m: m.group(1) + "\n".join(lines) + m.group(2), html, count=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet-id", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    from update_sheet import get_sheets_service, read_sheet  # noqa: PLC0415
    globals()["read_sheet"] = read_sheet  # used by as_dicts
    service = get_sheets_service(HERE / "service_account.json")

    builds = {}
    for tab, builder in [("Senate", build_senate), ("Governors", build_govs), ("House", build_house)]:
        rows = as_dicts(service, args.sheet_id, tab)
        lines = builder(rows)
        if len(lines) < MIN_ROWS[tab]:
            raise SystemExit(f"ABORT: {tab} produced only {len(lines)} rows (min {MIN_ROWS[tab]}) — refusing to overwrite fallbacks")
        builds[tab] = lines
        print(f"  {tab}: {len(lines)} rows from Sheet")

    html_path = HERE / "index.html"
    html = html_path.read_text()
    html = replace_array(html, "DEFAULT_SENATE", builds["Senate"])
    html = replace_array(html, "DEFAULT_GOVS", builds["Governors"])
    html = replace_array(html, "DEFAULT_HOUSE", builds["House"])

    if args.dry_run:
        print("dry run — index.html NOT written")
        return
    html_path.write_text(html)
    print("index.html fallback arrays regenerated from the Sheet.")


if __name__ == "__main__":
    main()
