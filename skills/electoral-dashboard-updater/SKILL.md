---
name: electoral-dashboard-updater
description: >
  Weekly research and update workflow for P-funk's 2026 Electoral Dashboard. Use this skill
  whenever running the weekly electoral briefing, checking congressional chamber balance,
  researching race rating changes from Cook/Sabato/Inside Elections, updating constants_patch.json,
  or delivering the Monday electoral summary. Trigger on any request that mentions the electoral
  dashboard, weekly briefing, chamber balance, race ratings, party switches, special-election
  winners, or the Google Sheet (ID: 1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA). Also trigger
  when asked whether last week's patch was applied or why the sheet looks stale.
---

# Electoral Dashboard — Weekly Update Skill

This skill runs the weekly research-and-update cycle for the 2026 Electoral Dashboard. You
produce a **weekly briefing** markdown file, a **`constants_patch.json`** the apply layer
consumes, and a new **`history.json`** entry.

It is structured as four **contracts** you must satisfy in order:
**Pre-flight → Data → Output → Post-flight.** Do not skip a contract. If a contract fails,
say so loudly in the briefing rather than papering over it.

**Key references**
- Sheet ID: `1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA`
- Project folder: `~/Documents/Claude/Projects/Electoral Dashboard/`
- Dashboard: https://ppothiawala-afk.github.io/electoral-dashboard/
- Ratings scale (7-point enum): **Solid D · Likely D · Lean D · Toss-up · Lean R · Likely R · Solid R**

**How this fits the pipeline (human-in-the-loop).** You (Claude, in Cowork) do the *research*
and write the patch/briefing whenever the user asks — this is NOT a scheduled API task. A
**GitHub Actions cron** (Mondays 20:00 UTC / 1 PM PT) runs the *deterministic apply layer*
(`update_sheet.py` + `apply_constants_patch.py`) against whatever patch has been committed,
then commits the archived patch + `history.json` back (which redeploys Pages). So: run research
**before** Monday; the Monday job applies the committed patch **same day** (this is what fixes
the old "patch applied 7 days stale" bug). Never assume a cron will run the research for you.

---

## CONTRACT 1 — PRE-FLIGHT (verify the pipeline is healthy before writing anything)

Before you research or overwrite `constants_patch.json`, confirm last week's cycle actually
completed. If it did not, you must NOT silently overwrite the pending patch.

**Check A — last week's patch was consumed.** In the project folder:
- There should be an archive `constants_patch.applied_YYYY-MM-DD.json` dated **last Monday**.
- There should be **no** leftover `constants_patch.json` from a prior week (a leftover means
  the apply job never ran — the patch is unapplied).

**Check B — history matches last week's briefing.** Read `history.json`. Its **last** `weeks[]`
entry's `date` and `briefing` should correspond to last week's `weekly_briefing_YYYY-MM-DD.md`.
A missing or mismatched last entry means Step "append to history" was skipped last week.

