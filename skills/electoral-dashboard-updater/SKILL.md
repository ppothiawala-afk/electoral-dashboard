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

### Step 0 — SYNC THE CLONE FIRST (mandatory, before any file write)

**Run one script. Do not hand-roll the git.**

```bash
cd ~/Documents/Claude/Projects/"Electoral Dashboard" && python3 preflight_sync.py
```

`preflight_sync.py` clears stale locks at every depth, fetches, adjudicates any file that blocks
the merge, pulls with rename detection disabled, and verifies afterwards that nothing was lost.
Read its exit code and act on it:

| Exit | Meaning | What you do |
|---|---|---|
| **0** | Clone synced and clean | Proceed to Check A |
| **1** | Operational failure (locks unremovable, fetch/pull failed) | **Stop.** Report verbatim. If locks are stuck, the sandbox needs `mcp__cowork__allow_cowork_file_delete` granted on the folder |
| **2** | Real local divergence | **Stop and do not write any file.** Name the diverging paths in your report and let the user resolve |

**Why a script and not a judgment call (added 2026-08-03).** The recurring blocker is not the
locks — it is a *dirty worktree*. The apply job pushes a commit back, the clone never pulls it, and
the identical edits sit uncommitted locally, so `git pull` aborts with "Your local changes … would
be overwritten by merge." Clearing that needs `git checkout -- <files>`, which is off the allowlist.
But the safety argument is mechanical, not discretionary:

> if `sha256(worktree) == sha256(origin blob)` for every blocking file, then reverting and
> fast-forwarding returns the worktree to exactly the bytes it started with.

The script checks that equality for every file every time and **refuses when it does not hold** —
which is stricter than a human eyeballing a diff, and is why this no longer needs a human at all.
On a failed pull it restores anything it reverted, so it can never leave the worktree worse than it
found it. Use `--dry-run` to see the adjudication without changing anything.

> 🚫 **Never work around exit 2** by stashing, resetting, or re-running until it passes. Exit 2 means
> content exists locally that is not in the incoming commit — the Ghost integration files have been
> sitting uncommitted for weeks for exactly this reason. Destroying them is the 2026-07-29 class of
> incident, not a recovery.

