# Electoral Dashboard (2026)

A weekly-updated dashboard tracking the 2026 U.S. election cycle: House/Senate/Governor
race ratings on a 7-point scale, live congressional chamber balance, and a per-week archive.

Public dashboard: https://ppothiawala-afk.github.io/electoral-dashboard/

---

## Architecture

Four layers:

1. **Research / briefing (manual, in Cowork).** Claude runs the
   `electoral-dashboard-updater` skill on request — researches membership changes and
   forecaster rating moves, writes `constants_patch.json` + `weekly_briefing_YYYY-MM-DD.md`,
   and appends a `history.json` entry. This is a **human-in-the-loop** step: it is NOT a
   scheduled API job. See `skills/electoral-dashboard-updater/SKILL.md`.
2. **Deterministic apply (GitHub Actions cron).** `.github/workflows/weekly-apply.yml` runs
   Mondays 20:00 UTC (1 PM PT) and on manual `workflow_dispatch`. It runs
   `update_sheet.py` (scrapes ratings + chamber balance) then `apply_constants_patch.py`
   (applies the committed patch), using the `GOOGLE_CREDENTIALS` repo secret, then commits
   the archived patch + `history.json` + briefings back — which redeploys Pages.
3. **Google Sheet** (ID `1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA`) — tabs Senate, House,
   Governors, StateLeg, Constants, published as CSV.
4. **GitHub Pages** — `index.html` reads the published CSVs live; `history.html` reads the
   co-located `history.json`.

```
 Cowork (Claude, manual)                 GitHub Actions (Mon 1 PM PT)
 ─────────────────────────               ────────────────────────────
 skill → constants_patch.json  ──git──▶  update_sheet.py ─▶ Google Sheet
        weekly_briefing_*.md             apply_constants_patch.py ─▶ Sheet
        history.json append              commit archive + history ─▶ Pages redeploy
```

Claude never writes to the Sheet directly (the Drive MCP is read-only); every write flows
through `constants_patch.json` and the audited apply script.

---

## Data flow & the sequencing fix

The old design had a same-day race: a 1 PM cron applied whatever patch existed, but Claude's
scheduled task wrote that week's patch *after* 1 PM — so every patch landed **7 days stale**.

The human-in-the-loop model removes the race entirely:

- You run the **research** step (the skill) **before Monday** and commit the resulting
  `constants_patch.json`.
- The Monday Actions job applies **that committed patch, same day**, and there is no dependency
  on a second scheduled research job firing on time.

If a week's patch was never committed, the apply job simply finds nothing to apply and the
dashboard holds last week's values — visible and safe, not silently corrupted.

---

## Chamber-balance data model (read before editing any number)

- **HOUSE counts are EXCLUSIVE** and partition all seats:
  `HOUSE_R + HOUSE_D + HOUSE_I + HOUSE_VACANCIES == 435`.
- **SENATE counts OVERLAP:** `SENATE_R + SENATE_D == 100`. The three independents
  (Sanders-VT, King-ME, Murkowski-AK) are counted **inside** the R/D caucus totals.
  `SENATE_I` (= 3) is informational and a **subset** — it is not added on top.
  `SENATE_R + SENATE_D + SENATE_I == 103` is **correct**, not a bug. Never "fix" the Senate to
  sum to 100 by lowering R/D to net out the independents.

These invariants are enforced in `validate_patch.py`, in `update_sheet.py`
(`check_chamber_invariants()` gates every Constants write), and in `apply_constants_patch.py`.

---

## Weekly rhythm

1. **Before Monday** — in Cowork, trigger the `electoral-dashboard-updater` skill. It runs its
   four contracts (pre-flight → data → output → post-flight), writes the patch + briefing,
   appends to `history.json`, and runs `validate_patch.py`.
2. **Commit & push** the new `constants_patch.json`, `weekly_briefing_*.md`, and
   `history.json` to the repo.
3. **Monday 1 PM PT** — GitHub Actions applies the patch to the Sheet, archives it as
   `constants_patch.applied_YYYY-MM-DD.json`, and commits the archive + history back (Pages
   redeploys automatically). Failures show red in the Actions tab and email you.
4. The skill's **pre-flight contract** catches a stuck pipeline next week: a leftover
   `constants_patch.json` (never applied) or a missing `history.json` entry triggers a
   ⚠️ PIPELINE ALERT instead of silently overwriting the pending patch.

---

## Files

| File | Purpose |
|---|---|
| `update_sheet.py` | Scrapes ratings (Wikipedia) + House balance (Press/Radio-TV Gallery); writes to the Sheet. All race tabs go through `update_ratings_in_tab()`. |
| `apply_constants_patch.py` | Applies `constants_patch.json`; validates invariants first; archives only on full success. |
| `validate_patch.py` | Standalone (no Google API) validator: schema, 435 / Senate==100 invariants, 7-point enum, ISO dates, compound-key rule, optional fixture key-uniqueness. |
| `constants_patch.json` | Pending payload the apply job consumes (present only when a patch is queued). |
| `history.json` | Per-week archive powering `history.html`. Appended once per week, ascending order. |
| `index.html` / `history.html` | GitHub Pages front-end. |
| `skills/electoral-dashboard-updater/SKILL.md` | Canonical weekly skill (four contracts). |
| `skills/SCHEDULED_TASK_SKILL.md` | Same content, staged for copying into the Claude scheduled-task folder (see MANUAL_STEPS.md). |
| `skills/electoral-dashboard-updater-workspace/` | Trigger evals + Layer-2 output evals + fixtures. |
| `attic/` | Vestigial one-off scripts and old data, kept for reference. |

---

## Setup

1. Ensure `.gitignore` is in place **before** the first push (it excludes
   `service_account.json` and all credentials — see MANUAL_STEPS.md).
2. Add the `GOOGLE_CREDENTIALS` repo secret (base64 of the service-account JSON) and enable
   Actions. Full instructions in `MANUAL_STEPS.md`.
3. Local runs (optional) need `pip install -r requirements.txt` and either
   `service_account.json` in this folder or the `GOOGLE_CREDENTIALS` env var.

### Running the evals

```bash
# Patch validator (against the pending patch)
python3 validate_patch.py constants_patch.json

# Layer-2 output evals (regression traps)
python3 skills/electoral-dashboard-updater-workspace/output_evals/run_output_evals.py
```
