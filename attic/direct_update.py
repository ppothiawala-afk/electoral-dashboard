#!/usr/bin/env python3
"""
Electoral Dashboard — Direct Updater
Run this locally (not in the Cowork sandbox) where outbound internet is available.

Usage:
  python3 direct_update.py

Credentials: uses ./electoral-dashboard-497521-95fc18adc4e7.json (already present)

Changes as of May 26, 2026 (sources: NPR / Cook Political Report):
  SENATE:
    NC  Toss-up → Lean D   (Cooper vs Whatley; Cook rates Lean D)
    GA  Toss-up → Lean D   (Ossoff favored; Cook rates Lean D)
    OH  Lean R  → Toss-up  (Husted appointed; Sherrod Brown running; Cook rates Toss-up)
    NE  Solid R → Likely R (Ricketts vs Osborn (I); Osborn competitive but not favored)
  GOVERNORS:
    AZ  Toss-up → Lean D   (Biggs leading R primary; far-right positions hurt vs Hobbs-era D)
"""

import json
import sys
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

SHEET_ID = "1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA"
CREDS_FILE = Path(__file__).parent / "electoral-dashboard-497521-95fc18adc4e7.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SENATE_UPDATES = {
    "NC": "Lean D",
    "GA": "Lean D",
    "OH": "Toss-up",
    "NE": "Likely R",
}

GOVERNOR_UPDATES = {
    "AZ": "Lean D",
}


def get_service():
    creds = service_account.Credentials.from_service_account_file(
        str(CREDS_FILE), scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def read_tab(service, tab):
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f"{tab}!A:Z"
    ).execute()
    return result.get("values", [])


def write_tab(service, tab, values):
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=f"{tab}!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()


def run():
    print("=" * 60)
    print("Electoral Dashboard — Weekly Updater (May 26, 2026)")
    print("Sources: NPR / Cook Political Report")
    print("=" * 60)

    service = get_service()
    print("✓ Authenticated\n")
    results = {}

    # ── Senate ──────────────────────────────────────────────────────────────
    print("[1/2] Updating Senate tab...")
    rows = read_tab(service, "Senate")
    header = rows[0]
    state_idx = header.index("State")
    up_idx = header.index("Up in 2026")
    rating_idx = header.index("Rating")
    changed = 0

    for i, row in enumerate(rows[1:], 1):
        while len(row) <= max(state_idx, up_idx, rating_idx):
            row.append("")
        if row[up_idx] != "YES":
            continue
        state = row[state_idx]
        if state in SENATE_UPDATES:
            new_r = SENATE_UPDATES[state]
            old_r = row[rating_idx]
            if old_r != new_r:
                print(f"  Senate | {state}: {old_r!r} → {new_r!r}")
                row[rating_idx] = new_r
                rows[i] = row
                changed += 1

    if changed:
        write_tab(service, "Senate", rows)
        print(f"  ✓ {changed} change(s) written.")
    else:
        print("  No changes needed.")
    results["Senate"] = changed

    # ── Governors ───────────────────────────────────────────────────────────
    print("\n[2/2] Updating Governors tab...")
    rows = read_tab(service, "Governors")
    header = rows[0]
    state_idx = header.index("State")
    elec_idx = header.index("Election 2026")
    rating_idx = header.index("Rating")
    changed = 0

    for i, row in enumerate(rows[1:], 1):
        while len(row) <= max(state_idx, elec_idx, rating_idx):
            row.append("")
        if row[elec_idx] != "YES":
            continue
        state = row[state_idx]
        if state in GOVERNOR_UPDATES:
            new_r = GOVERNOR_UPDATES[state]
            old_r = row[rating_idx]
            if old_r != new_r:
                print(f"  Governors | {state}: {old_r!r} → {new_r!r}")
                row[rating_idx] = new_r
                rows[i] = row
                changed += 1

    if changed:
        write_tab(service, "Governors", rows)
        print(f"  ✓ {changed} change(s) written.")
    else:
        print("  No changes needed.")
    results["Governors"] = changed

    print("\n" + "=" * 60)
    total = sum(results.values())
    print(f"TOTAL: {total} change(s) — Senate: {results['Senate']}, Governors: {results['Governors']}")
    print("✅ Done!")


if __name__ == "__main__":
    run()
