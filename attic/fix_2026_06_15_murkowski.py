#!/usr/bin/env python3
"""
Corrective fix for 2026-06-15 patch run.

The constants_patch.json row_updates for Senate used key_cols=["State"] only,
which matched BOTH Alaska Senate rows (Sullivan, Class 2, up in 2026 AND
Murkowski, Class 3, not up until 2028) and incorrectly overwrote Murkowski's
Rating from "N/A" to "Toss-up".

This script restores Murkowski's row to Rating = "N/A". Sullivan's row
(Lean R -> Toss-up, per Crystal Ball's 2026-06-11 move) was correct and is
left unchanged.

Run from the Electoral Dashboard folder:
  GOOGLE_CREDENTIALS="$(base64 -i service_account.json)" python3 fix_2026_06_15_murkowski.py
"""
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os, base64, json

SHEET_ID = "1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_service():
    env_creds = os.environ.get("GOOGLE_CREDENTIALS")
    if env_creds:
        info = json.loads(base64.b64decode(env_creds).decode("utf-8"))
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        sa = Path(__file__).parent / "service_account.json"
        creds = service_account.Credentials.from_service_account_file(str(sa), scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def main():
    svc = get_service()
    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range="Senate!A:Z").execute().get("values", [])
    header = rows[0]
    state_i = header.index("State")
    incumbent_i = header.index("Incumbent")
    rating_i = header.index("Rating")
    up_i = header.index("Up in 2026")

    fixed = 0
    for i, row in enumerate(rows[1:], 1):
        while len(row) <= max(state_i, incumbent_i, rating_i, up_i):
            row.append("")
        if row[state_i] == "AK" and "Murkowski" in row[incumbent_i] and row[up_i].lower() == "no":
            if row[rating_i] != "N/A":
                print(f"  Senate | AK Murkowski: {row[rating_i]!r} -> 'N/A'")
                row[rating_i] = "N/A"
                rows[i] = row
                fixed += 1

    if fixed:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range="Senate!A1",
            valueInputOption="RAW", body={"values": rows}).execute()
        print(f"  -> {fixed} row(s) fixed in 'Senate'.")
    else:
        print("  -> No fix needed (Murkowski row already correct).")


if __name__ == "__main__":
    main()
