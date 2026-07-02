#!/usr/bin/env python3
"""
Electoral Dashboard — constants_patch.json validator
====================================================
Standalone, dependency-free (stdlib only) machine check for a patch file.
Makes NO Google API calls. Used by:
  - the weekly SKILL post-flight contract (run before finishing a briefing),
  - apply_constants_patch.py (invariant gate before it writes to the Sheet),
  - the GitHub Actions workflow (fail-fast before the apply step),
  - run_output_evals.py (regression suite).

Checks performed:
  1. JSON parses; top-level shape matches the patch schema.
  2. HOUSE_R + HOUSE_D + HOUSE_I + HOUSE_VACANCIES == 435   (EXCLUSIVE counts).
  3. SENATE_R + SENATE_D == 100.                            (see overlap note)
  4. Every rating (updates + row_updates) is in the 7-point enum.
  5. All dates (LAST_UPDATED, ISO fields) are valid ISO YYYY-MM-DD.
  6. Senate / Governors row_updates use a COMPOUND key_cols that includes
     "Up in 2026" (Senate) / "Election 2026" (Governors), never bare ["State"].
  7. (optional, --sheet-csv DIR) each row_update key matches exactly one row
     in the corresponding fixture CSV — key-uniqueness against real data.

────────────────────────────────────────────────────────────────────────────
SENATE OVERLAP SEMANTICS (read before "fixing" any Senate number)
────────────────────────────────────────────────────────────────────────────
HOUSE counts are EXCLUSIVE and partition all 435 seats:
    HOUSE_R + HOUSE_D + HOUSE_I + HOUSE_VACANCIES == 435

SENATE counts OVERLAP. The three independents (Sanders-VT, King-ME,
Murkowski-AK) are counted INSIDE the caucus totals SENATE_R / SENATE_D:
    SENATE_R + SENATE_D == 100        <-- the only Senate sum invariant
    SENATE_I is informational (= 3), a SUBSET of the caucus counts.
NEVER "correct" the Senate to 100 by changing SENATE_R or SENATE_D to net out
SENATE_I. SENATE_R + SENATE_D + SENATE_I == 103 is CORRECT, not a bug.

Exit code 0 on success, 1 on any validation failure.

Usage:
  python3 validate_patch.py constants_patch.json
  python3 validate_patch.py constants_patch.json --sheet-csv fixtures/
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

VALID_RATINGS = {"Solid D", "Likely D", "Lean D", "Toss-up",
                 "Lean R", "Likely R", "Solid R"}

HOUSE_TOTAL = 435
SENATE_TOTAL = 100

# Tabs whose rows are two-per-state and therefore REQUIRE a compound key that
# disambiguates the seat that is actually up for election.
COMPOUND_KEY_REQUIRED = {
    "Senate": "Up in 2026",
    "Governors": "Election 2026",
}


class ValidationError(Exception):
    pass


def _is_iso_date(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _check_schema(patch: dict, errors: list):
    if not isinstance(patch, dict):
        errors.append("Top-level patch is not a JSON object.")
        return
    if "updates" in patch and not isinstance(patch["updates"], dict):
        errors.append("'updates' must be an object.")
    if "row_updates" in patch and not isinstance(patch["row_updates"], dict):
        errors.append("'row_updates' must be an object.")
    if "updates" not in patch and "row_updates" not in patch:
        errors.append("Patch has neither 'updates' nor 'row_updates' — nothing to apply.")


def _to_int(name, value, errors):
    try:
        return int(value)
    except (TypeError, ValueError):
        errors.append(f"{name} is not an integer: {value!r}")
        return None


def _check_house_invariant(updates: dict, errors: list):
    keys = ["HOUSE_R", "HOUSE_D", "HOUSE_I", "HOUSE_VACANCIES"]
    if not all(k in updates for k in keys):
        # Only enforce when the House block is present at all.
        present = [k for k in keys if k in updates]
        if present:
            errors.append(f"Partial House block: got {present}, need all of {keys}.")
        return
    vals = [_to_int(k, updates[k], errors) for k in keys]
    if any(v is None for v in vals):
        return
    total = sum(vals)
    if total != HOUSE_TOTAL:
        errors.append(
            f"HOUSE invariant violated: {vals[0]}R + {vals[1]}D + {vals[2]}I + "
            f"{vals[3]}V = {total}, expected {HOUSE_TOTAL} (House counts are EXCLUSIVE)."
        )


def _check_senate_invariant(updates: dict, errors: list):
    if "SENATE_R" not in updates or "SENATE_D" not in updates:
        present = [k for k in ("SENATE_R", "SENATE_D") if k in updates]
        if present:
            errors.append(f"Partial Senate block: got {present}, need both SENATE_R and SENATE_D.")
        return
    r = _to_int("SENATE_R", updates["SENATE_R"], errors)
    d = _to_int("SENATE_D", updates["SENATE_D"], errors)
    if r is None or d is None:
        return
    total = r + d
    if total != SENATE_TOTAL:
        errors.append(
            f"SENATE invariant violated: {r}R + {d}D = {total}, expected {SENATE_TOTAL}. "
            f"NOTE: independents (SENATE_I) are counted INSIDE R/D caucus totals — do NOT "
            f"subtract SENATE_I to reach 100. Only SENATE_R + SENATE_D must equal 100."
        )
    # Sanity: if SENATE_I is present, it must be a plausible subset, not additive.
    if "SENATE_I" in updates:
        i = _to_int("SENATE_I", updates["SENATE_I"], errors)
        if i is not None and (r + d + i) == SENATE_TOTAL and i > 0:
            errors.append(
                f"SENATE_R + SENATE_D + SENATE_I = {SENATE_TOTAL} — this means independents were "
                f"double-subtracted. Independents are INSIDE the caucus totals; SENATE_R + "
                f"SENATE_D alone must equal 100 (currently {total})."
            )


def _check_dates(updates: dict, errors: list):
    if "LAST_UPDATED" in updates and not _is_iso_date(updates["LAST_UPDATED"]):
        errors.append(f"LAST_UPDATED is not ISO YYYY-MM-DD: {updates['LAST_UPDATED']!r}")


def _check_update_ratings(updates: dict, errors: list):
    # No rating fields live in `updates` normally, but guard any that appear.
    for k, v in updates.items():
        if k.endswith("_RATING") and v not in VALID_RATINGS:
            errors.append(f"updates[{k!r}] = {v!r} is not a valid 7-point rating.")


def _check_row_updates(row_updates: dict, errors: list, fixtures: dict | None):
    for tab, spec in row_updates.items():
        if not isinstance(spec, dict):
            errors.append(f"row_updates[{tab!r}] must be an object.")
            continue
        key_cols = spec.get("key_cols")
        changes = spec.get("changes")
        if not isinstance(key_cols, list) or not key_cols:
            errors.append(f"row_updates[{tab!r}] missing non-empty 'key_cols' list.")
            key_cols = key_cols if isinstance(key_cols, list) else []
        if not isinstance(changes, list):
            errors.append(f"row_updates[{tab!r}] missing 'changes' list.")
            changes = []

        # Compound-key requirement for two-rows-per-state tabs.
        required = COMPOUND_KEY_REQUIRED.get(tab)
        if required and required not in key_cols:
            errors.append(
                f"row_updates[{tab!r}] uses key_cols={key_cols} — must include "
                f"{required!r} (compound key) so it targets the seat up for election, "
                f"not both rows for the state."
            )

        # Per-change validation.
        for idx, change in enumerate(changes):
            if not isinstance(change, dict):
                errors.append(f"row_updates[{tab!r}].changes[{idx}] is not an object.")
                continue
            key = change.get("key")
            # Key arity should match key_cols.
            if isinstance(key, list):
                if len(key) != len(key_cols):
                    errors.append(
                        f"row_updates[{tab!r}].changes[{idx}] key {key!r} has "
                        f"{len(key)} parts but key_cols has {len(key_cols)}."
                    )
            elif key is None:
                errors.append(f"row_updates[{tab!r}].changes[{idx}] missing 'key'.")
            elif len(key_cols) > 1:
                errors.append(
                    f"row_updates[{tab!r}].changes[{idx}] key {key!r} is scalar but "
                    f"key_cols has {len(key_cols)} columns — use a list."
                )

            rating = change.get("rating")
            if rating is not None and rating not in VALID_RATINGS:
                errors.append(
                    f"row_updates[{tab!r}].changes[{idx}] rating {rating!r} is not a "
                    f"valid 7-point rating."
                )

            # Fixture key-uniqueness.
            if fixtures is not None and key is not None and key_cols:
                _check_key_unique_in_fixture(tab, key_cols, key, fixtures, errors, idx)


def _load_fixture_csvs(sheet_csv_dir: str) -> dict:
    """Load fixture CSVs named <Tab>.csv (Senate.csv, House.csv, ...)."""
    import csv
    fixtures = {}
    d = Path(sheet_csv_dir)
    for csv_path in d.glob("*.csv"):
        tab = csv_path.stem
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        fixtures[tab] = rows
    return fixtures


def _check_key_unique_in_fixture(tab, key_cols, key, fixtures, errors, idx):
    rows = fixtures.get(tab)
    if not rows:
        errors.append(f"row_updates[{tab!r}]: no fixture CSV '{tab}.csv' found for uniqueness check.")
        return
    header = rows[0]
    try:
        key_idxs = [header.index(kc) for kc in key_cols]
    except ValueError as e:
        errors.append(f"row_updates[{tab!r}]: key column not in fixture header ({e}).")
        return
    target = key if isinstance(key, list) else [key]
    matches = 0
    for row in rows[1:]:
        vals = [row[i] if i < len(row) else "" for i in key_idxs]
        if vals == [str(t) for t in target]:
            matches += 1
    if matches != 1:
        errors.append(
            f"row_updates[{tab!r}].changes[{idx}] key {key!r} matches {matches} fixture "
            f"row(s) (expected exactly 1) with key_cols={key_cols}."
        )


def validate(patch: dict, fixtures: dict | None = None) -> list:
    """Return a list of error strings (empty == valid)."""
    errors: list = []
    _check_schema(patch, errors)
    if errors:
        return errors
    updates = patch.get("updates", {})
    row_updates = patch.get("row_updates", {})
    _check_house_invariant(updates, errors)
    _check_senate_invariant(updates, errors)
    _check_dates(updates, errors)
    _check_update_ratings(updates, errors)
    _check_row_updates(row_updates, errors, fixtures)
    return errors


def validate_file(path: str, sheet_csv_dir: str | None = None) -> list:
    with open(path, encoding="utf-8") as f:
        patch = json.load(f)
    fixtures = _load_fixture_csvs(sheet_csv_dir) if sheet_csv_dir else None
    return validate(patch, fixtures)


def main():
    parser = argparse.ArgumentParser(description="Validate a constants_patch.json file.")
    parser.add_argument("patch", help="Path to constants_patch.json")
    parser.add_argument("--sheet-csv", default=None,
                        help="Directory of fixture CSVs (<Tab>.csv) for key-uniqueness checks")
    args = parser.parse_args()

    try:
        errors = validate_file(args.patch, args.sheet_csv)
    except FileNotFoundError:
        print(f"ERROR: patch file not found: {args.patch}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: patch is not valid JSON: {e}")
        sys.exit(1)

    if errors:
        print(f"❌ VALIDATION FAILED ({len(errors)} issue(s)) for {args.patch}:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"✅ {args.patch} is valid.")
    sys.exit(0)


if __name__ == "__main__":
    main()
