# Electoral Dashboard — Weekly Briefing
**Week of September 7–13, 2026**

---

## Pipeline note (pre-flight)

Last week's `constants_patch.json` (dated 2026-09-08) was **still pending** at the start of this run — it was committed and pushed to origin, but no Monday apply job has run since it was written (the 09-08 run fell after that week's Monday apply, so its patch was queued for the **upcoming** Monday, 2026-09-14). The Sheet confirms this: Constants `LAST_UPDATED` reads **2026-09-07** and last week's CA-14/GA-13/FL-20 changes are not yet live. Per Contract 1 the pending patch was **not overwritten or discarded** — this week's patch is a **superset** that carries those verified changes forward and adds this week's findings, so tomorrow's apply job applies everything at once. (An earlier scheduled attempt today aborted at pre-flight because the sandbox lacked file-delete permission and no one was present to grant it; that has since been granted and `preflight_sync.py` now exits 0.)

---

## Chamber Balance

No membership change this week. Confirmed: **218 R | 214 D | 1 I | 2 V House** / **53 R | 47 D | 2 I Senate** ([House Clerk](https://clerk.house.gov/Members/ViewVacancies), [Press Gallery](https://pressgallery.house.gov/member-data/party-breakdown)).

The House is 218 R / 214 D / 1 I with **2 vacancies**, live once tomorrow's apply job runs. Last week's two special-election winners are sworn in and confirmed on the Clerk's rolls: **CA-14 — Aisha Wahab (D)**, oath Sep 2 (Swalwell-D resigned Apr 14); **GA-13 — Everton Blair Jr. (D)**, oath Sep 1 (Scott-D died Apr 22) ([House Clerk vacancies](https://clerk.house.gov/Members/ViewVacancies)).

Current 2 House vacancies:
- **FL-20** (Cherfilus-McCormick, D — resigned Apr 21) — special-election date listed **TBD** by the Clerk ([House Clerk](https://clerk.house.gov/Members/ViewVacancies)).
- **TX-23** (Tony Gonzales, R — resigned Apr 14) — special-election date listed **TBD** by the Clerk ([House Clerk](https://clerk.house.gov/Members/ViewVacancies)).

Senate: **53 R / 47 D / 2 I** — Sanders-VT and King-ME counted inside the D caucus total; Murkowski-AK is R ([senate.gov party division](https://www.senate.gov/history/partydiv.htm)). No change.

---

## Notable Rating Shifts (Past Week)

### House
- **MO-05 (Cleaver, D — Kansas City)** — **Solid R → Solid D.** The Missouri Supreme Court blocked the 2025 GOP congressional map and ordered the 2022 lines used in November ([Missouri Independent, Sep 3](https://missouriindependent.com/2026/09/03/missouri-supreme-court-blocks-gerrymandered-congressional-map-orders-referendum-vote/); [CNN, Sep 3](https://www.cnn.com/2026/09/03/politics/missouri-supreme-court-blocks-trump-backed-map-midterms)), restoring MO-05 as a safe Kansas City Democratic seat. **Both** forecasters moved it: [Cook, Sep 11](https://www.cookpolitical.com/analysis/house/missouri-house/two-missouri-house-race-ratings-change-after-redistricting-roller) (Solid R → Solid D) and [Sabato, Sep 10](https://centerforpolitics.org/crystalball/rating-the-new-missouri-house-map/) (Safe R → Safe D) — a clean Cook+Sabato consensus. ✅ Applied. Resolves the sheet's prior "contingent" note.
- **MO-02 (Wagner, R — suburban St. Louis)** — **held at Solid R this week (change dropped).** The map reversion made MO-02 more competitive and both forecasters moved it off Solid R, but Cook's new tier is reported two incompatible ways from Cook's own material — the [article slug](https://www.cookpolitical.com/analysis/house/missouri-house/mo-02-wagner-moves-likely-republican-lean-republican) reads "Likely R → Lean R" while the [roundup](https://www.cookpolitical.com/analysis/house/missouri-house/two-missouri-house-race-ratings-change-after-redistricting-roller) prose reads "Solid R → Likely R." Sabato is at [Likely R](https://centerforpolitics.org/crystalball/rating-the-new-missouri-house-map/). Because whether this is a consensus (both Likely R → move) or a split (Cook Lean R → hold) turns on a fact I could not settle against a readable primary, the change is dropped per Contract 3.5 and queued for your call (decisions.json: `2026-09-13-mo-02-cook-tier`).
- **Lone Sabato movers (cells hold per §2.3b consensus):** [AL-02, Sep 10](https://centerforpolitics.org/crystalball/2026-rating-changes/) (Likely R → Lean R) and [TX-34, Sep 10](https://centerforpolitics.org/crystalball/three-rating-changes-in-texas-all-towards-democrats/) (Toss-up → Lean D) are Sabato-only; Cook has not matched, so the Rating cells do not move.

### Governors
- **AK-Gov** — [Sabato moved Likely R → Toss-up, Sep 3](https://www.mediaite.com/politics/sabatos-crystal-ball-moves-three-gubernatorial-races-left-giving-democrats-chance-to-get-majority/), but [Cook still rates it Likely R](https://www.cookpolitical.com/analysis/governors/alaska-governor/ranked-choice-complexities-move-alaska-governor-likely). Lone mover → cell **holds at Likely R** (unchanged from last week's determination).

### Senate
- No Cook or Sabato Senate rating change was published in the Sep 6–13 window (independently confirmed). TX-Sen and IA-Sen remain Lean R under the standing consensus rule.

---

## Matchups Resolved (calendar + notes updated)

- **NH Senate (Sep 8 primary)** — **Rep. Chris Pappas (D)** (def. Karishma Manzur ~62-36) vs **former Sen. John E. Sununu (R)** (def. Scott Brown ~70-25, Trump-endorsed); open seat, Shaheen retiring ([NBC News, Sep 8](https://www.nbcnews.com/politics/2026-election/chris-pappas-john-sununu-new-hampshire-senate-primary-winner-rcna596479)). Sheet note refreshed; rating unchanged **Lean D**.
- **NH Governor** — Gov. **Kelly Ayotte (R)** vs **Cinde Warmington (D)** confirmed after the Sep 8 primary ([NBC News, Sep 8](https://www.nbcnews.com/politics/2026-election/gop-gov-kelly-ayotte-democrat-cinde-warmington-face-new-hampshire-gove-rcna596481)).
- **SC Senate (Aug 25 GOP runoff)** — appointed **Sen. Darline Graham Nordone (R)** defeated Rep. Ralph Norman ~52.5%; faces **Annie Andrews (D)** Nov 3 ([NPR, Aug 25](https://www.npr.org/2026/08/25/nx-s1-5943041/south-carolina-senate-runoff-graham-norman-trump-endorsement)). Neither Norman nor Fry vacated a House seat. Sheet note refreshed; rating unchanged **Solid R**.

---

## IE Tilt Watch

Inside Elections divergences from the sheet — leading indicators only; per §2.3a these do **not** move the Rating cell. No Cook/Sabato follow-through this week, so all open entries remain open.

- **AK-Sen** — IE **Tilt R** ([Sep 3](https://www.270towin.com/2026-senate-election/inside-elections-2026-senate-ratings)) vs sheet **Toss-up**. ⏳ open.
- **NH-Sen** — IE **Toss-up** (Sep 2) vs sheet **Lean D**. ⏳ open (primary now resolved Pappas vs Sununu; watch for Cook/Sabato).
- **NC-Sen** — IE **Tilt D** vs sheet **Lean D**. ⏳ open.
- **GA-Sen** — IE **Tilt D** vs sheet **Lean D** (Sabato Likely D unadopted under consensus). ⏳ open.
- **KS-Gov** — IE **Tilt R** vs sheet **Lean R**. ⏳ open.
- **FL-14** — IE **Tilt R** vs sheet **Toss-up**. ⏳ open.
- **TX-15** — IE **Tilt R** vs sheet **Lean R**. ⏳ open.
- IA-Sen and IA-Gov remain **confirmed** (Cook followed IE on Aug 20).

---

## Electoral Environment

The week's structural story was Missouri: the state Supreme Court's Sep 3 ruling reinstating the 2022 congressional map is worth an estimated one-seat swing toward Democrats in the House battle, snapping MO-05 back to safe-D and making MO-02 more competitive ([The Hill, Sep 11](https://thehill.com/homenews/6085372-missouri-redistricting-election-chaos/)). Elsewhere, new September polling showed Democrats holding or extending narrow edges in several toss-ups — Nevada Gov. (Ford +2, [Las Vegas Sun, Sep 10](https://lasvegassun.com/news/2026/sep/10/aaron-ford-edges-past-joe-lombardo-in-latest-poll/)), Maine Sen. (dead heat, [CNN via Press Herald, Sep 9](https://www.pressherald.com/2026/09/09/still-no-space-between-susan-collins-troy-jackson-in-maine-senate-race-cnn-poll-finds/)) — while Republicans pointed to a tightening Minnesota Senate race (Flanagan +2, [RedState, Sep 9](https://redstate.com/terichristoph/2026/09/09/michele-tafoya-just-put-democrats-on-notice-in-minnesota-n2206691/)). With the last regular primary (NH) now behind us, every 2026 field is set ahead of the Nov 3 general.

---

## Candidate News

- **TX-Sen** — Ken Paxton's personal financial disclosures "appear to violate" state ethics law ([Texas Tribune, Sep 4](https://www.texastribune.org/2026/09/04/texas-ken-paxton-personal-financial-disclosures-ethics-law-us-senate-race/)); a former Paxton whistleblower endorsed Talarico ([Texas Tribune, Sep 8](https://www.texastribune.org/2026/09/08/ken-paxton-whistleblower-endorses-james-talarico-texas-senate-david-maxwell/)).
- **OH-Gov** — An armed man charged at Democrat Amy Acton at the Sep 6 Canfield Fair, drawing bipartisan condemnation ([Newsweek, Sep 7](https://www.newsweek.com/amy-acton-attack-ohio-vivek-ramaswamy-polls-12413129)).
- **MT-Sen** — A Sep 11 Montana Free Press poll shows Republican Kurt Alme leading (38%) as independent Bodnar (30%) and Democrat Bankhead (16%) split the opposition ([Montana Free Press, Sep 11](https://montanafreepress.org/2026/09/11/alme-holds-an-8-point-lead-over-bodnar-in-senate-race/)).

---

## Sheet Updates

| Tab | Race | Old | New | Source |
|---|---|---|---|---|
| House | MO-05 (Cleaver, D) | Solid R | **Solid D** | [Cook Sep 11](https://www.cookpolitical.com/analysis/house/missouri-house/two-missouri-house-race-ratings-change-after-redistricting-roller) + [Sabato Sep 10](https://centerforpolitics.org/crystalball/rating-the-new-missouri-house-map/) (MO map reverted to 2022 lines) |
| House | CA-14 | VACANT | Wahab (D), Solid D | [House Clerk](https://clerk.house.gov/Members/ViewVacancies) — carried forward from 09-08 |
| House | GA-13 | VACANT | Blair (D), Solid D | [House Clerk](https://clerk.house.gov/Members/ViewVacancies) — carried forward from 09-08 |
| House | FL-20 | R / Solid R | D / Solid D | Data fix — carried forward from 09-08 (corrections.json) |
| Senate | NH-Sen note | pre-primary | post-primary (Pappas vs Sununu) | [NBC, Sep 8](https://www.nbcnews.com/politics/2026-election/chris-pappas-john-sununu-new-hampshire-senate-primary-winner-rcna596479) — rating unchanged |
| Senate | SC-Sen note | runoff pending | Nordone won runoff, faces Andrews | [NPR, Aug 25](https://www.npr.org/2026/08/25/nx-s1-5943041/south-carolina-senate-runoff-graham-norman-trump-endorsement) — rating unchanged |
| Constants | LAST_UPDATED | 2026-09-07 | 2026-09-13 | this run |

### No action needed
- Chamber counts unchanged (218 R / 214 D / 1 I / 2 V House; 53 R / 47 D / 2 I Senate).
- AK-Gov, AL-02, TX-34 lone Sabato movers — cells hold per §2.3b.
- FL-20 and TX-23 special-election dates remain TBD (Clerk).

---

## Verification

- ✅ 9 rating/map claims confirmed by independent fact-check (ratings verifier), plus chamber/membership and matchup verifiers — all CONFIRMED against Cook, Sabato, House Clerk, Press Gallery, senate.gov, NBC/NPR/Ballotpedia.
- ⚠️ **MO-02 (Cook tier) — CONTRADICTED / UNVERIFIABLE:** verifier and Cook's own slug and roundup disagree (Lean R vs Likely R). **Dropped** from the patch per Contract 3.5; MO-02 holds at Solid R. Queued as decisions.json `2026-09-13-mo-02-cook-tier`.
- ✅ No Cook/Sabato Senate or Governor rating change published in the Sep 6–13 window (confirmed — no missed consensus).
- 🗳️ Awaiting your call — MO-02 Rating tier (Cook Likely R vs Lean R). Ran with the conservative branch (hold Solid R) meanwhile. (decisions.json: `2026-09-13-mo-02-cook-tier`)
- **State News refresh:** 27/27 configured races rescored with dated, deep-linked coverage; **L2b coverage = 25/27**. Genuinely stale (no datable coverage within 10 days — campaigns quiet until October debates): **WI-Governor** (newest datable Sep 2) and **AZ-Governor** (newest datable Aug 24). No dates were inferred.

---

*Corrections log: no new published-error corrections this week (the FL-20 R→D fix was logged 2026-09-08 and is carried forward).*
