---
name: electoral-dashboard-updater
description: Weekly update of Electoral Dashboard Google Sheet with latest 2026 race ratings and chamber balance
---

You are running the weekly Electoral Dashboard update for the 2026 election cycle.

NOTE: The actual Google Sheet rating updates are handled automatically by a local cron job on the user's Mac (run_weekly_update.sh), which runs update_sheet.py at 1pm PST every Monday. You do NOT need to run the Python script yourself.

Your job is research, summarization, and updating the Constants tab when chamber balance changes.

---

## STEP 1 — Check for membership changes (ALWAYS do this first)

Search for any of the following events since last Monday:
- Member resignations or deaths
- Party affiliation switches (any member leaving their party or becoming independent)
- Special election results (new members being sworn in)
- Senate appointments (governor appointments to fill vacant seats)

Sources to check:
- https://pressgallery.house.gov/member-data/party-breakdown (official count)
- https://clerk.house.gov
- Web search: "House resignation [current month] 2026", "Senate special election 2026", "member switches party 2026"

For each event found, note the member name, state/district, what changed, effective date, and net impact on R/D/I/Vacancy counts.

---

## STEP 2 — Update the Constants tab if balance changed

Sheet ID: 1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA

Use Google Drive MCP to read the current Constants tab. Check existing values for:
HOUSE_R, HOUSE_D, HOUSE_I, HOUSE_VACANCIES, SENATE_R, SENATE_D, SENATE_I

If any value has changed based on Step 1, update those cells in the Constants tab.
Always update LAST_UPDATED to today's date (YYYY-MM-DD) when making any changes.

Validation rules that must always hold:
- HOUSE_R + HOUSE_D + HOUSE_I + HOUSE_VACANCIES = 435
- Independents who caucus with a party still count as Independent (not R or D)
- A seat stays vacant until a successor is sworn in (not just when a special election is called)

---

## STEP 3 — Check race rating changes

Search for major 2026 race rating changes from the past week:
- Cook Political Report (cookpolitical.com)
- Sabato's Crystal Ball (centerforpolitics.org/crystalball)
- Inside Elections
- 270toWin

Focus on races moving to/from Toss-up, new retirements, and candidate entries that shift a race's outlook.

---

## STEP 4 — Cross-check the sheet

Use Google Drive MCP to read the current Senate, House, and Governors tabs.
Flag any races where the sheet rating appears stale compared to Step 3 findings.

---

## STEP 5 — Deliver the weekly briefing

Write a concise summary covering:

**Chamber Balance** (only if something changed this week)
**Notable Rating Shifts** — races that moved categories
**Environment Narrative** — generic ballot trend, major polling/fundraising news
**Candidate News** — retirements, announcements, primary results
**Sheet Flags** — races needing manual review

---

## Key reference data
- Sheet ID: 1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA
- Dashboard URL: https://ppothiawala-afk.github.io/electoral-dashboard/
- Ratings scale: Solid D, Likely D, Lean D, Toss-up, Lean R, Likely R, Solid R
- Official House balance: https://pressgallery.house.gov/member-data/party-breakdown
- Cron job log: ~/Documents/Claude/Projects/Electoral Dashboard/update_log.txt
