# Electoral Dashboard Weekly Briefing — June 15, 2026

## Chamber Balance — ACTION NEEDED

**House membership changed this week.** James Gallagher (R) was sworn in on June 10, 2026, filling the CA-1 vacancy left by the death of Rep. Doug LaMalfa (R-CA). [[Source]](https://thehill.com/homenews/house/5918833-california-republican-james-gallagher-sworn-in-doug-lamalfa-seat/)

**Constants tab update required** (I do not have write access to the Google Sheet — these changes need to be applied manually or via `update_sheet.py`):

| Key | Current | New |
| :-- | :-: | :-: |
| HOUSE_R | 217 | **218** |
| HOUSE_D | 212 | 212 (no change) |
| HOUSE_I | 1 | 1 (no change) |
| HOUSE_VACANCIES | 5 | **4** |
| LAST_UPDATED | 2026-06-02 | **2026-06-15** |

Validation check: 218 + 212 + 1 + 4 = 435 ✓

Also update the **House tab**: CA-01 should change from "VACANT / Solid D" to **James Gallagher (R), Solid R** (he won the seat that Trump carried heavily; LaMalfa's old district leans solidly Republican — current "Solid D" listing for that row appears to be a labeling error unrelated to this week's change, worth a second look).

**Remaining vacancies (4 after update):** FL-20, GA-14, TX-23, and CA-14 (pending — see below).

**CA-14 special election is happening tomorrow, June 16** (the day after this briefing), to fill Eric Swalwell's former seat. State Sen. Aisha Wahab held an early lead in initial reporting. If no candidate wins a majority, a runoff follows on August 18 — so this seat may remain vacant past tomorrow. Recommend checking results next Monday and updating Constants again if a winner is sworn in. [[Source]](https://www.cbsnews.com/sanfrancisco/news/alameda-county-voters-deciding-who-will-succeed-former-rep-eric-swalwell/)

No Senate membership changes found this week. No party switches identified.

---

## Notable Rating Shifts

**Texas Senate (Cornyn → Paxton):** Cook Political Report moved this race from Likely R to **Lean R** on June 12, following Ken Paxton's decisive runoff win over John Cornyn (64%–36%) on May 27. Cook cites Paxton's weak fundraising and ethics baggage (bribery allegations, a "biblical grounds" divorce) as making the seat newly competitive. The dashboard's Senate tab already lists TX as "Lean R" with Paxton as the primary winner — **this is up to date**. [[Source]](https://www.cookpolitical.com/analysis/senate/texas-senate/texas-senate-moves-lean-republican-after-paxton-runoff-win)

**Alaska Senate (Sullivan vs. Peltola) — FLAG:** Sabato's Crystal Ball moved this from Lean R to **Toss-up** on June 11, citing Mary Peltola's strength as a challenger. The dashboard currently shows AK as "Lean R" — **this is now stale relative to Crystal Ball's latest call** and worth a manual review/possible downgrade to Toss-up. [[Source]](https://centerforpolitics.org/crystalball/the-senate-the-race-for-the-majority-is-not-a-toss-up-but-the-races-that-will-decide-it-are/)

**Ohio Senate (Husted vs. Brown):** Also moved Lean R → Toss-up by Crystal Ball on June 11. The dashboard already lists OH Senate as "Toss-up" — **already current**.

**North Carolina Senate (Cooper vs. Whatley):** Crystal Ball moved this from Toss-up to **Lean D** on June 11. The dashboard already shows NC Senate as "Lean D" — **already current**.

**Florida House delegation (Cook, June 11):** FL-09 (Soto, D) moved Solid D → Likely R, and FL-14 (Castor, D) moved Solid D → Lean R. The dashboard's House tab already lists both as "Likely R" and "Lean R" respectively — **already current** (someone clearly updated these recently).

**Inside Elections House moves (June 11)** — directional changes, mostly minor refinements within already-competitive categories:
- CA-06 (Bera, D): Likely D → Lean D — dashboard shows "Solid D," slightly behind this move
- NJ-07 (Kean, R): Toss-up → Tilt D — dashboard shows "Toss-up," consistent
- OH-01 (Landsman, D): Toss-up → Tilt D — dashboard shows "Lean D," consistent direction
- PA-17 (Deluzio, D): Likely D → Safe D — dashboard shows "Solid D," consistent
- IA-03 (Nunn, R): Lean R → Tilt R — dashboard shows "Toss-up," in the same competitive neighborhood
- Others (IN-01, MI-08, NC-11, TX-15, OH-07, PA-08, WI-03) are minor refinements; none appear to represent a major category jump that the dashboard is missing.

---

## Environment Narrative

- **Texas Senate primary fallout**: Paxton's runoff win (May 27) continues to dominate Senate coverage. An early post-primary poll showed Democratic state Rep. James Talarico leading Paxton, reinforcing Cook's competitiveness re-rating. [[Source]](https://thehill.com/homenews/campaign/5902035-texas-senate-race-poll/)
- **House majority margin remains razor-thin.** With Gallagher's swearing-in, the House sits at 218 R / 212 D / 1 I / 4 vacancies — Republicans hold a net margin of 5 seats over Democrats, with the CA-14 special election (tomorrow) and three other vacancies still to be filled.
- **Crystal Ball's broader framing**: their June 11 analysis argues the overall battle for the Senate majority isn't itself a toss-up, but several of the individual races that will decide it (AK, OH, NC) now are — a notable framing shift for narrative purposes. [[Source]](https://centerforpolitics.org/crystalball/the-senate-the-race-for-the-majority-is-not-a-toss-up-but-the-races-that-will-decide-it-are/)
- **House overall picture (Crystal Ball)**: roughly 210 seats Safe/Likely/Lean D, 208 Safe/Likely/Lean R, and 17 Toss-ups — an extremely narrow battlefield with Democrats nominally on the cusp of 218.

---

## Candidate News

- **Mark Green (R-TN-07) resigned** from Congress in June for a private-sector job; TN-07 is Solid R and his eventual successor shouldn't change the chamber balance materially once seated. No swearing-in date confirmed yet — worth checking next week. [[Source]](https://thehill.com/homenews/house/5412871-tennessee-republican-mark-green-resigns-house/)
- **CA-14 special election** (Swalwell's former seat) is underway as of June 16 — results should be checked at next week's update.
- No new high-profile retirements or party switches identified this week beyond previously tracked departures.

---

## Sheet Flags Summary

1. **Constants tab**: HOUSE_R 217→218, HOUSE_VACANCIES 5→4, LAST_UPDATED→2026-06-15 (manual update needed — no Sheets write tool available this session).
2. **House tab, CA-01**: Update from VACANT to James Gallagher (R), and verify/correct the rating (currently shows "Solid D," which looks mismatched for a seat Republicans just won and that LaMalfa held safely).
3. **Senate tab, AK**: Consider updating from "Lean R" to "Toss-up" per Crystal Ball's June 11 move (Sullivan vs. Peltola).
4. **House tab, CA-06**: Consider tightening from "Solid D" toward "Likely D" / "Lean D" per Inside Elections' June 11 move.
5. **Tomorrow (June 16)**: CA-14 special election results — check next week and update Constants again if a winner is sworn in before the next cycle.

---

*Note: I was unable to write directly to the Google Sheet (Sheet ID 1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA) this session — only read access was available via the connected Drive tool. The Constants and House tab edits above should be applied via `update_sheet.py` or manually.*
