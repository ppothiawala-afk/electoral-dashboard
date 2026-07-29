# Electoral Dashboard — Weekly Briefing
**Week of July 27–August 2, 2026** *(off-cycle run: research executed Wednesday, July 29, for the Monday, August 3 apply window)*

---

## ⚠️ PIPELINE ALERT — local clone is behind origin (Actions itself is healthy)

**Contract 1 Check A failed on the file signal, but the Sheet says the patch landed.** Reporting both, because the two disagree and the distinction matters.

**What's wrong:** `constants_patch.json` dated 2026-07-20 was still sitting in the project folder, and no `constants_patch.applied_2026-07-20.json` archive existed locally. Under the Contract 1 tripwire that reads as "the Monday apply job never ran."

**What actually happened:** it did run. Three independent signals confirm the July 20 patch was applied to the Sheet:

1. The Sheet's Drive `modifiedTime` is **2026-07-20T21:05Z**, after the 20:00 UTC cron.
2. Constants `LAST_UPDATED` on the Sheet reads **2026-07-20**.
3. Every July 20 row change is present on the Sheet — CA-45 and NY-19 at Likely D, KY-06 Likely R, NH-02 and OR-05 Solid D, TX-15 Lean R, CA-22 Lean D, and the ME/SC/LA Senate notes.

So the pending patch was a **stale local copy of already-applied work**, not unapplied changes. Nothing was destroyed by overwriting it, and I proceeded with a new patch on that basis. This is a deliberate deviation from the letter of Contract 1 ("archive present, no leftover"), justified because the Sheet is the authoritative record and the archive file is only a proxy for it.

**Root cause:** the Actions job's commit-back (`chore(weekly-apply)`) was pushed to `origin/main`, but the local clone was never pulled. Local `HEAD` and the local `origin/main` ref both still sit at `6ac2708` (the July 20 research commit) because nothing has fetched since.

**July 27 run: resolved, and clean.** The Actions history shows `Weekly Sheet Apply #13` succeeded on July 27 at 2:04 PM PDT in 27 seconds, with no `pages build and deployment` afterwards — i.e. the job ran, found nothing to change (patch already archived July 20, scrape produced no diffs), and correctly committed nothing. That also explains why the Sheet's `modifiedTime` has not moved since July 20. The pipeline is healthy; the only defect is the unpulled local clone.

**Still needs action: the push will be rejected as-is.** Origin is ahead of you. The git block at the end of this briefing stashes, pulls, and pops to handle it.

**Timing note for future runs.** The cron is `0 20 * * 1` (20:00 UTC = 1:00 PM PDT), but both recent runs actually started at ~2:04–2:05 PM PDT — a consistent ~64-minute queue delay, which is normal GitHub behaviour for scheduled workflows under load rather than a misconfiguration. It does not change the deadline: the patch must be **committed** before 1 PM PT, since the job checks out whatever is on `main` when it finally starts.

---

## Chamber Balance