**If either check is violated → ⚠️ PIPELINE ALERT.**
- Lead the briefing with a bold `⚠️ PIPELINE ALERT` section naming exactly what's wrong
  (e.g. "constants_patch.json dated 2026-06-29 is still unapplied — the Monday apply job did
  not run" or "history.json is missing the 2026-06-29 entry").
- **Do NOT overwrite the pending `constants_patch.json`.** Overwriting destroys unapplied
  changes. Instead, tell the user to run/inspect the apply job first, and fold this week's
  findings into the alert rather than a fresh patch.
- Only once the pending patch is confirmed applied (archive present, no leftover) do you write
  a new patch.

> This contract exists because a dead cron went unnoticed for weeks — every run overwrote the
> previous unapplied patch. The pre-flight is the tripwire.

---

## CONTRACT 2 — DATA (what a correct patch and history entry look like)

### 2.1 Research the changes (Step-1 work)

Search for events **since last Monday**. This includes questions like *"did any senators switch
parties recently?"* and *"who won the [state-district] special election?"* — those ARE this
skill's job.

Events to find:
- Member deaths, resignations, party-affiliation switches.
- Special-election winners **being sworn in** (a seat stays vacant until the successor is sworn
  in — not when the election is called or won).
- Governor appointments filling Senate vacancies.
- Race rating changes from the four forecasters.

**Sources (check all):**
- House balance: https://pressgallery.house.gov/member-data/party-breakdown (official count)
- Vacancies: https://clerk.house.gov/Members/ViewVacancies
- Cook Political Report: https://www.cookpolitical.com/ratings
- Sabato's Crystal Ball: https://centerforpolitics.org/crystalball/2026-rating-changes/
- Inside Elections: https://www.insideelections.com/ratings
- 270toWin: https://www.270towin.com (aggregated views)
- Web searches: "House resignation [month] 2026", "Senate special election 2026",
  "member switches party 2026", "[forecaster] rating changes [month] 2026".

> ⚠️ **Stale-Press-Gallery trap.** The Press Gallery page updates only when departures are read
> on the House floor, so it can *lag* — e.g. showing 0 vacancies when 4 exist. Cross-check the
> Clerk's vacancy list. Never lower the vacancy count below a known-good figure just because the
> Press Gallery hasn't caught up. (The scraper enforces a vacancy floor and will skip-and-flag.)

### 2.2 Read the current sheet (read-only)

The Google Drive MCP provides **read-only** access to the sheet. Read the Constants, Senate,
House, and Governors tabs. Extract current chamber values and current ratings, and note where
the sheet lags forecaster consensus. **Never attempt a direct sheet write** — all writes flow
through `constants_patch.json`.

### 2.3 Invariants (must always hold)

- **HOUSE (exclusive):** `HOUSE_R + HOUSE_D + HOUSE_I + HOUSE_VACANCIES == 435`.
- **SENATE (overlapping):** `SENATE_R + SENATE_D == 100`. The three independents
  (**Sanders-VT, King-ME, Murkowski-AK**) are counted **INSIDE** the R/D caucus totals.
  `SENATE_I` (= 3) is informational and a **subset** — it is NOT added on top.
  > 🚫 **Senate-sums-to-103 trap.** `SENATE_R + SENATE_D + SENATE_I = 103` is **CORRECT**, not a
  > bug. NEVER "fix" the Senate to sum to 100 by lowering `SENATE_R`/`SENATE_D` to net out the
  > independents. The only Senate sum invariant is `SENATE_R + SENATE_D == 100`.
- Ratings ∈ the 7-point enum. Dates are ISO `YYYY-MM-DD`.
- **Kevin Kiley (CA-03)** is Independent but caucuses R → counts as **I** in `HOUSE_I`, not R.
  His sheet Party cell should be "I". (Same shape of edge case: a member who caucuses with a
  party is still counted as their registered affiliation.)

### 2.4 `constants_patch.json` schema

Placeholder values (`<int>`, `<Rating>`) shown below — **never hard-code live numbers into this
skill; always read them from the sheet each week** so future runs don't anchor on stale values.

```json
{
  "notes": "<one-line human summary of what changed and why>",
  "updates": {
    "HOUSE_R": <int>, "HOUSE_D": <int>, "HOUSE_I": <int>, "HOUSE_VACANCIES": <int>,
    "SENATE_R": <int>, "SENATE_D": <int>, "SENATE_I": <int>,
    "LAST_UPDATED": "<YYYY-MM-DD>",
    "NOTES": "Kiley (CA-03) is Independent but caucuses R. Vacancies (<N>): <list>."
  },
  "row_updates": {
    "Senate": {
      "key_cols": ["State", "Up in 2026"],
      "rating_col": "Rating",
      "extra_col_map": {"Challenger": "challenger", "Notes": "notes"},
      "changes": [
        {"key": ["<ST>", "YES"], "rating": "<Rating>", "challenger": "<name>", "notes": "<why>"}
      ]
    },
    "Governors": {
      "key_cols": ["State", "Election 2026"],
      "rating_col": "Rating",
      "changes": [
        {"key": ["<ST>", "YES"], "rating": "<Rating>"}
      ]
    },
    "House": {
      "key_cols": ["State", "District"],
      "rating_col": "Rating",
      "extra_col_map": {"Note": "note"},
      "changes": [
        {"key": ["<ST>", "<NN>"], "rating": "<Rating>", "note": "<forecaster + date>"}
      ]
    }
  }
}
```

**Invariants for the patch:**
- Always include all seven chamber fields in `updates` (even if unchanged — the apply layer
  reads all of them), plus `LAST_UPDATED` = today and the `NOTES` vacancy list.
- `HOUSE_*` must sum to 435; `SENATE_R + SENATE_D` must equal 100 (§2.3).
- **🚫 Murkowski two-row trap.** The Senate and Governors tabs have **TWO rows per state**
  (two senators; governors up in different years). `key_cols: ["State"]` alone matches BOTH
  rows and silently corrupts the wrong seat — this caused the Murkowski incident. Senate
  changes **must** use `["State", "Up in 2026"]` with `"key": ["ST", "YES"]`; Governors must
  use `["State", "Election 2026"]`. Every Senate/Governors change is **mandatory** compound-key.
- House changes use `["State", "District"]` with zero-padded two-char districts (`"01"`, not `1`).

### 2.5 `history.json` entry schema

Append **one** entry per week to `weeks[]` in **chronological (ascending) order — newest last**
(the `history.html` timeline renders `weeks[]` as columns left-to-right). Do not reorder or edit
prior entries.

```json
{
  "date": "<YYYY-MM-DD>",
  "label": "<Mon DD>",
  "briefing": "weekly_briefing_<YYYY-MM-DD>.md",
  "chamber": {
    "house_r": <int>, "house_d": <int>, "house_i": <int>, "house_vacancies": <int>,
    "senate_r": <int>, "senate_d": <int>, "senate_i": <int>,
    "notes": "<one-line summary of any membership changes>"
  },
  "rating_changes": [
    { "tab": "Senate|House|Governors", "race": "<ST — description>",
      "from": "<Rating>", "to": "<Rating>", "source": "<Forecaster, Date>" }
  ],
  "snapshot": {}
}
```

Only list genuine **forecaster rating moves** in `rating_changes`. Sheet-error corrections
(e.g. a D incumbent mislabeled Solid R) are data fixes, not rating moves — put them in the
briefing's corrections table, not in `history.json` `rating_changes`. Leave `snapshot` as `{}`
unless capturing a full snapshot (not required weekly).

---

## CONTRACT 3 — OUTPUT (the briefing)

Write `~/Documents/Claude/Projects/Electoral Dashboard/weekly_briefing_YYYY-MM-DD.md`.

### Inline citation rule (mandatory)

Every factual claim — rating moves, chamber counts, polling numbers, resignations, election
results — must carry a **hyperlinked source cited inline**, right next to the claim, so
stakeholders can verify without hunting a footer.

Format: `([Publication, Date](url))`

> **Alaska Senate** — ([Sabato's Crystal Ball, June 11](https://centerforpolitics.org/crystalball/2026-rating-changes/)) moved **Lean R → Toss-up**.
> Democrats lead the generic ballot D+6 ([RealClearPolling, June 20](https://www.realclearpolling.com/polls/state-of-the-union/generic-congressional-vote)).

Cite at the first sentence of a paragraph / first bullet of a same-source list; cite each bullet
if sources differ. Do not defer sources to a footer.

### Required sections (template)

```markdown
# Electoral Dashboard — Weekly Briefing
**Week of [Monday date]–[Sunday date], [year]**

---
[⚠️ PIPELINE ALERT — only if Contract 1 failed; describe the problem and what the user must do]

## Chamber Balance
[If unchanged: "No changes this week. Confirmed: XR | XD | XI | XV House / XR | XD | XI Senate
 ([House Clerk](https://clerk.house.gov/Members/ViewVacancies), [Press Gallery](https://pressgallery.house.gov/member-data/party-breakdown))."]
[If a correction is applied, add a brief ⚠️ note with source.]

Current N House vacancies:
- [ST-DD] ([Member, Party]) — [status, source inline]

Senate: XR / XD / XI — [Sanders-VT, King-ME, Murkowski-AK counted inside caucus totals; no change / explain]

---

## Notable Rating Shifts (Past Week)
### Senate
- **[State]** — ([Forecaster, date](url)) moved **[Old] → [New]**. Sheet shows [X]. [✅ / ⚠ stale]
### House
- **[Forecaster] ([date](url)):** [moves with sheet status]
### Governors
- **[State]** — ([Forecaster, date](url)) moved **[Old] → [New]**. [✅ / ⚠]

---

## Electoral Environment
[3–5 sentences; inline citation on every polling average / fundraising figure / structural claim]

---

## Candidate News
[Bullets; each cites its source inline]

---

## Sheet Updates
[Table of every change being applied via constants_patch.json]
| Tab | Race | Old | New | Source |
|---|---|---|---|---|

### No action needed
[Vacancies still pending; seats already correct]
```

Use `present_files` to share the briefing and `constants_patch.json` with the user.

---

## CONTRACT 3.5 — VERIFICATION (independent fact-check before finalizing)

The author of the briefing must not be its only checker. After drafting the briefing but
BEFORE writing the final files, run this two-part verification:

### 3.5.1 Subagent fact-check (fresh-context verifiers)

Spawn up to **three** verification subagents in parallel (Agent tool, general-purpose).
Each gets ONLY a claims list — never your sources, reasoning, or drafts — so its research
is independent and can't inherit your anchoring:

1. **Ratings verifier** — every rating move you're claiming this week, as bare claims
   ("Cook moved OH-Sen Likely R → Lean R on <date>"). Instructions: verify each against the
   forecaster's own site or two independent secondary sources; return per-claim
   CONFIRMED / CONTRADICTED (with what it found instead) / UNVERIFIABLE, with URLs.
2. **Membership & balance verifier** — claimed chamber counts, vacancies, resignations,
   deaths, party switches, special-election results. Same protocol; prefer primary sources
   (press gallery, clerk.house.gov, senate.gov, state SoS).
3. **Candidate/matchup verifier** — the nominee/matchup lines in news_config.json states
   with a primary in the past 2 weeks or next 2 weeks (this is the biggest staleness source
   — see the Abbott term-limit and Cornyn-lost-runoff misses of 2026-07-03). Return any
   matchup where the config or Sheet names the wrong candidates.

Do NOT spawn more than three; batch claims per verifier instead. Skip a verifier entirely
if it would receive zero claims this week.

### 3.5.2 Reconcile

- **CONFIRMED** → cite normally in the briefing.
- **CONTRADICTED** → investigate yourself with the verifier's URLs. Whoever has the primary
  source wins. Fix the patch/briefing, or if genuinely unresolved, drop the change from the
  patch and flag it.
- **UNVERIFIABLE** → keep the change ONLY if your own source is primary; flag it either way.

### 3.5.3 Verification section (mandatory in the briefing)

Add to the briefing, after Sheet Updates:

```markdown
## Verification
- ✅ N claims confirmed by independent fact-check (3 subagents)
- ⚠️ [claim] — CONTRADICTED: [what the verifier found] → [action taken]
- ⚠️ [claim] — UNVERIFIABLE: kept on primary source [link] / dropped
```

An all-✅ section with zero ⚠️ items and zero dropped changes is the normal, expected result.
If you skipped verification (e.g., zero changes this week), say so in this section explicitly.

---

## CONTRACT 4 — POST-FLIGHT (machine-verify before you finish)

Do NOT consider the run complete until both pass:

1. **Validate the patch.** Run the standalone validator (no Google calls):
   ```bash
   cd ~/Documents/Claude/Projects/Electoral\ Dashboard && python3 validate_patch.py constants_patch.json
   ```
   It checks schema, the 435 and Senate==100 invariants, the 7-point enum, ISO dates, and the
   compound-key requirement for Senate/Governors. If it exits nonzero, **fix the patch and
   re-run** — do not hand off a failing patch.

2. **Confirm the history append.** Re-read `history.json` and verify your new entry is present,
   is the **last** element, has the correct `date`/`briefing`, and that prior entries are
   untouched (this is the step that was silently skipped on 2026-06-29). Confirm the file still
   parses as JSON.

3. **Run the deterministic verifier.** `python3 verify_dashboard.py --local` — checks
   news_analysis.json schema/freshness, config consistency, rating enums in the dashboard
   fallbacks, State News wiring, pending-patch validity, and history ordering. Fix any ❌
   before finishing. (The Actions job re-runs this plus live-Sheet checks post-apply.)

Only after all three checks pass do you tell the user the weekly cycle is done.

---

## Environment notes

- Google Drive MCP is **read-only**. Cell writes go through `constants_patch.json` only.
- The apply layer is `apply_constants_patch.py` (handles `updates` via `update_constants()` and
  `row_updates` via `update_ratings_in_tab()` in `update_sheet.py`). It re-validates invariants
  and **only archives the patch on a fully successful apply** — a skipped/failed change leaves
  the file in place and exits nonzero, so the pending patch survives for a retry.
- A prior applied patch is archived as `constants_patch.applied_YYYY-MM-DD.json` — presence of
  last Monday's archive is your Contract-1 signal that the apply job ran.
