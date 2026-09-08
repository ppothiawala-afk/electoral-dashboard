# Electoral Dashboard — Weekly Briefing
**Week of September 1–8, 2026**

---

## ⚠️ Pipeline Note — reconciled (Contract 1, Check B)

Last Monday's apply job **did run**: `constants_patch.json` was archived as `constants_patch.applied_2026-09-07.json` and the Sheet shows Constants `LAST_UPDATED = 2026-09-07` with TX-Sen and IA-Sen live at **Lean R** ([Sheet Constants + Senate tabs, read this run](https://docs.google.com/spreadsheets/d/1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA)). So the patch is applied and it was safe to write this week's patch.

The gap: that 09-07 patch was an **out-of-band reviewer resolution** (P-funk resolved `decisions.json 2026-08-25-tx-ia-sen-consensus` on 09-03, reverting TX/IA-Sen Toss-up → Lean R per the §2.3b consensus rule), and it was applied **without a standalone briefing or `history.json` entry** — so the last history entry was 08-31 while the newest applied patch was 09-07. I have **backfilled a 2026-09-07 `history.json` entry** recording the two Senate reverts, keeping the timeline complete. No data was lost and no pending patch was overwritten.

---

## Chamber Balance

Confirmed: **218 R | 214 D | 1 I | 2 V House / 53 R | 47 D | 2 I Senate** ([House Clerk vacancies](https://clerk.house.gov/Members/ViewVacancies), [Ballotpedia balance-of-power snapshot, Sep 2](https://news.ballotpedia.org/2026/09/02/everton-blair-jr-takes-office-ending-the-vacancy-in-georgias-13th-congressional-district/)).

**Change this week: two vacant Democratic seats were filled**, moving the House from 218 R / 212 D / 1 I / 4 V to **218 R / 214 D / 1 I / 2 V**:

- **GA-13** — Everton Blair Jr. (D) was sworn in **Sep 1, 2026**, ending the vacancy left by the late Rep. David Scott (D); he won the Aug 25 runoff 53.2–46.8 over Marcye Scott ([Ballotpedia, Sep 2](https://news.ballotpedia.org/2026/09/02/everton-blair-jr-takes-office-ending-the-vacancy-in-georgias-13th-congressional-district/); [AJC, Sep 1](https://www.ajc.com/politics/2026/09/everton-blair-georgias-first-openly-gay-congressman-sworn-into-office/)).
- **CA-14** — Aisha Wahab (D) was sworn in **Sep 2, 2026**, ending the vacancy left by Eric Swalwell's (D) resignation; she won the Aug 18 runoff over Melissa Hernandez ([Ballotpedia, Sep 4](https://news.ballotpedia.org/2026/09/04/aisha-wahab-takes-office-ending-the-vacancy-in-californias-14th-congressional-district/)).

Current **2 House vacancies** — both are held-for-November seats with no special called, filled at the Nov 3 general:

- **FL-20** (Cherfilus-McCormick-D resigned Apr 21) — a heavily Democratic Broward/Palm Beach seat ([Ballotpedia, Apr 22](https://news.ballotpedia.org/2026/04/22/sheila-cherfilus-mccormicks-resignation-leaves-floridas-20th-congressional-district-vacant/)).
- **TX-23** (Gonzales-R resigned Apr 14) — no special called by Gov. Abbott.

⚠️ **Data fix applied this week:** the House tab carried the vacant **FL-20** row as **Party R / Solid R**. FL-20 is a majority-Black, safe-Democratic seat; the label was a published error and is corrected to **D / Solid D** (see Sheet Updates and `corrections.json`). It does not affect the R/D counts (a vacant seat is counted in `HOUSE_VACANCIES`).

Senate: **53 R / 47 D / 2 I** — no change. The two independents (**Sanders-VT, King-ME**) caucus D and are counted inside the 47; **Murkowski-AK is a Republican**, counted in the 53 ([senate.gov party division](https://www.senate.gov/history/partydiv.htm)).

---

## Notable Rating Shifts (Past Week)

**No consensus (Cook + Sabato) Rating-cell moves this week** — an independently-verified result, not a skipped step (see Verification). The forecaster activity that did occur was either governor-only, a lone mover, or already reflected on the sheet:

### Senate
- No new Cook or Sabato Senate cell changes in the Sep 1–8 window. Sabato's AK/OH-Sen Toss-up and NC-Sen Lean D ratings (which the sheet already carries) date to **June**, not this week — a search summary that dated them to "Sep 2" was **contradicted** by the verifier and is not treated as a fresh move.

### House
- No new Cook or Sabato House cell changes in the window. Sabato's TX-15 → Toss-up move was July 30 / Aug 26, already on the sheet.

### Governors
- **Alaska** — ([Sabato's Crystal Ball, Sep 3](https://centerforpolitics.org/crystalball/the-governors-a-trio-of-rating-changes-toward-democrats-as-they-chase-a-rare-edge-in-overall-seats-held/)) moved AK-Gov **Likely R → Toss-up**. This is a **lone mover**: Cook still rates AK-Gov **Likely R** ([Cook Political Report, AK Governor](https://www.cookpolitical.com/governor/race/479451)). Under §2.3b the cell **holds at Likely R** pending a second forecaster; noted here, not written. ✅ cell correct.
- Sabato's same Sep 3 batch moved IA-Gov → Lean D and PA-Gov → Safe D; **both already match the sheet** (Lean D / Solid D). No action.

---

## IE Tilt Watch

Inside Elections divergences from the sheet — leading indicators only; per §2.3a these do **not** move the Rating cell. Four new divergences logged from IE's Sep 2–3 update ([IE Senate ratings via 270toWin](https://www.270towin.com/2026-senate-election/inside-elections-2026-senate-ratings), [IE House ratings via 270toWin](https://www.270towin.com/2026-house-election/inside-elections-2026-house-ratings)):

- **AK-Sen** — IE **Tilt R** (Sep 3) vs. sheet **Toss-up**. IE one tier toward R; watch whether Cook/Sabato drift to Lean R or hold Toss-up. ⏳ open
- **NH-Sen** — IE **Toss-up** (Sep 2) vs. sheet **Lean D**. IE one tier more competitive (toward Sununu); watch for Cook/Sabato to follow. ⏳ open
- **FL-14** — IE **Tilt R** (Sep 3) vs. sheet **Toss-up**. Castor-D seat drawn more R; Cook+Sabato consensus already at Toss-up. ⏳ open
- **TX-15** — IE **Tilt R** (Sep 3) vs. sheet **Lean R**. De La Cruz-R; watch for Cook/Sabato toward Toss-up. ⏳ open

Still open from prior weeks: **NC-Sen** (IE Tilt D vs Lean D), **GA-Sen** (IE Tilt D vs Lean D), **KS-Gov** (IE Tilt R vs Lean R). Confirmed earlier: IA-Sen, IA-Gov. (IE's Sep 3 OH-Sen, KS-Sen and MN-01 moves **converged onto** the sheet's ratings — no divergence logged.)

---

## Electoral Environment

The competitive map continues to tilt modestly toward Democrats. Democratic incumbents/nominees lead comfortably in the marquee open-seat contests — Roy Cooper is up double digits in NC-Sen ([Elon Poll, Aug 12](https://www.elon.edu/u/news/2026/08/12/elon-poll-cooper-continues-to-lead-in-north-carolina-u-s-senate-race/)) and Katie Hobbs leads AZ-Gov by ~15 ([KJZZ, Aug 24](https://www.kjzz.org/politics/2026-08-24/poll-hobbs-leading-biggs-by-15-points-in-arizona-governors-race)) — while several red-state races are unexpectedly close: Texas Senate is a genuine toss-up with Talarico edging Paxton ([Houston Public Media, Aug 25](https://www.houstonpublicmedia.org/articles/news/politics/election-2026/2026/08/25/560302/james-talarico-continues-to-edge-out-ken-paxton-in-texas-u-s-senate-race-new-poll-finds/)) and Nebraska's Ricketts–Osborn race is tied on some internals ([Newsweek, Aug 26](https://www.newsweek.com/republicans-chances-of-losing-to-dan-osborn-in-nebraska-senate-race-12370545)). Mary Peltola holds a narrow, consistent edge in ranked-choice Alaska, prompting a planned Trump campaign trip for Sullivan ([Washington Examiner, Sep 2](https://www.washingtonexaminer.com/news/campaigns/congressional/4710205/trump-alaska-trip-preview-dan-sullivan/)). The New Hampshire primary is **today (Sep 8)**; Chris Pappas (D) and John E. Sununu (R) are the heavy Senate favorites, with results pending ([Washington Post, Sep 7](https://www.washingtonpost.com/politics/2026/09/07/new-hampshire-primary-senate-pappas-manzur-sununu-brown-governor-house-nh01/94bd1446-aab5-11f1-b498-8697f35a6743_story.html)).

---

## Candidate News

- **Florida Senate** — coverage is dominated by the "Hope Florida" scandal: a leaked Leon County grand-jury report found the state misappropriated $10M of a Medicaid settlement and faulted appointed Sen. Ashley Moody's (R) office, and Democratic nominee Angie Nixon is demanding her resignation ([Florida Phoenix, Aug 27](https://floridaphoenix.com/2026/08/27/democrats-fired-up-republicans-on-the-defense-after-hope-florida-grand-jury-report-leaked-to-the-press/)).
- **Ohio Governor** — an armed man charged at Democrat Amy Acton at a county fair (Sep 6–7), days after she declined to debate Vivek Ramaswamy ([Signal Ohio, Sep 7](https://signalohio.org/armed-man-charged-toward-democratic-candidate-ohio-governor-amy-acton/)).
- **Iowa** — ticket-splitting on display: Republican Ashley Hinson leads the Senate race 50–45 while Democrat Rob Sand leads the concurrent governor's race, per the same Emerson poll ([Emerson College, Sep 3](https://emersoncollegepolling.com/iowa-2026-poll-hinson-leads-turek/)).
- **Texas** — Ken Paxton's campaign drew mockery for a data-center plan carrying a "made with AI" disclaimer as Trump's MAGA Inc. disclosed a $10M independent expenditure to shore him up ([Newsweek, Aug 24](https://www.newsweek.com/james-talarico-ken-paxton-texas-ai-data-center-plan-12360637)).

---

## Sheet Updates

Every change applied via `constants_patch.json` this week:

| Tab | Race / Field | Old | New | Source |
|---|---|---|---|---|
| Constants | HOUSE_D | 212 | 214 | CA-14 + GA-13 sworn in ([Ballotpedia](https://news.ballotpedia.org/2026/09/02/everton-blair-jr-takes-office-ending-the-vacancy-in-georgias-13th-congressional-district/)) |
| Constants | HOUSE_VACANCIES | 4 | 2 | Same |
| Constants | LAST_UPDATED | 2026-09-07 | 2026-09-08 | This run |
| House | CA-14 Incumbent | VACANT | Aisha Wahab (D) | Sworn Sep 2 ([Ballotpedia](https://news.ballotpedia.org/2026/09/04/aisha-wahab-takes-office-ending-the-vacancy-in-californias-14th-congressional-district/)) |
| House | GA-13 Incumbent | VACANT | Everton Blair Jr. (D) | Sworn Sep 1 ([Ballotpedia](https://news.ballotpedia.org/2026/09/02/everton-blair-jr-takes-office-ending-the-vacancy-in-georgias-13th-congressional-district/)) |
| House | FL-20 Party / Rating | R / Solid R | D / Solid D | Data fix — safe-D vacant seat ([Ballotpedia](https://news.ballotpedia.org/2026/04/22/sheila-cherfilus-mccormicks-resignation-leaves-floridas-20th-congressional-district-vacant/)) |

### No action needed
- **AK-Gov** — Sabato lone move to Toss-up; held at Likely R per §2.3b (Cook still Likely R). Logged, not written.
- **IE Tilt Watch** (AK-Sen, NH-Sen, FL-14, TX-15) — logged to `ie_watch.json`, never written to the Rating cell.
- Remaining vacancies **FL-20, TX-23** — filled at the Nov 3 general; no special called.

---

## Verification

- ✅ **7 rating/forecaster claims** and **7 membership/balance claims** and **4 matchup/calendar claims** confirmed by three independent fact-check subagents (claims-only, fresh context).
- ⚠️ **"Sabato moved NC-Sen → Lean D on Sep 2"** — **CONTRADICTED**: the verifier found that move dates to **mid-June 2026**, and there was no September Sabato Senate move. → No patch impact (the sheet already carries NC-Sen Lean D; no NC change was written). The briefing avoids citing any September Sabato Senate move.
- ✅ **Chamber math independently confirmed**: House 218 R / 214 D / 1 I / 2 V after both swearings-in; only FL-20 and TX-23 remain vacant; Senate 53 R / 47 D with Sanders/King inside the 47 and Murkowski R.
- ✅ **FL-20 correction confirmed**: verifier independently found FL-20 is a heavily-Democratic seat, making the prior "R / Solid R" label an error (logged in `corrections.json`).
- ✅ **No dropped changes.** Every change in the patch is backed by a primary or independently-corroborated source.
- **State News:** L2b coverage **27/27 configured races** refreshed with articles dated within 10 days (two rounds of news subagents; the second round recovered NV-Gov, AZ-Gov, LA-Sen, FL-Sen, KS-Gov, MT-Sen, AK-Sen).
- **Decision queue:** no open `decisions.json` items — the last open one (`2026-08-25-tx-ia-sen-consensus`) was resolved by P-funk on 09-03 and its patch applied 09-07. No new judgment calls this week.