No changes this week. Confirmed: **218 R | 212 D | 1 I | 4 V** House ([House Clerk vacancy list](https://clerk.house.gov/Members/ViewVacancies), [House Press Gallery party breakdown](https://pressgallery.house.gov/member-data/party-breakdown)) and **53 R | 47 D** Senate, with Sanders-VT, King-ME and Murkowski-AK counted inside the caucus totals.

Current 4 House vacancies:

- **GA-13** (David Scott, D — died Apr 22) — **still vacant.** The July 28 all-party special produced no majority: Marcye Scott 46.8%, Everton Blair Jr. 36.7%, sending two Democrats to an **August 25 runoff** ([Atlanta Journal-Constitution, July 28](https://www.ajc.com/politics/2026/07/blair-scott-advance-to-runoff-in-13th-congressional-district-special-election/)). A seat stays vacant until a successor is sworn in, so the count is unchanged.
- **CA-14** (Eric Swalwell, D — resigned Apr 14) — special **runoff** August 18, Aisha Wahab vs. Melissa Hernandez, both D ([Office of the Governor, April 14 proclamation](https://www.gov.ca.gov/2026/04/14/governor-newsom-issues-proclamation-setting-special-election-for-california-congressional-district-14/)). Note the terminology fix: under the proclamation, August 18 is formally the *special runoff*, not the special general.
- **FL-20** (Sheila Cherfilus-McCormick, D — resigned Apr 21) — no special date set; expected to resolve on the November 3 ballot ([House Clerk](https://clerk.house.gov/Members/ViewVacancies)).
- **TX-23** (Tony Gonzales, R — resigned Apr 14) — **still not called.** Abbott's office says he "will announce a special election later on," with no date after more than three months of vacancy ([Axios San Antonio, July 27](https://www.axios.com/local/san-antonio/2026/07/27/special-election-tony-gonzales-texas-23-congress)).

**Senate:** 53 R / 47 D / 3 I, unchanged. One counting note worth logging: the *registration* split is 53 R / 45 D / 2 I (Sanders and King), because Murkowski is a registered Republican. The dashboard's `SENATE_I = 3` follows the project's own convention of treating Murkowski as a de facto independent, and `SENATE_R + SENATE_D = 100` still holds. Flagging it as a definitional quirk, not proposing a change.

---

## Notable Rating Shifts (Past Week)

### Governors

- **Florida** — ([Sabato's Crystal Ball, July 23](https://centerforpolitics.org/crystalball/three-gubernatorial-rating-changes-michigan-to-leans-democratic-new-mexico-to-safe-democratic-florida-to-likely-republican/)) moved **Safe R → Likely R**, citing a University of North Florida poll with Byron Donalds (R) up only five over David Jolly (D). Sheet showed Solid R. **⚠ stale → being corrected to Likely R this week.**
- **Michigan** — ([Sabato's Crystal Ball, July 23](https://centerforpolitics.org/crystalball/three-gubernatorial-rating-changes-michigan-to-leans-democratic-new-mexico-to-safe-democratic-florida-to-likely-republican/)) moved **Toss-up → Leans D**. Sheet already showed Lean D. **✅ no change needed** — Sabato caught up to where the dashboard sat.
- **New Mexico** — ([Sabato's Crystal Ball, July 23](https://centerforpolitics.org/crystalball/three-gubernatorial-rating-changes-michigan-to-leans-democratic-new-mexico-to-safe-democratic-florida-to-likely-republican/)) moved **Likely D → Safe D** on Haaland's roughly seven-to-one cash advantage. Sheet already showed Solid D. **✅ no change needed.**

### Senate

No forecaster moves this week. Cook's last Senate change remains Alaska Lean R → Toss-up on July 1; Sabato's last was June 11; Inside Elections' Senate page was last updated July 12 with no logged change ([Inside Elections Senate ratings](http://insideelections.com/ratings/senate/)).

### House

No forecaster moves this week. Cook's most recent House batch is still July 16 — six districts, all toward Democrats ([Cook Political Report, July 16](https://www.cookpolitical.com/analysis/house/house-overview/our-initial-range-potential-house-outcomes-shows-dems-favored-gop)) — all seven of last week's House changes (six Cook plus CA-22 from Sabato) are confirmed live on the Sheet.

### Not a rating change, but new to the landscape

Fox News launched an initial 2026 Power Rankings set in the window — Senate July 21, House July 22, Governor July 23 ([Fox News Power Rankings, July 21](https://www.foxnews.com/politics/fox-news-power-rankings-voters-say-theyre-economic-pain-democrats-gain)). These are inaugural ratings, not moves, and the dashboard tracks four forecasters, so no action. Worth a decision at some point on whether to add them.

---

## Electoral Environment

The generic ballot remains the clearest structural signal and it has not moved much: the July average sits around **D+6**, with Democrats at 47.8% to Republicans' 41.6% ([USPollingData, July 2026](https://uspollingdata.com/news/generic-ballot-july-2026/)), though the spread across individual polls is unusually wide — Emerson had D+11 ([Emerson College Polling, July 2026](https://emersoncollegepolling.com/july-2026-national-poll-democrats-with-11-point-generic-ballot-advantage/)) while Morning Consult had D+3 in the same month. Cook's own framing is that Republicans are favored in 212 seats and would need to split the 18 Toss-ups to reach a four-seat majority ([Cook Political Report, July 16](https://www.cookpolitical.com/analysis/house/house-overview/our-initial-range-potential-house-outcomes-shows-dems-favored-gop)).

The Q2 fundraising picture that emerged this month is lopsided in Democrats' favor in the marquee races: Ossoff raised $20M in the quarter against Mike Collins' $2.1M, roughly a 20-to-1 cash-on-hand gap ([Roll Call, July 23](https://rollcall.com/2026/07/23/at-the-races-seeing-blue-in-georgia/)); Talarico raised $30M to Paxton's $9M ([Texas Tribune, July 20](https://www.texastribune.org/2026/07/20/texas-senate-talarico-paxton-fundraising-spending-money-donors/)); and Peltola more than tripled Sullivan's Q2 haul in Alaska ([Anchorage Daily News, July 20](https://www.adn.com/politics/2026/07/20/peltola-raises-millions-more-than-sullivan-in-alaskas-us-senate-race/)). Money is not votes, but the consistency across four different states is the notable part.

The counterweight is candidate-quality risk on the Democratic side in two states with primaries inside three weeks — Michigan's Senate primary and Wisconsin's gubernatorial primary are both producing polling that suggests the front-runner may not be the strongest general-election nominee.

---

## Candidate News

- **Maine Senate** — Democrats formally nominated **Troy Jackson** on July 25, 566 of 571 delegates, closing out the Platner withdrawal ([NPR, July 25](https://www.npr.org/2026/07/25/nx-s1-5902982/democrats-maine-senate-race)). A UNH poll fielded July 15–20 has Jackson 49, Collins 46 ([Portland Press Herald, July 21](https://www.pressherald.com/2026/07/21/troy-jackson-has-slight-edge-over-susan-collins-new-poll-finds/)). Maine Democrats also nominated Matt Dunlap for ME-02 at the same convention.
- **South Carolina Senate** — Filing closed July 28 with **nine certified candidates** after the state GOP decertified three of twelve who filed: Buckner, Fry, Graham (Nordone), Lynch, McBride, Norman, Parker, Sanford, Shepherd ([SC Daily Gazette, July 29](https://scdailygazette.com/2026/07/29/sc-gop-bars-3-candidates-from-primary-ballot-leaving-9-to-compete-for-us-senate/)). Appointed Sen. **Darline Graham Nordone is running**, with Trump's endorsement ([Axios, July 20](https://www.axios.com/2026/07/20/trump-backed-nordone-enters-senate-race)) — the dashboard said the opposite. Reps. Ralph Norman (SC-05) and Russell Fry (SC-07) are both in the field but remain seated; no House vacancy.
- **Arizona Governor** — **Andy Biggs** won the July 21 GOP primary roughly 70–17 over David Schweikert and faces Hobbs in November ([CNN, July 21](https://www.cnn.com/2026/07/21/politics/arizona-primaries-takeaways)).
- **Michigan Senate (Aug 4)** — Stevens vs. El-Sayed, with pro-Stevens outside spending past $50M including AIPAC-linked ads featuring Obama, who has not endorsed ([CNN, July 17](https://www.cnn.com/2026/07/17/politics/obama-michigan-senate-stevens-el-sayed-ads)). A late-July poll has Stevens beating Rogers 47–45 but Rogers beating El-Sayed 49–39 ([Roll Call, July 28](https://rollcall.com/2026/07/28/contentious-democratic-senate-contest-dominates-michigans-primary-season/)).
- **Wisconsin Governor (Aug 11)** — State Rep. **Francesca Hong** leads two July polls (Marquette: Hong 38, Barnes 16, Crowley 7, most undecided), while Marquette also finds Barnes is the strongest Democrat against Tiffany, up 44–40 ([Wisconsin Public Radio, July 22](https://www.wpr.org/news/marquette-poll-wisconsin-governor-july-22-2026)).
- **Minnesota Senate (Aug 11)** — Flanagan has widened her lead over Craig to 46–32 despite roughly $20M in pro-Craig outside spending ([MPR News, July 23](https://www.mprnews.org/episode/2026/07/23/peggy-flanagan-angie-craig-democratic-race-for-senate)).
- **Florida Senate special (Aug 18)** — Moody leads Nixon 50–42 and Vindman 50–40 in a UNF poll, with the less-funded Nixon outperforming ([Florida Phoenix, July 20](https://floridaphoenix.com/2026/07/20/moody-leads-nixon-by-8-points-vindman-by-10-in-new-poll-of-florida-senate-race-embargoed/)).
- **Texas Senate** — Talarico leads Paxton 45–40, his largest general-election lead to date ([Texas Tribune, July 28](https://www.texastribune.org/2026/07/28/texas-senate-poll-james-talarico-ken-paxton-july-2026/)).

---

## Sheet Updates

| Tab | Race | Old | New | Source |
|---|---|---|---|---|
| Governors | FL — Rating | Solid R | **Likely R** | [Sabato's Crystal Ball, Jul 23](https://centerforpolitics.org/crystalball/three-gubernatorial-rating-changes-michigan-to-leans-democratic-new-mexico-to-safe-democratic-florida-to-likely-republican/) |
| Governors | AZ — Notes | GOP primary Jul 21 pending | Biggs won ~70–17; Hobbs unopposed | [CNN, Jul 21](https://www.cnn.com/2026/07/21/politics/arizona-primaries-takeaways) |
| Governors | MI — Notes | (no Sabato line) | Sabato Toss-up → Leans D Jul 23; primary state of play | [Sabato's Crystal Ball, Jul 23](https://centerforpolitics.org/crystalball/three-gubernatorial-rating-changes-michigan-to-leans-democratic-new-mexico-to-safe-democratic-florida-to-likely-republican/) |
| Senate | SC — Notes | "Nordone (interim, **not running**)"; field = Norman, Lynch, Buckner | **Nordone IS running** (Trump-endorsed); 9 certified of 12 filed | [Axios, Jul 20](https://www.axios.com/2026/07/20/trump-backed-nordone-enters-senate-race); [SC Daily Gazette, Jul 29](https://scdailygazette.com/2026/07/29/sc-gop-bars-3-candidates-from-primary-ballot-leaving-9-to-compete-for-us-senate/) |
| Senate | FL — Challenger | "Alan Grayson (D)" | **Alex Vindman (D) vs. Angie Nixon (D)**, Aug 18 primary | [Florida Phoenix, Apr 22](https://floridaphoenix.com/2026/04/22/its-official-alex-vindman-is-running-for-the-u-s-senate-seat/) |
| Senate | ME — Challenger | "Troy Jackson (D, presumptive)" | **Troy Jackson (D)** — formally nominated | [NPR, Jul 25](https://www.npr.org/2026/07/25/nx-s1-5902982/democrats-maine-senate-race) |
| House | CA-03 — Party | R | **I** (Kiley; caucuses R) | [The Hill](https://thehill.com/homenews/house/5775383-kevin-kiley-independent-gop/); [Ballotpedia News, Mar 11](https://news.ballotpedia.org/2026/03/11/rep-kevin-kiley-becomes-the-10th-member-of-the-u-s-congress-to-change-party-affiliation-since-2000/) |
| Constants | NOTES | Jul 20 vacancy text | GA-13 runoff, CA-14 runoff wording, Nordone status | this briefing |

Also updated outside the patch: `corrections.json` (3 entries), `election_calendar.json` (10 events), `news_config.json` (MI/WI/FL/ME/AZ fields), `news_analysis.json` (12 races), `index.html` (5 DEMO_NEWS blocks).

### No action needed

- GA-13, CA-14, FL-20, TX-23 vacancies all still pending — no chamber-count change.
- MI and NM Governor: Sabato's July 23 moves landed on ratings the dashboard already carried.
- MO-05, CA-01, FL-09, FL-14 show D incumbents with R-leaning ratings (and vice versa). Checked — these are consequences of the 2025–26 re-redistricting, not sheet errors. Leaving them.

---

## Verification

Three independent subagents ran with claims only — no sources, drafts, or reasoning passed to them. 30 claims checked.

- ✅ **26 claims confirmed** by independent fact-check.
- ⚠️ **"Nordone is interim and not running" — CONTRADICTED.** She announced July 20 that she is running, with Trump's endorsement; two separate verifiers caught this independently. → Corrected in the patch, logged in `corrections.json`.
- ⚠️ **"FL Senate challenger is Alan Grayson" — CONTRADICTED.** Grayson is not in the field; it's Alex Vindman vs. Angie Nixon, and the verifier also flagged that Alex is frequently confused with his twin, Rep. Eugene Vindman (VA-01). → Corrected in the patch, logged in `corrections.json`.
- ⚠️ **"Michigan D Senate field is McMorrow / El-Sayed / Stevens" — CONTRADICTED.** McMorrow suspended July 5; she remains printed on the ballot. → Calendar note corrected, logged in `corrections.json`.
- ⚠️ **"Cook's July 16 House batch moved seven races" — CONTRADICTED on a technicality.** Cook moved *six* on July 16; the "Seven House Ratings Shift" article is from June 18. Last week's patch was still correct — it applied six Cook moves plus CA-22 from Sabato, seven total. Framing only, no data error, no correction logged.
- ⚠️ **CA-01 special election August 4 — UNRESOLVED, dropped.** One verifier surfaced a Ballotpedia page for a CA-01 special general on August 4; the other, working from the House Clerk's list, confirmed CA-01 was filled by James Gallagher on June 2. The Clerk is the primary source and wins, so nothing was added to the calendar. Worth a second look if it resurfaces.
- ⚠️ **Wisconsin GOP gubernatorial field — verifiers disagreed.** One reported Josh Schoemann and Bill Berrien on the August 11 ballot; the other found Schoemann exited in January after Trump endorsed Tiffany and no candidate named Berrien at all. Neither could be resolved to a primary source, so the calendar and news entries use the conservative wording "Tiffany, Trump-endorsed front-runner" and name no other Republicans.

### Scope note on the State News refresh (Contract 3.9)

This run refreshed **12 of 27** configured races rather than all of them: ME-Sen, MI-Sen, MI-Gov, WI-Gov, MN-Sen, KS-Gov, FL-Sen, AK-Sen, AZ-Gov, NH-Sen, TX-Sen, GA-Sen. Selection was by freshness risk — every state with a primary between August 4 and September 8, plus the two contests that resolved in the window (AZ, ME). The remaining 15 races carry article sets from the July 20 refresh. Calling this out rather than reporting a full refresh: `generated` was bumped to 2026-07-29, so the L2-freshness check will pass and would otherwise mask the partial coverage. The unrefreshed races should be prioritized next run.
