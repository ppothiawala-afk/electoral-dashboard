# Electoral Dashboard — Weekly Briefing
**Week of June 29–July 5, 2026**

---

## Chamber Balance

No changes this week. Confirmed: **218 R | 212 D | 1 I | 4 V House / 53 R | 47 D Senate** ([House Clerk](https://clerk.house.gov/Members/ViewVacancies), [Press Gallery](https://pressgallery.house.gov/member-data/party-breakdown) — note the Press Gallery page still shows 5 vacancies because it hasn't been re-cached since [Gallagher's June 10 swearing-in](https://rollcall.com/2026/06/10/james-gallagher-sworn-in-to-finish-lamalfas-term-in-the-house/); the known-good count is 4).

Current 4 House vacancies:
- **CA-14** (Swalwell, D — resigned Apr 14) — special general/runoff **Aug 18**: Aisha Wahab (D) vs. Melissa Hernandez ([Gov. Newsom proclamation, Apr 14](https://www.gov.ca.gov/2026/04/14/governor-newsom-issues-proclamation-setting-special-election-for-california-congressional-district-14/))
- **FL-20** (Cherfilus-McCormick, D — resigned Apr 21) — special date still TBD; candidates filed for an Aug 18 primary tied to the regular cycle ([Ballotpedia](https://ballotpedia.org/Florida's_20th_Congressional_District_election,_2026))
- **GA-13** (Scott, D — died Apr 22) — special election **July 28** (runoff Aug 25 if no majority) ([Georgia SoS](https://sos.ga.gov/news/call-special-election-congressional-district-13))
- **TX-23** (Gonzales, R — resigned Apr 14) — date not set; Abbott expected to call an emergency special or consolidate with Nov 3 ([TPR, Apr 15](https://www.tpr.org/government-politics/2026-04-15/when-will-gov-abbott-call-a-special-election-for-texas-23rd-congressional-district))

Senate: 53 R / 47 D / 3 I — counted inside caucus totals per dashboard convention; no change. ⚠️ One verifier flagged that [Murkowski remains a registered Republican](https://ballotpedia.org/Lisa_Murkowski) and only Sanders-VT and King-ME are formally independents — the seat math (53/47) is unaffected, but the SENATE_I=3 convention note may deserve a documentation review. No constants were changed.

---

## Notable Rating Shifts (Past Week)

### Senate
- **Alaska** — ([Cook Political Report, July 1](https://www.cookpolitical.com/analysis/senate/alaska-senate/alaska-senate-shifts-toss-column)) moved **Lean R → Toss-up**, after the [Alaska Supreme Court ruled June 29](https://www.adn.com/politics/2026/06/29/alaska-supreme-court-rules-that-dan-j-sullivan-can-appear-on-the-ballot-against-sen-dan-sullivan/) that a second "Dan Sullivan" (Dan J. Sullivan, no party) may appear on the Aug 18 primary ballot alongside Sen. Dan S. Sullivan (R), potentially siphoning GOP votes in the top-four/RCV system against Mary Peltola (D). **Sheet already shows Toss-up** (Sabato moved it there [June 11](https://centerforpolitics.org/crystalball/2026-rating-changes/)) — ✅ no rating change needed; AK Notes updated. Forecasters now diverge: Cook Toss-up, Sabato Toss-up, [Inside Elections still Lean R](https://insideelections.com/ratings/senate) (as of Jun 25).

### House
- No new forecaster moves in the window ([Sabato's rating-changes page](https://centerforpolitics.org/crystalball/2026-rating-changes/) last dated Jun 11; [Inside Elections House](https://insideelections.com/ratings/house) last dated Jun 11).

### Governors
- No new moves this week. Context/watch item: [Inside Elections' June 25 batch](https://www.270towin.com/2026-governor-election/inside-elections-governor-2026) (GA Tilt R → Toss-up, IA Lean R → Toss-up, MI Toss-up → Tilt D, OH Likely → Lean R, among others) is broadly consistent with the sheet's current ratings; MI (IE Tilt D vs. sheet Toss-up) is the one to watch if Cook/Sabato follow.

---

## Electoral Environment

Democrats retain a stable mid-single-digit generic-ballot edge, with [aggregated averages around D+4 to D+7](https://www.racetothewh.com/polls/genericballot) and [RealClearPolling showing similar spreads](https://www.realclearpolling.com/polls/state-of-the-union/generic-congressional-vote). Trump approval continues to average [~39–40%](https://uspollingdata.com/), a structural tailwind for Democrats in swing seats. In Alaska, a [NYT/Siena poll released July 1](https://alaskawatchman.com/2026/07/01/sullivan-holds-slim-lead-over-peltola-in-nyt-alaska-senate-poll/) shows Sullivan holding only a slim lead over Peltola, consistent with the forecaster moves to Toss-up. The [DSCC is publicly framing Alaska](https://www.dscc.org/article/new-alaska-senate-race-shifts-towards-peltola-as-democrats-move-within-striking-distance-of-majority/) as putting Democrats "within striking distance" of the majority — partisan framing, but it signals real investment.

---

## Candidate News

- **AK Senate:** The [Alaska Supreme Court ruled June 29](https://alaskabeacon.com/2026/06/29/alaska-supreme-court-rules-dan-j-sullivan-eligible-to-run-for-us-senate/) that Dan J. Sullivan Jr. (retired teacher, Petersburg) is eligible for the Aug 18 primary ballot; the ballot will distinguish "Sullivan, Daniel J. Jr." from "Sullivan, Dan S." ([NPR, Jun 30](https://www.npr.org/2026/06/30/nx-s1-5875485/dan-sullivan-is-challenging-sen-dan-sullivan-on-alaskas-primary-ballot)).
- **GA Governor (correction):** Rick Jackson (R) defeated Burt Jones in the [June 16 GOP runoff](https://www.newsnationnow.com/politics/2026-midterm-elections/georgia-governor-primary-runoff-election-results-2026/amp/); the general is **Jackson (R) vs. Keisha Lance Bottoms (D)** ([Wikipedia](https://en.wikipedia.org/wiki/2026_Georgia_gubernatorial_election)). The sheet still described the R field as unsettled — fixed this week (see Sheet Updates + corrections log).
- **GA Senate:** Mike Collins confirmed as the GOP nominee vs. Ossoff after winning the runoff ~55.5% with a late Trump endorsement ([NBC News](https://www.nbcnews.com/politics/2026-election/georgia-senate-midterms-primary-winner-collins-rcna350028)) — sheet already correct.
- **AZ Governor:** Primary is **July 21**. Hobbs (D) faces minimal primary opposition; Biggs (Trump-endorsed, ~50%) leads Schweikert (~8%) for the GOP nod; [Emerson has Hobbs–Biggs at 44–43](https://emersoncollegepolling.com/arizona-2026-governor/) ([Ballotpedia](https://ballotpedia.org/Arizona_gubernatorial_and_lieutenant_gubernatorial_election,_2026)) — config verified current (Robson dropped out in February).
- **Upcoming:** GA-13 special July 28; AZ primary July 21; CA-14 special general and AK primary Aug 18.

---

## Sheet Updates

| Tab | Race | Old | New | Source |
|---|---|---|---|---|
| Constants | LAST_UPDATED | 2026-07-02 | 2026-07-06 | — |
| Senate | AK — Sullivan (R) vs Peltola (D) | Toss-up (notes stale) | Toss-up + notes: Cook joined Sabato Jul 1; IE still Lean R | [Cook, Jul 1](https://www.cookpolitical.com/analysis/senate/alaska-senate/alaska-senate-shifts-toss-column) |
| Governors | GA — open (Kemp term-limited) | Notes implied R field unsettled / Jones-led | Toss-up (unchanged) + notes: Jackson (R) def. Jones in Jun 16 runoff; vs. Bottoms (D) | [NewsNation, Jun 16](https://www.newsnationnow.com/politics/2026-midterm-elections/georgia-governor-primary-runoff-election-results-2026/amp/) |

Also updated locally: `news_config.json` GA Governor candidate list (Burt Jones removed post-runoff); `corrections.json` entry appended for the GA nominee staleness.

### No action needed
- Chamber constants unchanged (218/212/1/4; 53/47/3).
- AK Senate rating already Toss-up; TX Senate (Paxton/Talarico, Lean R), GA Senate (Collins nominee) already correct.
- `index.html` DEFAULT_SENATE fallback array is stale vs. the Sheet (e.g. AK "Lean R", TX "Cornyn/Likely R", MT/KS/VA incumbent errors) — the `sync_fallbacks.py` step in today's 1 PM PT Actions run regenerates all fallback arrays from the verified Sheet, so this self-heals on apply; verify after the run.

---

## Verification

- ✅ 11 claims confirmed by independent fact-check (3 subagents: ratings, membership/balance, candidate matchups)
- ⚠️ GA Governor nominee — CONTRADICTED: verifier found Rick Jackson (R) won the June 16 runoff over Burt Jones → sheet notes + news_config fixed, corrections.json entry added
- ⚠️ "Inside Elections moved AK to Toss-up July 1" (initial search summary) — CONTRADICTED: IE's own site still shows Lean R (Jun 25) → move attributed to Cook only
- ⚠️ Murkowski counted among 3 Senate independents (dashboard convention) — verifier found she remains a registered Republican; seat math unaffected, SENATE_I left at 3 per skill convention → flagged for documentation review, no constant changed
- ⚠️ Press Gallery shows 5 vacancies — known-stale (pre-Gallagher); Clerk-based count of 4 retained per vacancy-floor rule

---

*Pipeline note: pre-flight passed — the 6/29 patch was applied and archived 7/2 (plus 7/3 corrections patch); history.json current through 6/29. This week's `constants_patch.json` is committed for the Monday 1 PM PT Actions apply run.*
