#!/usr/bin/env python3
"""
Electoral Dashboard — One-Time Constants Tab Setup
===================================================
Run once to create the 'Constants' tab in your Google Sheet and seed it
with the current chamber balance figures.

After running this, update_sheet.py will maintain the tab automatically
every Monday, and the dashboard will read live values from it.

Usage:
  python3 setup_constants_tab.py --sheet-id 1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = Path(__file__).parent / "service_account.json"

# ── Current values as of June 2026 ───────────────────────────────────────────
# Update these if the numbers have changed before you run this script.
INITIAL_VALUES = {
    "HOUSE_R":        217,
    "HOUSE_D":        212,
    "HOUSE_I":        1,    # Kevin Kiley, CA-03, caucuses R
    "HOUSE_VACANCIES": 5,   # FL-20, CA-01, GA-14, TX-23, CA-14
    "SENATE_R":       53,
    "SENATE_D":       47,
    "SENATE_I":       2,    # Sanders-VT, King-ME caucus D; Murkowski-AK is R, NOT counted here (corrected 2026-08-03)
    "LAST_UPDATED":   "2026-06-02",
    "NOTES":          "Kiley (CA-03) is Independent but caucuses R. Vacancies: FL-20, CA-01, GA-14, TX-23, CA-14.",
}


def get_service():
    env_creds = os.environ.get("GOOGLE_CREDENTIALS")
    if env_creds:
        try:
            info = json.loads(base64.b64decode(env_creds).decode("utf-8"))
            creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            print("  ✓ Loaded credentials from GOOGLE_CREDENTIALS env var.")
            return build("sheets", "v4", credentials=creds)
        except Exception as e:
            print(f"  WARNING: GOOGLE_CREDENTIALS env var failed: {e}")
    creds = service_account.Credentials.from_service_account_file(str(SERVICE_ACCOUNT_FILE), scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def tab_exists(service, sheet_id, tab_name):
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    return any(s["properties"]["title"] == tab_name for s in meta.get("sheets", []))


def create_tab(service, sheet_id, tab_name):
    body = {"requests": [{"addSheet": {"properties": {"title": tab_name}}}]}
    service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()
    print(f"  ✓ Created '{tab_name}' tab.")


def write_constants(service, sheet_id, values_dict):
    rows = [["Key", "Value", "Notes"]]
    for key, val in values_dict.items():
        rows.append([key, val, ""])
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="Constants!A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()
    print(f"  ✓ Wrote {len(rows)-1} constants to 'Constants' tab.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet-id", required=True)
    args = parser.parse_args()

    print("=" * 55)
    print("Electoral Dashboard — Constants Tab Setup")
    print("=" * 55)

    if not os.environ.get("GOOGLE_CREDENTIALS") and not SERVICE_ACCOUNT_FILE.exists():
        print("ERROR: No credentials found. Set GOOGLE_CREDENTIALS env var.")
        sys.exit(1)

    print("\n[1/3] Authenticating...")
    service = get_service()

    print("\n[2/3] Checking for existing Constants tab...")
    if tab_exists(service, args.sheet_id, "Constants"):
        print("  Constants tab already exists — overwriting with current values.")
    else:
        create_tab(service, args.sheet_id, "Constants")

    print("\n[3/3] Writing initial values...")
    write_constants(service, args.sheet_id, INITIAL_VALUES)

    print("\n✅ Done! Next steps:")
    print("  1. Go to your Google Sheet → Constants tab → verify the values look right")
    print("  2. File → Share → Publish to web → select 'Constants' tab → CSV → copy URL")
    print("  3. Paste that URL as 'constants' in SHEET_URLS inside index.html")
    print("  4. The dashboard will now read live chamber balance from the sheet!")
    print(f"\n  Sheet: https://docs.google.com/spreadsheets/d/{args.sheet_id}/edit")


if __name__ == "__main__":
    main()
