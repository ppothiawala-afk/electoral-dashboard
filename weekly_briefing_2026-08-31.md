# Electoral Dashboard — Weekly Briefing
**Week of August 25–31, 2026**

---

## ⚠️ PIPELINE ALERT — last week's patch is still pending (queued for today's apply)

Pre-flight found a pending **`constants_patch.json` dated 2026-08-25** and the newest archive only `constants_patch.applied_2026-08-17.json`. The Sheet confirms the Aug 25 patch has **not yet been applied**: Constants `LAST_UPDATED` still reads **2026-08-17**, and its row moves are not live (Sheet still shows OH-07 **Lean R**, MI-08 **Lean D**, MI-10 **Lean R**, and FL-Sen challenger "Alex Vindman (D) vs. Angie Nixon (D)").

**This is not a dead cron.** The Aug 24 Monday apply job ran fine but had nothing to apply (the patch didn't exist yet — it was written Aug 26). The Aug 25 patch's first apply slot is **today's** Monday job (≈1 PM PT), which had not yet run when this cycle executed Monday morning. Per Contract 1, the pending patch was left **byte-for-byte untouched** (validated ✅, integrity ✅) so today's apply can consume it. **No new `constants_patch.json` was written this cycle** — writing one would have clobbered the unapplied Aug 25 changes (the Check A trap).

What P-funk should see after today's apply: an archive `constants_patch.applied_2026-08-31.json`, Constants `LAST_UPDATED` → 2026-08-25, and OH-07/MI-08/MI-10 live on the Sheet. If that has **not** happened by Tuesday, the Monday apply job did not fire and needs inspection.

---

## Chamber Balance

No changes this week. Confirmed: 218R | 212D | 1I | 4V House / 53R | 47D | 2I Senate ([House Clerk](https://clerk.house.gov/Members/ViewVacancies), [House Press Gallery](https://pressgallery.house.gov/member-data/party-breakdown)). No House or Senate member died, resigned, or switched parties this week.

> ⚠️ Press Gallery caution: a search snapshot of the Press Gallery breakdown this week read **3** vacancies against the Clerk's **4** — the familiar Press-Gallery lag (departures post only when read on the floor). The known-good figure is **4**; do not lower it.

Two special elections resolved at the ballot box, but neither changes the count — a seat stays vacant until the successor is **sworn in**:

- **CA-14** — State Sen. **Aisha Wahab (D)** won the Aug 18 runoff over Melissa Hernandez (D), called ~Aug 20 ([CBS News SF, Aug 20](https://www.cbsnews.com/sanfrancisco/news/aisha-wahab-califonia-district-14-special-election-eric-swalwell/)). **Not yet sworn in** — CA-14 remains vacant. When seated, House D → 213 and vacancies → 3.
- **GA-13** — Democrat **Everton Blair Jr.** won the Aug 25 runoff over Marcye Scott (both D), ~52% ([FOX 5 Atlanta, Aug 25](https://www.fox5atlanta.com/news/georgia-election-results-everton-blair-wins-13th-congressional-district-runoff)). Safe-D seat; **not yet sworn in**, so the vacancy count holds.

Current 4 House vacancies:

- **CA-14** (Eric Swalwell, D — resigned Apr 14) — Wahab (D) won Aug 18, awaiting swearing-in ([CBS News SF, Aug 20](https://www.cbsnews.com/sanfrancisco/news/aisha-wahab-califonia-district-14-special-election-eric-swalwell/)).
- **FL-20** (Sheila Cherfilus-McCormick, D — resigned Apr 21) — no separate special; filled at the Nov 3 general ([Ballotpedia](https://ballotpedia.org/Florida's_20th_Congressional_District_election,_2026)).
- **GA-13** (David Scott, D — died Apr 22) — Blair (D) won the Aug 25 runoff, awaiting swearing-in ([FOX 5 Atlanta, Aug 25](https://www.fox5atlanta.com/news/georgia-election-results-everton-blair-wins-13th-congressional-district-runoff)).
- **TX-23** (Tony Gonzales, R — resigned Apr 14) — Gov. Abbott has still not called a special; filled Nov 3 ([Ballotpedia](https://ballotpedia.org/Texas's_23rd_Congressional_District_election,_2026)).

Senate: 53R / 47D / 2I — unchanged. Sanders-VT and King-ME are the two independents counted **inside** the 47-seat Democratic caucus; Murkowski-AK is a Republican ([senate.gov party division](https://www.senate.gov/history/partydiv.htm)).

---

## Notable Rating Shifts (Past Week)

### Applying today (from the pending Aug 25 patch — see Pipeline Alert)
These consensus (Cook + Sabato) moves were researched last cycle and are what today's apply job will write to the Sheet: **OH-07 Lean R → Toss-up**, **MI-08 Lean D → Likely D**, **MI-10 Lean R → Toss-up**, plus the FL-Sen challenger data fix to **Angie Nixon (D)**. They are already recorded in `history.json` (2026-08-25) and are **not** re-applied here.

### New this week (Aug 25–31) — reported, deferred to next patch
- **TX-Sen** — **consensus now reached.** ([Sabato's Crystal Ball, Aug 26](https://centerforpolitics.org/crystalball/2026-rating-changes/)) moved **Leans R → Toss-up**, joining Cook's Aug 20 Toss-up ([Cook Political Report, Aug 20](https://www.cookpolitical.com/analysis/senate/senate-overview/texas-and-iowa-senate-races-move-toss-races-governor-also-move)). Both forecasters now agree at **Toss-up** — which is exactly where the pending patch already holds the TX-Sen cell, so the value applying today is now consensus-correct. This resolves the TX half of the open Cook/Sabato split (decisions.json `2026-08-25-tx-ia-sen-consensus`).
- **IA-Sen** — **still split.** Cook Toss-up (Aug 20); Sabato has **not** matched (still Leans R). Under §2.3b the consensus rating is the last one both agreed on (Lean R). The pending patch nonetheless holds IA-Sen at **Toss-up** (the more-competitive branch, logged as the open decision). It will apply as Toss-up today; P-funk may prefer to revert it to Lean R next cycle until Sabato confirms — see Verification.
- **TX-15** (De La Cruz, R) — lone mover. ([Sabato's Crystal Ball, Aug 26](https://centerforpolitics.org/crystalball/2026-rating-changes/)) moved **Lean R → Toss-up** (part of a three-race Texas tranche, [Political Wire, Aug 26](https://politicalwire.com/2026/08/26/three-rating-changes-in-texas-move-towards-democrats/)). Cook still rates it Lean R. Per §2.3b a lone Sabato move does **not** move the cell (currently not on the sheet's competitive House list); logged as a note-only finding for next patch once Cook confirms or it fades.

No new Governor rating moves this week.

---

## IE Tilt Watch

Inside Elections divergences from the sheet — leading indicators only; per methodology §2.3a these do **not** move the Rating cell. Reconciled this week: no new confirmations or fades; all entries carried forward.

- **NC-Sen** — IE **Tilt D** ([Aug 6](https://www.270towin.com/2026-senate-election/inside-elections-2026-senate-ratings)) vs. sheet Lean D. ⏳ Open — Cook/Sabato still Lean D (Cooper still leads Whatley, but the race is tightening).
- **GA-Sen** — IE **Tilt D** ([Aug 6](https://www.270towin.com/2026-senate-election/inside-elections-2026-senate-ratings)) vs. sheet Lean D. ⏳ Open — Cook Lean D, Sabato Likely D; IE pulls toward Toss-up.
- **KS-Gov** — IE **Tilt R** ([Aug 6](https://www.270towin.com/2026-governors-election/inside-elections-2026-governor-ratings)) vs. sheet Lean R. ⏳ Open — late-Aug polling has Holscher (D) 47-46, consistent with IE's more-competitive read; no Cook/Sabato move yet.
- **IA-Sen** — IE **Tilt R** ([Aug 6](https://www.270towin.com/2026-senate-election/inside-elections-2026-senate-ratings)) vs. sheet Toss-up. ✅ **Confirmed** — Cook followed to Toss-up (Aug 20); IE was the early mover. Closed.
- **IA-Gov** — IE **Tilt D** ([Aug 6](https://www.270towin.com/2026-governors-election/inside-elections-2026-governor-ratings)) vs. sheet Lean D. ✅ **Confirmed** — Cook moved Toss-up → Lean D (Aug 20). Closed.

---

## Electoral Environment

The Senate map kept drifting toward a coin flip: Sabato's Aug 26 move on Texas ([Sabato's Crystal Ball, Aug 26](https://centerforpolitics.org/crystalball/2026-rating-changes/)) means both major forecasters now rate TX-Sen a Toss-up, so Ken Paxton — who ousted John Cornyn in the May 26 GOP runoff — is running even-to-behind Democrat James Talarico in a seat no one modeled as competitive a year ago ([Houston Public Media, Aug 25](https://www.houstonpublicmedia.org/articles/news/politics/election-2026/2026/08/25/560302/james-talarico-continues-to-edge-out-ken-paxton-in-texas-u-s-senate-race-new-poll-finds/)). Down-ballot in Texas, Sabato also nudged TX-15 and a statewide race toward Democrats ([Political Wire, Aug 26](https://politicalwire.com/2026/08/26/three-rating-changes-in-texas-move-towards-democrats/)). The Democratic pickup targets continued to look healthy: Roy Cooper leads in North Carolina though pollsters flag tightening after Labor Day ([Newsweek, Aug 21](https://www.newsweek.com/whatley-within-striking-distance-of-defeating-roy-cooper-in-north-carolina-12354446)), Abdul El-Sayed holds a narrow Michigan edge ([Forbes, Aug 31](https://www.forbes.com/sites/saradorn/2026/08/31/latest-2026-senate-polls-el-sayed-leads-rogers-by-4-points-in-michigan/)), and data-center backlash keeps Ohio unexpectedly live for Sherrod Brown ([Axios, Aug 19](https://www.axios.com/2026/08/19/gop-data-center-memo-ai-election)). At the gubernatorial level the competitive picture is stable, with Katie Hobbs comfortably ahead in Arizona ([KJZZ, Aug 24](https://www.kjzz.org/politics/2026-08-24/poll-hobbs-leading-biggs-by-15-points-in-arizona-governors-race)) and Kansas shaping up as the tightest open seat ([KWCH, Aug 28](https://www.kwch.com/2026/08/28/poll-shows-tight-race-kansas-governor/)).

---

## Candidate News

- **FL-Sen** — Democrat **Angie Nixon** consolidated her Aug 18 primary upset with a Bernie Sanders endorsement and hammered appointed Sen. Ashley Moody over a leaked grand-jury report tied to the Hope Florida controversy; forecasters still rate the seat Solid/Safe R ([Newsweek, Aug 27](https://www.newsweek.com/nixon-hits-hard-ashley-moody-10m-florida-scandal-polls-12375702)).
- **GA-Sen** — Rep. Mike Collins (R) drew negative coverage after a former campaign staffer was found to have posed in a KKK uniform and posted a swastika online, as Ossoff maintained a steady lead ([Atlanta News First, Aug 28](https://www.atlantanewsfirst.com/2026/08/28/ex-staffer-collins-senate-campaign-posed-kkk-uniform-posted-swastika-online/)).
- **IA-Sen** — Sen. Ted Cruz headlined an Ashley Hinson fundraiser, calling Democrats "Marxists and Islamists," as a Suffolk poll showed Hinson only 45-41 over Josh Turek ([Iowa Capital Dispatch, Aug 29](https://iowacapitaldispatch.com/2026/08/29/sen-ted-cruz-criticizes-democrats-as-marxists-and-islamists-at-hinson-event-in-iowa/)).
- **AK-Sen** — the ballot chaos of a second "Dan Sullivan" is now under federal investigation as Sen. Sullivan and Mary Peltola head to a November ranked-choice showdown ([Alaska Beacon, Aug 28](https://alaskabeacon.com/2026/08/28/sullivan-goes-on-attack-in-first-post-primary-faceoff-for-alaskas-u-s-senate-race/)).
- **ME-Sen** — Susan Collins agreed to four local TV debates with Troy Jackson while declining a CNN/BDN debate, amid a wave of misleading attack ads from both sides ([Bangor Daily News, Aug 27](https://www.bangordailynews.com/2026/08/27/politics/susan-collins-troy-jackson-debates/)).

---

## Sheet Updates

**No new patch was written this cycle.** The pending `constants_patch.json` (dated 2026-08-25) is what today's apply job will write to the Sheet. Its changes, restated for the record:

| Tab | Race | Old (live on Sheet) | New (applying today) | Source |
|---|---|---|---|---|
| House | OH-07 | Lean R | Toss-up | Cook Aug 10 + Sabato Aug 13 (consensus) |
| House | MI-08 | Lean D | Likely D | Cook + Sabato Aug 2026 (consensus) |
| House | MI-10 | Lean R | Toss-up | Cook Aug 25 + Sabato (long-standing) (consensus) |
| Senate | FL (Moody seat) | challenger "Vindman/Nixon (Aug 18 primary)" | challenger "Angie Nixon (D)" | Aug 18 primary result (data fix) |
| Senate | TX (Paxton seat) | Toss-up | Toss-up (held) | Cook Aug 20 / Sabato held then — now consensus (Sabato Aug 26) |
| Senate | IA (Ernst seat) | Toss-up | Toss-up (held) | Cook Aug 20; Sabato still Leans R (open decision) |
| Constants | LAST_UPDATED | 2026-08-17 | 2026-08-25 | — |

Chamber constants in the pending patch (unchanged): 218R / 212D / 1I / 4V House; 53R / 47D / 2I Senate.

### No action needed
Vacancies (CA-14, FL-20, GA-13, TX-23) still pending swearing-in / Nov 3. No chamber-balance change this week.

---

## Verification

- ✅ **No new patch claims to gate this cycle.** No new `constants_patch.json` was written (Pipeline Alert), so the Contract 3.5 ratings verifier had zero new claims and was skipped by rule. The pending Aug 25 patch's claims were already fact-checked when it was written.
- ✅ **Membership/results confirmed during research** (primary sources): GA-13 won by Everton Blair Jr. (D) on Aug 25 ([FOX 5 / GA SoS](https://sos.ga.gov/august-25th-us-house-district-13-special-election-runoff)); CA-14 won by Aisha Wahab (D), not yet sworn ([CBS News SF](https://www.cbsnews.com/sanfrancisco/news/aisha-wahab-califonia-district-14-special-election-eric-swalwell/)); no death/resignation/switch since Aug 24. Vacancy count 4 (Clerk authoritative; Press Gallery lagging at 3).
- ✅ **TX-Sen consensus confirmed** — Sabato Aug 26 Leans R → Toss-up corroborated by two independent secondary sources ([Political Wire](https://politicalwire.com/2026/08/26/three-rating-changes-in-texas-move-towards-democrats/), search-confirmed Sabato 2026 rating-changes log). Reported only; not applied (already the sheet's held value).
- ⚠️ **TX-15** — Sabato Aug 26 move logged as a lone-mover finding; NOT applied (Cook still Lean R). No sheet effect.
- 🗳️ **Awaiting your call** — IA-Sen Cook/Sabato split. The pending patch holds it at **Toss-up** (more-competitive branch); strict §2.3b consensus would hold it at **Lean R** until Sabato matches Cook. Ran with the pending patch's conservative-as-written value meanwhile; consider reverting IA-Sen to Lean R next cycle if Sabato has not moved. (decisions.json: `2026-08-25-tx-ia-sen-consensus`; TX half now resolved via Sabato Aug 26.)

---

## State News refresh (Contract 3.9)

Refreshed all 27 configured races via parallel fan-out (6 primary subagents + 2 targeted top-ups); `news_analysis.json`, `sentiment_history.json`, the 9 `DEMO_NEWS` On Deck blocks in `index.html`, and `ie_watch.json` all stamped 2026-08-31.

**Coverage: 23/27 races carry an article within 10 days (L2b).** The 4 below are genuinely quiet — best available datable coverage is older, not skipped:

- **ME-Gov** (newest Jul 21) — sleepy race; Pingree (D) heavily favored.
- **MN-Gov** (newest Aug 12) — Klobuchar (D) dominant favorite.
- **LA-Sen** (newest Aug 20, one day outside window) — no datable Aug 21–31 coverage found.
- **MT-Sen** (newest Aug 10) — coverage quieted after the Aug 10 ballot-withdrawal deadline.