> 🚫 **The rename trap (this destroyed a full week's patch on 2026-07-29).** The Monday apply job
> archives by *renaming* `constants_patch.json` → `constants_patch.applied_YYYY-MM-DD.json` and
> pushes that commit back. If you write a NEW `constants_patch.json` and it gets committed while
> the clone is still behind, the later `git pull` detects a 100%-similarity rename and merges the
> new content **into the archive path** — with **no conflict** and a harmless-looking diffstat
> (`constants_patch.json => constants_patch.applied_*.json | 0`). The result is no pending patch
> for Monday *and* an archive holding the wrong week's content. Pulling FIRST removes the
> divergence, so the rename has nothing to collide with. Never skip Step 0 to save time.

If the pull fails or the folder is not a clean checkout, **stop and report** rather than writing a
patch onto a diverged clone — say so in the briefing and let the user resolve it.

**Check A — last week's patch was consumed.** After Step 0, in the project folder:
- There should be an archive `constants_patch.applied_YYYY-MM-DD.json` dated **last Monday**.
- There should be **no** leftover `constants_patch.json` from a prior week (a leftover means
  the apply job never ran — the patch is unapplied).

> ⚠️ **The archive file is only a proxy — the Sheet is the authority.** Before declaring Check A
> failed, read the Sheet: if Constants `LAST_UPDATED` equals last Monday's date and last week's
> row changes are visibly live, the patch **was** applied and the missing archive just means the
> clone was stale (which Step 0 now fixes). In that case it is safe to write a new patch — say so
> explicitly in the briefing rather than halting. Only treat the patch as genuinely unapplied when
> the Sheet also fails to show it.

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
> On 2026-08-03 it read 217R/5V against the Clerk's 218R/4V because it still listed CA-01 as open
> six weeks after Gallagher was sworn in. **Report both numbers and say which is lagging** — do
> not silently pick one.

### 2.1a Research hazards (all three bit on 2026-08-03 — budget for them)

- **The forecaster sites are client-rendered. `WebFetch` returns an empty shell.**
  cookpolitical.com and centerforpolitics.org both fetch as blank. Escalate to the Claude-in-Chrome
  tools; if the extension is not connected, fall back to a **secondary source that quotes the
  primary verbatim and deep-links it** (Mediaite, Newsweek, The Hill and Politicalwire all
  reproduced the full Jul 30 Crystal Ball list). Cite the primary's own URL once you have
  confirmed its contents. Never cite a rating change you have only seen summarized.
- **🚫 Search summaries garble district numbers.** On 2026-08-03 the same Sabato change came back
  as **NJ-0**, **NJ-13** and **NJ-07** across three searches. The truth was **NJ-09**, and NJ-13
  does not exist. **Never put a district-level change into the patch on the strength of a search
  summary** — confirm the district against article body text or the forecaster, and let the
  Contract 3.5 ratings verifier see every district claim. A wrong key silently no-ops or, worse,
  corrupts the wrong seat.
- **The Drive read truncates long tabs.** `read_file_content` on the Sheet returns the House tab
  only partway (it stopped at OH-12 on 2026-08-03), so rows for later states are invisible. You
  can still patch them — `row_updates` sets by key regardless — but you cannot report a truthful
  "Old" value, and a key that does not match will make the whole apply exit nonzero. Say in the
  briefing which rows you could not see, and prefer keys you have verified exist.

### 2.2 Read the current sheet (read-only)

The Google Drive MCP provides **read-only** access to the sheet. Read the Constants, Senate,
House, and Governors tabs. Extract current chamber values and current ratings, and note where
the sheet lags forecaster consensus. **Never attempt a direct sheet write** — all writes flow
through `constants_patch.json`.

### 2.3 Invariants (must always hold)

- **HOUSE (exclusive):** `HOUSE_R + HOUSE_D + HOUSE_I + HOUSE_VACANCIES == 435`.
- **SENATE (overlapping):** `SENATE_R + SENATE_D == 100`. The **two** independents
  (**Sanders-VT, King-ME**) are counted **INSIDE** the D caucus total.
  `SENATE_I` (= 2) is informational and a **subset** — it is NOT added on top.
  > 🚫 **Senate-overlap trap.** `SENATE_R + SENATE_D + SENATE_I = 102` is **CORRECT**, not a
  > bug. NEVER "fix" the Senate to sum to 100 by lowering `SENATE_R`/`SENATE_D` to net out the
  > independents. The only Senate sum invariant is `SENATE_R + SENATE_D == 100`.
  > ⚠️ **Murkowski is NOT an independent — corrected 2026-08-03.** This skill previously said
  > `SENATE_I = 3`, counting Murkowski-AK alongside Sanders and King. That was wrong on the
  > official record: [senate.gov's party division](https://www.senate.gov/history/partydiv.htm)
  > lists 53 R / 45 D / 2 I, and the dashboard's own Senate tab has always carried Murkowski as
  > **R**. She has publicly floated leaving the GOP but has not done so. Do not restore the 3
  > without a primary source showing she actually switched — and if she ever does, she moves
  > *out* of `SENATE_R` and into the D-caucus total only if she caucuses D. Re-verify against
  > senate.gov rather than assuming; this error survived several months of weekly runs because
  > the number was hard-coded here and never re-checked.
- Ratings ∈ the 7-point enum. Dates are ISO `YYYY-MM-DD`.

> ⚠️ **No live facts in this file — audit this rule when you touch §2.3.** §2.4 already says
> "never hard-code live numbers into this skill," and §2.3 violated it for months with
> `SENATE_I = 3`. Every weekly run inherited the wrong value because it was written here and
> never re-checked against a primary source. The remaining hard-coded facts in this section are
> **435**, the two-independent Senate composition, and the Kiley/CA-03 case. Those are stable,
> but they are not permanent: 435 is statutory, the others are people who can change their minds.
> **Re-verify them against a primary source at least quarterly**, and when one turns out to be
> wrong, open a `decisions.json` entry rather than either silently changing it or ignoring it.
- **Kevin Kiley (CA-03)** is Independent but caucuses R → counts as **I** in `HOUSE_I`, not R.
  His sheet Party cell should be "I". (Same shape of edge case: a member who caucuses with a
  party is still counted as their registered affiliation.)

### 2.3a Forecaster scale & the Inside Elections "Tilt" (route 3 — resolved 2026-08-12)

The **Rating** column tracks **Cook** and **Sabato**, which share the dashboard's 7-point enum.
**Inside Elections uses a finer scale** with a **"Tilt"** tier between "Lean" and "Toss-up"
(most→least competitive per side: **Toss-up · Tilt · Lean · Likely · Solid**).

> 🚫 **Never import a bare IE rating — Tilt or otherwise — into the Rating cell.** IE is
> corroboration, not a mover on this dashboard. When IE diverges from the sheet (a Tilt, or any
> tier disagreement), log it to **`ie_watch.json`** and surface it in the briefing's **IE Tilt
> Watch** section (Contract 3) as a leading indicator. Cook and Sabato are the only forecasters
> that move the Rating cell.

- An `ie_watch.json` entry is **`open`** while IE and the sheet disagree.
- Set it **`confirmed`** (fill `confirmed_by`) when Cook or Sabato later move to match IE — that
  is the payoff: IE flagged the move early, and the log proves it.
- Set it **`faded`** when IE reverts to the sheet's rating with no Cook/Sabato follow.
- The file's `nearest_7pt` field is informational only; it is **not** written to the sheet.

Resolves `decisions.json` `2026-08-10-inside-elections-tilt-mapping`. Weekly refresh: Contract 3.9
step 7. Machine check: `verify_dashboard.py` L12-iewatch.

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

**Deep-link rule (mandatory):** every URL — in briefings, `news_analysis.json` articles, News
tab columns, or anywhere else — must link directly to the specific article/page being cited,
never a publisher homepage or section front. `https://www.politico.com` is a broken citation;
`https://www.politico.com/news/2026/07/06/maine-senate-collins-platner-00123456` is a citation.
If you cannot recover the exact article URL, find a different source you can deep-link — do not
substitute the homepage. (`verify_dashboard.py --local` fails on homepage-only URLs: L10-links.)

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

Senate: XR / XD / XI — [Sanders-VT and King-ME counted inside the D caucus total; Murkowski-AK is R; no change / explain]

---

## Notable Rating Shifts (Past Week)
### Senate
- **[State]** — ([Forecaster, date](url)) moved **[Old] → [New]**. Sheet shows [X]. [✅ / ⚠ stale]
### House
- **[Forecaster] ([date](url)):** [moves with sheet status]
### Governors
- **[State]** — ([Forecaster, date](url)) moved **[Old] → [New]**. [✅ / ⚠]

---

## IE Tilt Watch
[Inside Elections divergences from the sheet — leading indicators only; per 2.3a these do NOT move
the Rating cell. One line per open `ie_watch.json` entry; note any newly confirmed or faded.]
- **[Race]** — IE **[ie_rating]** ([date](url)) vs. sheet **[sheet_rating]**. [divergence in a few
  words; ⏳ open / ✅ confirmed by [Forecaster, date] / ⤵ faded]
[If nothing is open: "No open IE divergences."]

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
3. **Candidate/matchup verifier** — the nominee/matchup lines in news_config.json states,
   PLUS the entries in `election_calendar.json`: confirm upcoming event dates are correct,
   add newly-scheduled events (runoffs, conventions, specials), and update the notes of
   events that just resolved (winner names). Bump the file's `updated` field.
   with a primary in the past 2 weeks or next 2 weeks (this is the biggest staleness source
   — see the Abbott term-limit and Cornyn-lost-runoff misses of 2026-07-03). Return any
   matchup where the config or Sheet names the wrong candidates.

Do NOT spawn more than three; batch claims per verifier instead. Skip a verifier entirely
if it would receive zero claims this week.

### 3.5.2 Reconcile — this GATES the patch

- **CONFIRMED** → cite normally in the briefing.
- **CONTRADICTED** → investigate yourself with the verifier's URLs. Whoever has the primary
  source wins. Fix the patch/briefing. **If you cannot settle it against a primary source, the
  change is DROPPED from the patch automatically** — not kept with a caveat, not argued through.
  Log it in the Verification section and move on.
- **UNVERIFIABLE** → keep the change ONLY if your own source is primary; flag it either way.

> **Fail-safe, never fail-stop (added 2026-08-03).** One unresolvable claim must never sink the
> run. Drop that single change, ship the rest of the patch, and say plainly in the briefing what
> was dropped and why. An unattended run that halts over one bad claim costs a whole week of
> updates; one that ships eight good changes and flags the ninth costs nothing. The only
> conditions that legitimately abort a run are Contract 1 exit 1/2 (diverged or broken clone) and
> a Contract 4 hard FAILURE — everything else degrades gracefully.

---

## CONTRACT 3.6 — DECISION QUEUE (never block on judgment calls)

Some things are genuinely not yours to decide alone: a value this skill hard-codes turning out to
be wrong, a sheet row whose note contradicts its own cell, a scope change. Before 2026-08-03 these
either blocked the run waiting for the user or got silently resolved. Both are wrong.

**Append to `decisions.json` and keep going.** Schema:

```json
{"id":"<YYYY-MM-DD-slug>","date":"<YYYY-MM-DD>","status":"open",
 "area":"<tab or field>","question":"<what must be decided>",
 "why_not_autonomous":"<why you did not just pick>",
 "options":["<a>","<b>"],"resolution":null,"source":"<url or null>"}
```

Rules:

- **Nothing in `decisions.json` gates the pipeline.** It is a queue, not a lock.
- Surface open items in the briefing under Verification, one line each. Do not re-litigate an
  item that is already `open` — one entry per question, ever.
- When the user resolves one, set `status` to `resolved` and fill `resolution`.
- If a decision turns out to have been a *published error*, it also gets a `corrections.json`
  entry when it is fixed. The two files are different jobs: `decisions.json` is "someone must
  choose", `corrections.json` is "we published something wrong and here is the fix."
- Default to the conservative branch while an item is open — the one that changes least and is
  easiest to reverse.

**Corrections log duty:** if this week's work FIXES a substantive error that was previously
published on the dashboard (wrong incumbent, wrong matchup, wrong rating, wrong count),
append an entry to `corrections.json` (date, area, wrong, right, caught_by, impact, source).
Rendered publicly on methodology.html — no silent corrections, ever.

### 3.5.3 Verification section (mandatory in the briefing)

Add to the briefing, after Sheet Updates:

```markdown
## Verification
- ✅ N claims confirmed by independent fact-check (3 subagents)
- ⚠️ [claim] — CONTRADICTED: [what the verifier found] → [action taken]
- ⚠️ [claim] — UNVERIFIABLE: kept on primary source [link] / dropped
```

Add one line per **open** `decisions.json` item as well:

```markdown
- 🗳️ Awaiting your call — [question]. Ran with [conservative branch] meanwhile. (decisions.json: <id>)
```

An all-✅ section with zero ⚠️ items and zero dropped changes is the normal, expected result.
If you skipped verification (e.g., zero changes this week), say so in this section explicitly.

> **A zero-change week is a legitimate, complete run.** Forecasters go quiet for weeks at a time,
> and Cook and Inside Elections both published nothing between 2026-07-27 and 2026-08-03. If
> nothing moved, write the briefing saying nothing moved, ship the unchanged chamber values with a
> fresh `LAST_UPDATED`, and stop. Never manufacture a rating change, stretch a stale one into
> "news", or pad the patch to make a run look productive. The dashboard's value is that it is
> right, not that it changes.

---

## CONTRACT 3.9 — STATE NEWS REFRESH (mandatory, every run)

Added 2026-07-16 (previously the optional Step 5 of WEEKLY_ROUTINE.md — it kept getting skipped,
leaving `news_analysis.json` stale and the State News tab flagged by L2-freshness).

> ⚠️ **Rewritten 2026-08-03 — FAN OUT, do not do this serially.** The 2026-08-03 run scored
> 10 of 27 races working alone and had to report a partial refresh. That was not a discipline
> failure: 27 races of searching, deep-link verification and scoring does not fit one agent's
> context, which is why this step "kept getting skipped" before it was made mandatory. Making it
> mandatory did not make it possible. **Parallelism does.**
>
> **Spawn 5–6 news subagents (Agent tool, general-purpose), each owning 4–5 races**, and run them
> in parallel in a single message. Each returns structured JSON for its races only; you merge,
> validate and write. Unlike the Contract 3.5 verifiers there is **no cap and no anchoring
> concern** here — this is gather-and-score, not adjudication, so fan-out is safe and is the
> whole point. Give each subagent: its race list, the exact `news_analysis.json` race schema,
> the `outlet_lean` map, the deep-link rule, and the instruction below about dates.
>
> **The date rule is non-negotiable and must be repeated to every subagent:** an article's `date`
> must come from the URL slug, an explicit dateline, or the page itself — **never inferred,
> never approximated.** If the date cannot be established, drop the article and find another. A
> plausible-looking invented date turns L2b from a real coverage metric into decoration, and is
> worse than a visible gap. Prefer sources that carry the date in the URL.

1. For every race in `news_config.json` (`states` → `races`), search its `query` for
   coverage from the last ~14 days (the config's `lookback_days` is the outer bound).
2. Rescore each race into `news_analysis.json` using the existing schema and semantics
   (`sentiment` = 0-100 D-favorability of coverage tone; `candidates[].sentiment` = personal
   coverage favorability; outlet `lean` from the config's `outlet_lean` map, null if unrated).
   Update `generated` to today. Leave baseline/non-config states untouched.
3. **Deep links only** — every article URL must point to the specific article
   (L10-links fails the run otherwise). Skip junk aggregators; prefer outlets in the lean map
   or credible state outlets.
4. Resync the `DEMO_NEWS` article blocks in `index.html` for the states/races present there,
   so the On Deck cards and flip panels cite the same fresh articles (regex-replace each
   `articles:[...]` block; verify the babel script still parses afterwards).
5. If a primary resolved since last run (AZ Jul 21, MI/KS Aug 4, WI/MN Aug 11, AK Aug 18,
   NH Sep 8), update the affected candidate lists and queries in `news_config.json` and flag
   the change in the briefing.

6. **Merge, then check your own coverage before moving on.** Run
   `python3 verify_dashboard.py --local` and read the `L2b-coverage` line. If it is below 27/27,
   you have subagent capacity left — spawn another round for the stale races rather than
   accepting the gap. Only report a partial refresh when a race genuinely has no datable recent
   coverage, and then name it.

> **Why L2b can under-report real work.** L2b requires an article dated within 10 days of
> `generated`. A race can be genuinely rescored and still count stale because the best available
> coverage is three weeks old — NC/Senate on 2026-08-03 was exactly this. That is not a bug: it
> is the metric correctly saying "this race has no fresh coverage." Say so in those words rather
> than implying you skipped it.

7. **Refresh `ie_watch.json` (IE Tilt Watch, route 3 — see 2.3a).** While the four forecasters'
   current ratings are in hand, reconcile the watch log against them:
   - For every **open** entry, check whether Cook or Sabato have moved to match IE → set `status`
     to `confirmed` and fill `confirmed_by`; or whether IE has reverted to the sheet's rating →
     set `status` to `faded`. **Never** move the sheet's Rating cell from an IE change.
   - Add an entry for any race where IE now diverges from the sheet cell (a Tilt, or any tier
     disagreement): `ie_moved`, `first_logged` = today, `sheet_rating`, `ie_rating`, an
     informational `nearest_7pt`, a deep-linked `source`, and a one-line `divergence`.
   - Bump `generated` to today and surface every open entry in the briefing's IE Tilt Watch
     section (Contract 3). `verify_dashboard.py` L12-iewatch checks schema and freshness.

Then Contract 4's steps 3-4 (sentiment snapshot + verifier) confirm the refresh landed.

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

3. **Append the sentiment snapshot.** After the Contract 3.9 news refresh, run
   `python3 append_sentiment_history.py` — it records this week's scores into
   `sentiment_history.json` (idempotent; re-running replaces the same date). Skipping this
   step leaves a permanent hole in the trend data.

4. **Run the deterministic verifier.** `python3 verify_dashboard.py --local` — checks
   news_analysis.json schema/freshness, config consistency, rating enums in the dashboard
   fallbacks, State News wiring, pending-patch validity, and history ordering. Fix any ❌
   before finishing. (The Actions job re-runs this plus live-Sheet checks post-apply.)

5. **Assert patch-file integrity.**
   ```bash
   cd ~/Documents/Claude/Projects/"Electoral Dashboard" && python3 check_patch_integrity.py
   ```
   Neither `validate_patch.py` nor `verify_dashboard.py --local` catches a *missing* pending
   patch — L7 treats "nothing to validate" as a pass, which is exactly how the 2026-07-29 rename
   trap went unnoticed while the verifier reported 10/10 green. This script checks that a pending
   patch exists and that no archive's `LAST_UPDATED` is *later* than its own filename date, and
   prints recovery commands on failure. See its docstring for the full incident write-up.

6. **Check the refresh coverage warning.** `verify_dashboard.py --local` now emits
   `L2b-coverage: N/M configured races refreshed`. L2-freshness only reads the `generated` date
   stamp, so it passes whether you rescored 27 races or zero; L2b measures the actual work by
   requiring each configured race to carry an article dated within 10 days of `generated`
   (tune with `--refresh-window`). If it warns, **name the exact count and the stale races in the
   briefing's Contract 3.9 scope note** — do not describe a partial refresh as a full one.

7. **Reconcile the briefing against the patch (L11, added 2026-08-03).**
   `verify_dashboard.py --local` now emits `L11-briefing`, which parses the chamber figures out
   of the newest briefing's **Chamber Balance** section and asserts they equal
   `constants_patch.json`. A contradiction is a **hard FAIL and blocks the push**; a briefing whose
   format it cannot parse is a **WARN**, because failure to extract is not evidence of an error.

   > **Why this exists.** On 2026-08-03 `SENATE_I` was corrected 3 → 2 in the patch, `history.json`
   > and this skill, while the briefing — the document humans actually read — still said "3I" in
   > two places. Nothing in the pipeline noticed; it was caught only because the user asked for the
   > briefing to be updated. On an unattended run that backstop does not exist.
   >
   > **If L11 fails, fix the briefing — do not "fix" the patch to match.** The patch is validated
   > against the Sheet and the invariants; the prose is the thing that drifts.
   >
   > Two parser rules worth knowing so you do not trip it: it reads **only the Chamber Balance
   > section**, and it takes the **first** figure per field. Elaboration after the headline line is
   > ignored deliberately — the 2026-07-29 briefing legitimately contains both "53 R / 47 D / 3 I"
   > and, one sentence later, "the registration split is 53 R / 45 D / 2 I", and only the first is
   > a claim about what the dashboard publishes. Keep the authoritative figures in the headline
   > "Confirmed: …" line and you will never fight this check.

8. **Check the IE Tilt Watch (L12-iewatch, added 2026-08-12).** `verify_dashboard.py --local`
   emits `L12-iewatch`: it parses `ie_watch.json`, asserts the schema (each entry carries a
   `race`, `sheet_rating`/`ie_rating`, a `status` of open/confirmed/faded, and a deep-linked
   `source`), and warns if `generated` is stale relative to the newest briefing. A malformed file
   is a **FAIL**; a stale `generated` is a **WARN**. This is the machine backstop for the route-3
   rule (2.3a); it does NOT re-check that IE stayed out of the Rating cell, so keep that
   discipline yourself.

Only after all eight checks pass do you tell the user the weekly cycle is done.

---

## CONTRACT 5 — SHIP IT (you run this; the user does not)

**Superseded rule.** The 2026-07-06 instruction "never run git yourself, end every run with a
paste-ready git block" is **retired as of 2026-07-29** at the user's explicit request ("I want you
to take it completely off my keyboard"). You now commit and push yourself, via one script:

```bash
cd ~/Documents/Claude/Projects/"Electoral Dashboard" && ./weekly_commit.sh "Weekly YYYY-MM-DD: <one-line summary of changes>"
```

**Do not hand-write git commands, and do not ask the user to run anything.** The script is the only
sanctioned path: it runs every Contract 4 gate, stages an explicit allowlist, pulls with **rename
detection disabled** so the archive rename can only surface as a visible conflict, re-checks
integrity after the merge, and **aborts before pushing** if the merge damaged anything. On any
post-commit failure it rewinds the repo to a clean state with the local commit intact and unpushed,
so an unattended run can never leave a half-merged repo behind.

Then report the outcome in your summary: the pushed commit SHA on success, or — if the script
exited nonzero — quote its error verbatim, state plainly that **nothing reached origin**, and say
what the user needs to decide. Never describe a run as complete when the push did not land.

`--dry-run` runs all gates and changes nothing; use it if you want to verify before shipping.

> The hazards below are why hand-written blocks are banned rather than merely discouraged — they
> are permanent properties of this environment, not one-off slips. They still apply if the user
> ever explicitly asks you for raw git commands:

- **zsh has `INTERACTIVE_COMMENTS` off**, so `#` and everything after it parses as arguments.
- **An apostrophe anywhere** (even in prose like "the bot's archive") opens a `quote>` continuation
  and swallows the rest of the block.
- **`verification_report.json` is gitignored** and `git add` errors on it.
- **`git add -A` is never safe here** — `weekly-apply.yml`, `publish_to_ghost.py` and
  `WEBSITE_PLAN.md` are intentionally uncommitted pending Ghost secrets, and committing the
  workflow without the script would break the Monday job.

### How the push works (and the two dead ends)

`weekly_commit.sh` reads `.gh_token` — a fine-grained PAT scoped to this repo with
`contents:write`, gitignored — and injects it into the remote URL for that single push. It is never
written to `.git/config`, never echoed, and redacted from any git output. The script refuses to run
if `.gh_token` ever becomes tracked. If the file is absent it falls back to the system credential
helper, so running on the Mac still works.

Two approaches were tried and abandoned on 2026-07-29; do not revive them:

- **Pushing from the sandbox with the system helper** — there are no credentials there:
  `fatal: could not read Username for 'https://github.com'`.
- **A macOS LaunchAgent running the script natively** — macOS TCC blocks background launchd jobs
  from `~/Documents`, where this repo lives: `bash: ./weekly_commit.sh: Operation not permitted`.
  The only workarounds were granting Full Disk Access to `/bin/bash` (far too broad) or moving the
  repo out of `~/Documents` (breaks the Cowork mount).

**If the token expires,** the push fails cleanly with nothing sent to origin. Say so plainly in the
summary and tell the user to mint a new fine-grained PAT (this repo only, contents:write) and
overwrite `.gh_token`. Never work around it by asking them to paste git commands.

### Git commands you may run

`git pull` (Contract 1 Step 0), `./weekly_commit.sh` (Contract 5), and any read-only inspection
(`status`, `log`, `show`, `diff`, `stash list`). Everything else — bare `add`/`commit`/`push`,
`reset --hard`, `stash pop`, force-pushes, branch surgery — stays off-limits: put it in front of
the user with an explanation instead. Always `find .git -maxdepth 1 -name "*.lock" -delete` first;
stale `index.lock` and `HEAD.lock` recur in this repo.

---

## Environment notes

- Google Drive MCP is **read-only**. Cell writes go through `constants_patch.json` only.
- The apply layer is `apply_constants_patch.py` (handles `updates` via `update_constants()` and
  `row_updates` via `update_ratings_in_tab()` in `update_sheet.py`). It re-validates invariants
  and **only archives the patch on a fully successful apply** — a skipped/failed change leaves
  the file in place and exits nonzero, so the pending patch survives for a retry.
- A prior applied patch is archived as `constants_patch.applied_YYYY-MM-DD.json` — presence of
  last Monday's archive is your Contract-1 signal that the apply job ran.
