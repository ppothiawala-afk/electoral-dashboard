#!/usr/bin/env python3
"""
Electoral Dashboard — Layer-2 output evals
==========================================
Fixture-based, machine-checkable regression suite. No LLM judge, no Google API.
Exercises validate_patch.py against a good sample patch and the four named
regression traps from the audit, plus a pipeline-state (pre-flight) trap.

Run:
  python3 run_output_evals.py

Exits 0 only if every case has its expected outcome.

Cases:
  1. good_patch                 -> expected VALID
  2. bad_murkowski_two_row      -> expected INVALID (bare Senate key_cols)
  3. bad_senate_103             -> expected INVALID (SENATE_R+SENATE_D != 100)
  4. bad_stale_vacancy          -> expected INVALID via vacancy-floor check
                                   (sum==435 but vacancies dropped below the
                                    fixture's known-good floor of 4)
  5. unapplied_patch (preflight)-> expected DETECTED (leftover constants_patch.json
                                   with no fresh applied-archive == pipeline alert)
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]          # .../Electoral Dashboard
FIXTURES = HERE / "fixtures"
PATCHES = HERE / "patches"

# Import the validator from the repo root.
sys.path.insert(0, str(REPO_ROOT))
import validate_patch  # noqa: E402


def _load_constants_floor():
    """Read the known-good HOUSE_VACANCIES floor from the Constants fixture."""
    import csv
    path = FIXTURES / "Constants.csv"
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if row and row[0] == "HOUSE_VACANCIES":
                return int(row[1])
    return 0


def check_vacancy_floor(patch: dict, floor: int) -> list:
    """
    Sheet-relative guard the patch-only validator cannot do: HOUSE_VACANCIES in
    the patch must not drop BELOW the known-good floor from the Constants
    fixture. This catches the stale-Press-Gallery regression (sum still 435 but
    vacancies zeroed out).
    """
    updates = patch.get("updates", {})
    if "HOUSE_VACANCIES" not in updates:
        return []
    try:
        v = int(updates["HOUSE_VACANCIES"])
    except (TypeError, ValueError):
        return [f"HOUSE_VACANCIES not an integer: {updates['HOUSE_VACANCIES']!r}"]
    if v < floor:
        return [
            f"HOUSE_VACANCIES {v} is below the known-good floor {floor} — "
            f"stale Press Gallery page. Do not lower vacancies below a confirmed count."
        ]
    return []


def validate_patch_file(name: str, floor: int) -> list:
    with open(PATCHES / name, encoding="utf-8") as f:
        patch = json.load(f)
    fixtures = validate_patch._load_fixture_csvs(str(FIXTURES))
    errors = validate_patch.validate(patch, fixtures)
    errors += check_vacancy_floor(patch, floor)
    return errors


def preflight_detects_unapplied(folder_state: dict) -> bool:
    """
    Simulate the Contract-1 pre-flight. Returns True if it would raise a pipeline
    alert (leftover unapplied patch OR no fresh applied-archive for last Monday).

    folder_state: {"leftover_patch": bool, "applied_archive_last_monday": bool}
    """
    leftover = folder_state.get("leftover_patch", False)
    archived = folder_state.get("applied_archive_last_monday", False)
    return leftover or not archived


def main():
    floor = _load_constants_floor()
    results = []  # (name, passed, detail)

    # Patch-content cases: (file, expected_valid)
    patch_cases = [
        ("good_patch.json", True),
        ("bad_murkowski_two_row.json", False),
        ("bad_senate_103.json", False),
        ("bad_stale_vacancy.json", False),
    ]
    for fname, expected_valid in patch_cases:
        errors = validate_patch_file(fname, floor)
        actual_valid = not errors
        passed = actual_valid == expected_valid
        detail = "valid" if actual_valid else f"invalid ({len(errors)} issue(s))"
        if not passed:
            detail += " -- UNEXPECTED"
        if errors and not expected_valid:
            detail += f"; first: {errors[0]}"
        results.append((fname, passed, detail))

    # Pipeline-state (pre-flight) trap: unapplied patch.
    unapplied_state = {"leftover_patch": True, "applied_archive_last_monday": False}
    healthy_state = {"leftover_patch": False, "applied_archive_last_monday": True}
    r1 = preflight_detects_unapplied(unapplied_state)      # must be True
    r2 = preflight_detects_unapplied(healthy_state)        # must be False
    preflight_passed = (r1 is True) and (r2 is False)
    results.append((
        "unapplied_patch_preflight",
        preflight_passed,
        f"alert_on_unapplied={r1}, alert_on_healthy={r2}"
        + ("" if preflight_passed else " -- UNEXPECTED"),
    ))

    # Report
    print("=" * 68)
    print("Electoral Dashboard — Layer-2 output evals")
    print("=" * 68)
    all_pass = True
    for name, passed, detail in results:
        mark = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{mark}] {name}: {detail}")
    print("-" * 68)
    print(f"  vacancy floor from Constants fixture: {floor}")
    print(f"  {sum(1 for _, p, _ in results if p)}/{len(results)} cases passed.")
    print("=" * 68)

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
