# Electoral Dashboard — Auto-Updater Setup Guide

This guide walks you through the one-time setup needed to connect
`update_sheet.py` to your Google Sheet. Takes about 10 minutes.

---

## Step 1: Get your Google Sheet ID

Open your Google Sheet in the browser. The URL looks like:

```
https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit
```

The Sheet ID is the long string between `/d/` and `/edit`:

```
1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
```

Save this — you'll need it for running the script and setting up the scheduled task.

---

## Step 2: Create a Google Cloud Project & Service Account

1. Go to [https://console.cloud.google.com](https://console.cloud.google.com)
2. Click **Select a project** (top left) → **New Project**
   - Name it something like `electoral-dashboard`
   - Click **Create**

3. In the left menu, go to **APIs & Services → Library**
   - Search for **Google Sheets API** → click it → click **Enable**

4. In the left menu, go to **APIs & Services → Credentials**
   - Click **+ Create Credentials → Service Account**
   - Name: `electoral-updater`
   - Click **Create and Continue** → **Done** (skip optional steps)

5. Click on the service account you just created
   - Go to the **Keys** tab
   - Click **Add Key → Create new key → JSON → Create**
   - A file downloads automatically — this is your `service_account.json`

6. **Move `service_account.json`** into this folder:
   ```
   Electoral Dashboard/service_account.json
   ```

---

## Step 3: Share your Google Sheet with the service account

1. Open `service_account.json` in a text editor
2. Find the `client_email` field — it looks like:
   ```
   electoral-updater@your-project.iam.gserviceaccount.com
   ```
3. Open your Google Sheet
4. Click **Share** (top right)
5. Paste that email address → set permission to **Editor** → click **Send**

---

## Step 4: Test the script manually

Open Terminal and run:

```bash
cd ~/Documents/Claude/Projects/Electoral\ Dashboard

# First install dependencies (one-time):
pip3 install google-auth google-auth-oauthlib google-api-python-client requests beautifulsoup4 lxml

# Dry run first (scrapes but doesn't write):
python3 update_sheet.py --sheet-id YOUR_SHEET_ID --dry-run

# Full run (writes to sheet):
python3 update_sheet.py --sheet-id YOUR_SHEET_ID
```

Replace `YOUR_SHEET_ID` with the ID from Step 1.

---

## Step 5: Update the Scheduled Task with your Sheet ID

Once you have your Sheet ID, tell Claude:

> "Update the electoral dashboard scheduled task with my Sheet ID: `YOUR_SHEET_ID`"

Claude will update the weekly task so it runs automatically with the correct ID.

---

## How the updater works

Each week the script:

1. **Scrapes** Wikipedia's 2026 election ratings pages and Sabato's Crystal Ball
2. **Compares** each rating to what's currently in your Google Sheet
3. **Updates** only the cells that have changed (Senate, House, Governors, StateLeg)
4. **Logs** every change it makes (e.g. `Senate | GA: Toss-up → Lean D`)

Your Google Sheet then feeds automatically into the live dashboard at:
https://ppothiawala-afk.github.io/electoral-dashboard/

---

## File structure

```
Electoral Dashboard/
├── update_sheet.py          ← The updater script
├── service_account.json     ← Your Google Cloud credentials (keep private!)
├── SETUP_GUIDE.md           ← This file
└── Electoral Dashboard Data.xlsx  ← Local backup copy
```

> ⚠️ **Never share `service_account.json`** or commit it to GitHub.
> Add it to your `.gitignore` if you push this folder to a repo.
