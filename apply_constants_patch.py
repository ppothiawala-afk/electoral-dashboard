#!/usr/bin/env python3
"""
Electoral Dashboard — Constants & Row Patch Applier
======================================================
Looks for a `constants_patch.json` file in this folder. If present, applies:
  1. its "updates" dict to the Constants tab via update_constants()
  2. its "row_updates" entries to House/Senate/Governors/StateLeg tabs via
     update_ratings_in_tab() — for rating changes, member/incumbent swaps,
     "VACANT" → name fills, etc.
Then archives the patch file (renamed with a timestamp) so it isn't
re-applied next run.

This is the mechanism Claude uses to push sheet updates (chamber balance,
race rating changes, House member swaps, etc.) discovered during the weekly
briefing — without needing broad write access to the sheet outside of this
script.

Patch file format (constants_patch.json):
{
  "notes": "Optional human-readable description of why these changes are being made",

  "updates": {
    "HOUSE_R": 218,
    "HOUSE_VACANCIES": 4
  },

  "row_updates": {
    "House": {
      "key_cols": ["State", "District"],
      "rating_col": "Rating",
      "extra_col_map": {"Incumbent": "incumbent", "Party": "party", "Note": "note"},
      "changes": [
        {"key": ["CA", "01"], "rating": "Solid R", "incumbent": "James Gallagher", "party": "R", "note": ""}
      ]
    },
    "Senate": {
      "key_cols": ["State"],
      "rating_col": "Rating",
      "changes": [
        {"key": "AK", "rating": "Toss-up"}
      ]
    }
  }
}

Notes on row_updates:
  - tab name must be one of: House, Senate, Governors, StateLeg (any tab with
    a rating column read via read_sheet/write_sheet)
  - key_cols: the column(s) that uniquely identify a row (e.g. State+District,
    or just State). For multi-column keys, "key" in each change entry is a list
    in the same order as key_cols; for a single-column key, "key" is a scalar.
  - IMPORTANT: key_cols must uniquely identify exactly ONE row. The Senate and
    Governors tabs have TWO rows per state (Class 2/3 senators, or governors
    with different election years) — using key_cols=["State"] alone will match
    both rows. Use key_cols=["State", "Up in 2026"] (with "key": ["AK", "YES"])
    to target only the seat that's actually up for election. A pre-flight check
    skips (with a warning) any change whose key matches != 1 row.
  - rating_col: the column to update with the new rating (must be a valid
    7-point rating: Solid D, Likely D, Lean D, Toss-up, Lean R, Likely R, Solid R)
  - extra_col_map (optional): maps sheet column names -> keys in each change
    entry, for updating non-rating columns (e.g. Incumbent name, Party, Note)
  - changes: list of {"key": ..., "rating": ..., <extra fields>...}

Usage:
  python3 apply_constants_patch.py --sheet-id 1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA

Run automatically by run_weekly_update.sh every Monday, after update_sheet.py.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

from update_sheet import (
    get_sheets_service,
    update_constants,
    update_ratings_in_tab,
    read_sheet,
    SERVICE_ACCOUNT_FILE,
)
import validate_patch


def _check_key_uniqueness(service, sheet_id, tab, key_cols, lookup_keys):
    """
    Pre-flight check: for each lookup_key, count how many rows in `tab`
    match it based on key_cols. Returns {lookup_key: match_count}.

    This guards against under-specified key_cols (e.g. ["State"] on a tab
    like Senate that has two rows per state) silently applying a change to
    multiple rows.
    """
    rows = read_sheet(service, sheet_id, tab)
    if not rows:
        return {k: 0 for k in lookup_keys}

    header = rows[0]
    try:
        key_idxs = [header.index(kc) for kc in key_cols]
    except ValueError as e:
        print(f"  WARNING: {e} — skipping uniqueness check for '{tab}'.")
        return {k: 1 for k in lookup_keys}  # assume OK, let update_ratings_in_tab report column errors

    counts = {k: 0 for k in lookup_keys}
    for row in rows[1:]:
        key_vals = tuple(row[idx] if idx < len(row) else "" for idx in key_idxs)
        row_key = key_vals[0] if len(key_vals) == 1 else key_vals
        if row_key in counts:
            counts[row_key] += 1

    return counts

SCRIPT_DIR = Path(__file__).parent
PATCH_FILE = SCRIPT_DIR / "constants_patch.json"


def apply_row_updates(service, sheet_id, row_updates: dict):
    """
    Apply each tab's row-level changes via update_ratings_in_tab().
    Returns (total_changed, skipped) where `skipped` counts any change that
    could not be applied safely (key matched != 1 row). A nonzero `skipped`
    means the patch did NOT fully apply and must NOT be archived.
    """
    total_changed = 0
    skipped = 0
    for tab, spec in row_updates.items():
        key_cols = spec.get("key_cols", [])
        rating_col = spec.get("rating_col", "Rating")
        extra_col_map = spec.get("extra_col_map", {})
        changes = spec.get("changes", [])

        if not key_cols or not changes:
            print(f"  WARNING: row_updates['{tab}'] missing key_cols or changes — skipping.")
            skipped += len(changes) if changes else 1
            continue

        # Build new_ratings dict: lookup_key -> {rating, <extra fields>}
        new_ratings = {}
        for entry in changes:
            key = entry.get("key")
            if isinstance(key, list):
                lookup_key = tuple(key) if len(key) > 1 else key[0]
            else:
                lookup_key = key
            data = {k: v for k, v in entry.items() if k != "key"}
            new_ratings[lookup_key] = data

        # Pre-flight: make sure each key matches exactly one row, so a too-broad
        # key (e.g. ["State"] on a tab with multiple rows per state) can't
        # silently overwrite unrelated rows.
        match_counts = _check_key_uniqueness(service, sheet_id, tab, key_cols, list(new_ratings.keys()))
        safe_ratings = {}
        for k, v in new_ratings.items():
            count = match_counts.get(k, 0)
            if count == 1:
                safe_ratings[k] = v
            else:
                skipped += 1
                print(f"  WARNING: '{tab}' key {k!r} matches {count} row(s) (expected 1) "
                      f"with key_cols={key_cols} — skipping this change. "
                      f"Add a more specific key_cols (e.g. include 'Up in 2026' or 'District').")

        if not safe_ratings:
            print(f"  No safe row updates to apply to '{tab}'.")
            continue

        print(f"  Applying {len(safe_ratings)} row update(s) to '{tab}'...")
        changed = update_ratings_in_tab(
            service, sheet_id, tab,
            rating_col_name=rating_col,
            key_cols=key_cols,
            new_ratings=safe_ratings,
            extra_col_map=extra_col_map,
        )
        print(f"  ✓ {changed} cell(s) updated in '{tab}'.")
        total_changed += changed

    return total_changed, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet-id", required=True)
    parser.add_argument("--service-account", type=str, default=None)
    args = parser.parse_args()

    sa_file = Path(args.service_account) if args.service_account else SERVICE_ACCOUNT_FILE

    if not PATCH_FILE.exists():
        print("[apply_constants_patch] No constants_patch.json found — nothing to do.")
        return

    print("[apply_constants_patch] Found constants_patch.json:")
    with open(PATCH_FILE) as f:
        patch = json.load(f)

    # ── Pre-apply validation gate ─────────────────────────────────────────────
    # Machine-check schema + the 435 / Senate==100 invariants + compound-key
    # requirements BEFORE touching the Sheet. A bad patch aborts here; the file
    # is left in place and we exit nonzero so the Actions run shows red.
    val_errors = validate_patch.validate(patch)
    if val_errors:
        print(f"  ERROR: patch failed validation ({len(val_errors)} issue(s)) — NOT applying:")
        for e in val_errors:
            print(f"    - {e}")
        print("  Leaving constants_patch.json in place. Exiting nonzero.")
        sys.exit(1)
    print("  ✓ Patch passed schema + invariant validation.")

    updates = patch.get("updates", {})
    row_updates = patch.get("row_updates", {})
    notes = patch.get("notes", "")
    if notes:
        print(f"  Notes: {notes}")

    constants_ok = True
    row_skipped = 0

    if not updates and not row_updates:
        print("  WARNING: Patch file has no 'updates' or 'row_updates' — nothing to apply.")
        print("  Leaving file in place; exiting nonzero for review.")
        sys.exit(1)

    service = get_sheets_service(sa_file)

    if updates:
        print(f"  Constants updates: {updates}")
        changed = update_constants(service, args.sheet_id, updates)
        print(f"  ✓ Applied {changed} change(s) to Constants tab.")
        # update_constants returns 0 both for "no diff" and "invariant refused".
        # Re-run the invariant check on the patched view to distinguish a genuine
        # refusal (which must block archiving) from a legitimate no-op.
        inv = validate_patch.validate({"updates": updates})
        if inv:
            constants_ok = False
            print("  ERROR: Constants updates violate invariants — apply incomplete.")
    else:
        print("  No Constants updates in this patch.")

    if row_updates:
        _, row_skipped = apply_row_updates(service, args.sheet_id, row_updates)
        if row_skipped:
            print(f"  ERROR: {row_skipped} row update(s) were skipped (key not unique).")
    else:
        print("  No row_updates in this patch.")

    # ── Archive ONLY on a fully successful apply ──────────────────────────────
    # Any skipped/failed change leaves the patch in place and exits nonzero so a
    # failed apply is visibly distinct from a successful one (audit §72 gap 2).
    if not constants_ok or row_skipped:
        print("  APPLY INCOMPLETE — leaving constants_patch.json in place, exiting nonzero.")
        sys.exit(1)

    today = datetime.date.today().isoformat()
    archive_name = SCRIPT_DIR / f"constants_patch.applied_{today}.json"
    PATCH_FILE.rename(archive_name)
    print(f"  ✓ Archived patch as {archive_name.name}")


if __name__ == "__main__":
    main()
