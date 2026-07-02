#!/usr/bin/env python3
"""
Applies confirmed rating changes for week of May 26, 2026.
Run from the Electoral Dashboard folder:
  python3 patch_2026_05_26.py

Changes applied:
  Senate  GA: Toss-up  → Lean D   (Sabato Apr 13, 2026)
  Senate  NC: Toss-up  → Lean D   (Sabato Apr 13, 2026)
  Senate  OH: Lean R   → Toss-up  (Sabato Apr 13, 2026 — special election)
  Governor MI: Toss-up → Lean D   (Cook Political May 21, 2026)
"""
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

SHEET_ID = "1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA"
SCOPES   = ["https://www.googleapis.com/auth/spreadsheets"]

SENATE_CHANGES = {
    "GA": "Lean D",   # Toss-up → Lean D (Sabato Apr 13)
    "NC": "Lean D",   # Toss-up → Lean D (Sabato Apr 13)
    "OH": "Toss-up",  # Lean R  → Toss-up (Sabato Apr 13, special)
}
GOV_CHANGES = {
    "MI": "Lean D",   # Toss-up → Lean D (Cook May 21)
}

def get_service():
    sa = Path(__file__).parent / "service_account.json"
    creds = service_account.Credentials.from_service_account_file(str(sa), scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)

def patch(svc, tab, key_col, filter_col, filter_val, rating_col, changes):
    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"{tab}!A:Z").execute().get("values", [])
    hdr = rows[0]
    ki, fi, ri = hdr.index(key_col), hdr.index(filter_col), hdr.index(rating_col)
    n = 0
    for i, row in enumerate(rows[1:], 1):
        while len(row) <= max(ki, fi, ri): row.append("")
        if row[fi] != filter_val:
            continue
        st = row[ki]
        if st in changes and row[ri] != changes[st]:
            print(f"  {tab} | {st}: {row[ri]!r} -> {changes[st]!r}")
            row[ri] = changes[st]
            rows[i] = row
            n += 1
    if n:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"{tab}!A1",
            valueInputOption="RAW", body={"values": rows}).execute()
        print(f"  -> {n} change(s) written to '{tab}'.")
    else:
        print(f"  -> No changes needed in '{tab}'.")

print("Electoral Dashboard — Patch 2026-05-26")
print("=" * 40)
svc = get_service()
print("\nApplying Senate changes...")
patch(svc, "Senate",    "State", "Up in 2026",   "YES", "Rating", SENATE_CHANGES)
print("\nApplying Governor changes...")
patch(svc, "Governors", "State", "Election 2026", "YES", "Rating", GOV_CHANGES)
print("\nDone. Verify at: https://docs.google.com/spreadsheets/d/" + SHEET_ID)
