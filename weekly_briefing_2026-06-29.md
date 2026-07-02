# Electoral Dashboard — Weekly Briefing
**Week of June 29, 2026**

---

## Chamber Balance

No changes this week. Current composition per House Clerk (confirmed as of June 29):

| | R | D | I | Vacancies | Total |
|---|---|---|---|---|---|
| **House** | 218 | 212 | 1 | 4 | 435 |
| **Senate** | 53 | 47 | 3\* | — | 100 |

\*Senate Independent count (Sanders-VT, King-ME, Murkowski-AK) caucus breakdown unchanged.

****Active House Vacancies** (4, per [House Clerk](https://clerk.house.gov/Members/ViewVacancies)):
- **CA-14** — Eric Swalwell (D) resigned Apr 14. Special general election Aug 18, 2026 (Wahab vs. Hernandez runoff).
- **FL-20** — Sheila Cherfilus-McCormick (D) resigned Apr 21. Special election date TBD.
- **GA-13** — David Scott (D) died Apr 22. Special election July 28, 2026.
- **TX-23** — Tony Gonzales (R) resigned Apr 14. Special election date TBD.

Previously vacant seats now filled: [James Gallagher (R) sworn in June 10](https://rollcall.com/2026/06/10/james-gallagher-sworn-in-to-finish-lamalfas-term-in-the-house/) (CA-01); [Clay Fuller (R) sworn in April 14](https://www.cbsnews.com/atlanta/news/republican-clay-fuller-sworn-into-house-after-winning-georgias-14th-district-special-election/) (GA-14).

---

## Notable Rating Shifts This Week

### Senate
**Texas (Cornyn → Paxton):** [Cook Political Report shifted TX Senate from **Likely R → Lean R** on June 26](https://thehill.com/homenews/campaign/5896436-texas-senate-race-rating-shift/), after [Ken Paxton defeated Sen. John Cornyn in the May 26 GOP runoff](https://www.texastribune.org/2026/05/26/texas-john-cornyn-ken-paxton-us-senate-republican-primary-runoff/). Paxton enters the general against Democratic state Rep. James Talarico. Cook cites Paxton's ethical vulnerabilities (bribery allegations, marital infidelity, weak fundraising) and Talarico's fundraising edge. [Current polling: Paxton +1.3 (45.8% vs 44.5%)](https://thehill.com/homenews/campaign/5902035-texas-senate-race-poll/). Inside Elections followed. This is the biggest Senate shift of the week.

Earlier in June (for context):
- **Ohio Senate:** [Sabato's moved OH (Jon Husted vs. Sherrod Brown) to **Toss-up**](https://centerforpolitics.org/crystalball/2026-rating-changes/) (June 11).
- **North Carolina Senate:** [Sabato's moved to **Lean D**](https://centerforpolitics.org/crystalball/2026-senate/) (June 11) — Roy Cooper vs. Michael Whatley.
- **Alaska Senate:** Sabato's moved to **Toss-up** (June 11) — Sullivan vs. Peltola.
- **Iowa Senate:** Moved from Likely R → Toss-up (Sabato's) and Likely R → Lean R (Cook) on June 2.

### House
[Cook June 25 shifts](https://www.cookpolitical.com/ratings/house-race-ratings) (redistricting/candidate-driven):
- **FL-09** (Darren Soto, D): Solid D → **Likely R** — significant flip risk flagged.
- **FL-14** (Kathy Castor, D): Solid D → **Lean R** — competitive after map changes.

[Inside Elections June 11 shifts](https://www.insideelections.com/ratings/house):
- MI-08: Lean D → Likely D
- NC-11: Likely R → Lean R
- NJ-07: Toss-up → Lean D (their "Tilt D")
- OH-01: Toss-up → Lean D
- PA-08, WI-03: Lean R → Toss-up

[Sabato's current House summary](https://centerforpolitics.org/crystalball/2026-house/): R 213, D 206, Toss-ups 16 (13 R-held, 3 D-held).
[Cook current House summary](https://www.cookpolitical.com/ratings/house-race-ratings): R 212, D 205, Toss-ups 18.

---

## Electoral Environment

**Generic ballot:** Democrats hold a consistent advantage heading into summer. [Aggregated averages show D+4 to D+7](https://www.racetothewh.com/polls/genericballot) depending on source; [most recent Economist/YouGov shows a narrower D+2](https://www.realclearpolling.com/polls/state-of-the-union/generic-congressional-vote) among registered voters. [Morning Consult has D+4](https://pro.morningconsult.com/trackers/2026-midterm-election-generic-ballot-polls). [Emerson June poll showed D+10](https://emersoncollegepolling.com/june-2026/). The range reflects methodological differences; the trend is stable Dem advantage, not expanding.

**Trump approval:** [Averaging ~39-40%](https://uspollingdata.com/), providing structural tailwind for Democratic candidates in swing districts.

---

## Candidate News

- **TX Senate:** [Ken Paxton officially the GOP nominee after May 26 runoff win over Cornyn](https://www.texastribune.org/2026/05/26/texas-john-cornyn-ken-paxton-us-senate-republican-primary-runoff/). General election is Paxton vs. James Talarico (D). [Two Republican Cornyn-endorsers have since backed Paxton](https://www.cbsnews.com/texas/news/two-republican-lawmakers-endorsed-john-cornyn-now-back-ken-paxton-texas-senate-race/).
- **No major new retirement announcements** confirmed this week. June is historically the quietest month for retirement announcements.
- **NY primaries (June 23):** Reps. Adriano Espaillat and Dan Goldman both lost Democratic primaries — primary losers do not create vacancies (seats remain D-held), but new nominees' strength may affect ratings. **Flag for manual verification.**

---

## Sheet Flags — Action Items

The `constants_patch.json` has been updated and will be applied by the Monday 1pm cron job. Changes queued:

**Constants tab:** LAST_UPDATED → 2026-06-29, NOTES corrected (CA-01 and GA-14 no longer listed as vacant).

**House tab rating corrections (data errors, not opinion changes):**
| District | Incumbent | Error | Correct |
|---|---|---|---|
| MO-05 | Emanuel Cleaver (D) | Solid R | Solid D |
| TN-09 | Steve Cohen (D) | Solid R | Solid D |
| TX-09 | Al Green (D) | Solid R | Solid D |
| TX-32 | Julie Johnson (D) | Solid R | Solid D |
| TX-35 | Greg Casar (D) | Likely R | Solid D |

**House tab rating updates (forecaster-driven):**
| District | Change |
|---|---|
| FL-09 | Solid D → Likely R (Cook June 25) |
| FL-14 | Solid D → Lean R (Cook June 25) |

**Senate tab update:**
| Race | Change |
|---|---|
| TX | Likely R → Lean R (Cook June 26); Challenger updated to James Talarico (D) |

---

---

*Briefing generated 2026-06-29. Primary sources: [House Clerk Vacancies](https://clerk.house.gov/Members/ViewVacancies) · [House Press Gallery Party Breakdown](https://pressgallery.house.gov/member-data/party-breakdown) · [Cook Political Report](https://www.cookpolitical.com/ratings) · [Sabato's Crystal Ball](https://centerforpolitics.org/crystalball/2026-rating-changes/) · [Inside Elections](https://www.insideelections.com/ratings/house) · [270toWin](https://www.270towin.com/2026-senate-election/) · [Texas Tribune](https://www.texastribune.org/2026/05/26/texas-john-cornyn-ken-paxton-us-senate-republican-primary-runoff/) · [The Hill](https://thehill.com/homenews/campaign/5896436-texas-senate-race-rating-shift/)*
