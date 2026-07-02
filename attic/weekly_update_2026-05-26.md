# Electoral Dashboard — Weekly Update (REVISED)
**Run date:** Tuesday, May 26, 2026 — second automated run  
**Data as of:** Cook Political Report / Sabato's Crystal Ball / Inside Elections (May 26, 2026)  
**Sheet ID:** 1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA

> **Note:** This replaces the earlier May 26 run. That run could not write to the sheet and some of its ratings (AK Senate as Lean D, GA Governor as Lean R) were not corroborated by multiple current sources. This revised report is based on cross-referenced Cook, Sabato, and search-verified data as of late May 2026.

---

## Execution Notes

The automated `update_sheet.py` script could **not complete** in the scheduled-task environment — the sandboxed Linux shell blocks all outbound Python HTTP via a proxy (403 Forbidden). This affects both web scraping (Wikipedia, Sabato) and the Google Sheets API write calls. The current sheet data was successfully **read** via the Google Drive MCP connector, and research was conducted via the built-in web search tool. The Google Sheet itself has **not been written to** this run.

**Action required:** Run the patch script below locally to apply confirmed changes, or apply them manually in the sheet.

---

## Rating Changes by Tab — Cross-Verified May 26, 2026

### Senate — **3 confirmed changes**

These three changes are confirmed across at least two sources (Sabato's Crystal Ball + corroborating search data), all dated April 13, 2026:

| State | Race | Current Rating (Sheet) | New Rating | Source | Notes |
|-------|------|----------------------|-----------|--------|-------|
| GA | Ossoff (D) vs Carter (R) | Toss-up | **Lean D** | Sabato (Apr 13) | Ossoff fundraising + polling advantage in Trump+3 state |
| NC | Open — Cooper (D) vs Whatley (R) | Toss-up | **Lean D** | Sabato (Apr 13) | Cooper's statewide brand strong; Whatley untested |
| OH | Husted (R) vs Brown (D) — Special | Lean R | **Toss-up** | Sabato (Apr 13) | Sherrod Brown brand competitive; Husted is weak incumbent |

**Senate competitive landscape after changes:**
- **Toss-up (3):** ME (Collins vs Mills), MI (open, Peters retiring), OH special (new)
- **Lean D (3):** GA (upgraded), NC (upgraded), NH (Shaheen open)
- **Lean R (1):** AK (Sullivan vs Peltola)
- **Likely D (1):** MN (Smith open)
- **Likely R (2):** IA (Ernst open), TX (Cornyn primary risk)

### House — **0 changes**
The House scraper in `update_sheet.py` refreshes the competitive district list but does not yet update individual district ratings (noted as a future enhancement). No bulk rating changes confirmed from Cook or Sabato for individual House districts this week. The existing toss-up districts tracked in the sheet (AZ-01, AZ-06, CO-08, FL-27, IA-01, IA-03, ME-02, MI-07, NE-02, NJ-07, NM-02, NY-04, NY-17, NY-19, OH-09, PA-07, PA-08, TX-28) are consistent with current reporting.

### Governors — **1 confirmed change**

| State | Race | Current Rating (Sheet) | New Rating | Source | Notes |
|-------|------|----------------------|-----------|--------|-------|
| MI | Open D seat (Whitmer term-limited) | Toss-up | **Lean D** | Cook Political (May 21) | No strong R candidate emerged; D primary producing credible options |

**Other competitive governor races — no change this run:**

| State | Current Rating | Status | Notes |
|-------|--------------|--------|-------|
| AZ | Toss-up | Holding | Sabato moved Lean D (Mar 19); Cook still Toss-up — keeping Toss-up pending consensus |
| GA | Toss-up | Holding | Kemp term-limited open R seat; R structural advantage but competitive |
| IA | Toss-up | Holding | Cook rates Toss-up (Rob Sand competitive); Sabato/IE rate Lean R — Cook used as primary source |
| NV | Toss-up | Holding | Lombardo (R incumbent) ran close in 2022; remains competitive |
| WI | Toss-up | Holding | Evers retiring; D environment helps but open seat in competitive state |
| KS | Lean R | Holding | Term-limited D Kelly; expected R flip in deep-R state |
| OH | Lean R | Holding | DeWine term-limited open R; Lean R per structural advantage |

### StateLeg — **0 confirmed changes**
No StateLeg rating changes confirmed from Sabato's Crystal Ball or other sources this week. The StateLeg scraper was not able to run (same network block). Current ratings remain as-is. Note: previous run mentioned MN and NH chamber shifts — these are not yet corroborated by Sabato's published ratings and are **not applied** this run.

---

## Summary

| Tab | Confirmed Changes | Notes |
|-----|-----------------|-------|
| Senate | **3** | GA, NC → Lean D; OH special → Toss-up |
| House | 0 | Scraper not runnable; no bulk moves confirmed |
| Governors | **1** | MI → Lean D (Cook, May 21) |
| StateLeg | 0 | Prior run's changes unconfirmed; not applied |
| **Total** | **4** | |

**Most notable shifts:** GA and NC Senate moving from Toss-up to Lean D represents the most significant development — two previously pure toss-up seats now favor Democrats, reflecting the broader national environment. Ohio's special election tightening to Toss-up also merits attention as Sherrod Brown mounts a comeback bid.

---

## Quick-Apply Patch Script

Save as `patch_2026_05_26.py` in the project folder and run locally:

```python
#!/usr/bin/env python3
"""Applies confirmed rating changes for week of May 26, 2026."""
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
        if row[fi] != filter_val: continue
        st = row[ki]
        if st in changes and row[ri] != changes[st]:
            print(f"  {tab} | {st}: {row[ri]!r} → {changes[st]!r}")
            row[ri] = changes[st]; rows[i] = row; n += 1
    if n:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"{tab}!A1",
            valueInputOption="RAW", body={"values": rows}).execute()
    print(f"  {tab}: {n} change(s) applied.")

svc = get_service()
patch(svc, "Senate",    "State", "Up in 2026",   "YES", "Rating", SENATE_CHANGES)
patch(svc, "Governors", "State", "Election 2026", "YES", "Rating", GOV_CHANGES)
print("Done.")
```

---

## Sources
- [Sabato's Crystal Ball 2026 Rating Changes](https://centerforpolitics.org/crystalball/2026-rating-changes/)
- [Sabato's Crystal Ball 2026 Senate](https://centerforpolitics.org/crystalball/2026-senate/)
- [Cook Political Report 2026 Senate Ratings](https://www.cookpolitical.com/ratings/senate-race-ratings)
- [Cook Political Report 2026 Governor Ratings](https://www.cookpolitical.com/ratings/governor-race-ratings)
- [Cook Political 2026 Governors Overview](https://www.cookpolitical.com/analysis/governors/governors-overview/2026-governors-ratings-huge-map-invites-whirlwind-competition)
- [270toWin — Sabato Senate 2026](https://www.270towin.com/2026-senate-election/sabatos-crystal-ball-senate-2026)
- [270toWin — Cook Governor 2026](https://www.270towin.com/2026-governor-election/cook-political-report-2026-governor)
- [Iowa Governor race — The Hill](https://thehill.com/homenews/campaign/5837106-rob-sand-iowa-governor-race-tossup/)
