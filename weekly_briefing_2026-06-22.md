# Electoral Dashboard — Weekly Briefing
**Week of June 16–22, 2026**

---

## Chamber Balance

**No changes this week.** Confirmed count: **218 R | 212 D | 1 I | 4 Vacancies** (= 435 ✓).

> ⚠️ **Patch correction:** The `constants_patch.json` found at the start of this run contained an error — it listed HOUSE_R=217 and 5 vacancies, still showing CA-01 as vacant. This was incorrect. James Gallagher (R, CA-01) was sworn in **June 10, 2026**; the June 15 applied patch already captured this. The corrected patch (218R/4V, updated NOTES) has been written and replaces the erroneous one.

**Current 4 vacancies:**
- CA-14 (Swalwell, D) — special primary held June 16; no majority winner; runoff August 18 (D vs D — safe D seat)
- FL-20 (Cherfilus-McCormick, D) — primary TBD, general November 3
- GA-13 (Scott, D) — special election July 28; runoff August 25 if no majority (safe D seat)
- TX-23 (Gonzales, R) — Governor Abbott has not yet scheduled a special election; likely November 3 concurrent with general

**Senate: 53R / 47D / 3I** — no change this week.

---

## Notable Rating Shifts (Past Week)

### Senate
- **Alaska** — Sabato (June 11) moved from **Lean R → Toss-up**. Sheet currently shows Toss-up. ✅
- **Ohio (Special)** — Sabato (June 11) moved from **Lean R → Toss-up** (Husted vs. Sherrod Brown). Sheet shows Toss-up. ✅
- **North Carolina** — Sabato (June 11) moved from **Toss-up → Lean D** (Cooper now clear frontrunner). Sheet shows Lean D. ✅
- **Iowa** — Sabato (June 2/3) moved from **Likely R → Lean R** (Hinson vs. Turek, internal poll showed Turek leading). **⚠ Sheet still shows "Likely R" — needs manual update to "Lean R".**
- **Texas** — Cook moved from **Likely R → Lean R** after Ken Paxton defeated Cornyn in the runoff. Sheet shows Lean R. ✅

### House
- **Inside Elections (June 11):** Multiple moves reflecting improved Democratic environment:
  - CA-06 (Bera, D): Likely D → Lean D *(sheet shows Lean D ✅)*
  - IA-03 (Nunn, R): Lean R → Tilt R (comparable to Lean R in sheet's scale) *(sheet shows Toss-up — may need review)*
  - IN-01 (Mrvan, D): Lean D → Likely D *(sheet shows Likely D ✅)*
  - MI-08 (McDonald Rivet, D): Lean D → Likely D *(sheet shows Lean D — stale)*
  - NC-11 (Edwards, R): Likely R → Lean R *(sheet shows Likely R — stale)*
  - NJ-07 (Kean, R): Toss-up → Tilt D *(sheet shows Toss-up — approaching Lean D territory)*
  - OH-01 (Landsman, D): Toss-up → Tilt D *(sheet shows Lean D — consistent)*
  - OH-07 (Miller, R): Toss-up → Likely R *(sheet shows Solid R — may be ahead of Inside Elections)*
  - PA-08 (Bresnahan, R): Tilt R → Toss-up *(sheet shows Toss-up ✅)*
  - WI-03: Tilt R → Toss-up *(district not clearly in sheet — verify)*

- **Cook Political Report (June 18):** Post-redistricting updates for newly redrawn seats:
  - FL-09 (Soto, D): Solid D → Likely R *(sheet already shows Likely R ✅)*
  - FL-14 (Castor, D): Solid D → Lean R *(sheet shows Lean R ✅)*
  - MO-05 (Cleaver, D): Solid D → Solid R *(sheet shows Solid R ✅ — redistricting)*

### Governors
- **Iowa** — Cook shifted Kim Reynolds' open seat from **Likely R → Toss-up** (April); Sabato now at Toss-up as of June. **Sheet shows Toss-up ✅.**

---

## Environment Narrative

Democrats continue to hold a structural polling advantage heading into the fall. The generic ballot sits at approximately **D+6 to D+7** (RealClear average D+4.8, Silver Bulletin/538 tracker around D+6–7), with independents breaking D+12 — a 9-point shift toward Democrats since January 2025. Women are at D+11, men at R+5.

The Texas Senate race has emerged as a tier-one pickup opportunity for Democrats after Ken Paxton defeated incumbent Sen. John Cornyn in the GOP runoff. Cook and Sabato both moved it to Lean R immediately post-runoff. Democrat James Talarico holds a fundraising lead and is running 3–5 points ahead in recent polling — the first credible Democratic path to winning Texas statewide in the modern era.

The breadth of House retirements — 58 members and 2 delegates not seeking re-election, second-most in modern history behind 1992 — is structurally favorable for Democrats, as a disproportionate number (36R vs. 24D) are Republicans vacating competitive-leaning seats.

---

## Candidate News

- **CA-14 special election (June 16):** Swalwell's D+D runoff (Wahab vs. Hernandez) set for August 18. Safe D seat; no partisan implications.
- **GA-13 special election (July 28):** Multiple Democrats including Marcye Scott (David Scott's daughter), Everton Blair, Jasmine Clark, and Emanuel Jones are competing for the safe D seat.
- **TX-23:** Governor Abbott has remained silent on scheduling; both parties are maneuvering — Democrats see an opportunity against GOP nominee Brandon Herrera (firearms manufacturer/YouTuber) given the district's swing nature.
- **IL Senate (D):** Raja Krishnamoorthi reported $12.7M raised, establishing himself as frontrunner in the Democratic primary to replace retiring Dick Durbin.
- **Iowa Senate (R):** Internal D poll showed Josh Turek (D) edging Ashley Hinson (R) — triggered the Sabato downgrade to Lean R.

---

## Sheet Updates

All changes below are included in `constants_patch.json` and will be applied automatically by the Monday cron.

| Tab | Race | Old Value | New Value | Source |
|---|---|---|---|---|
| Constants | NOTES / LAST_UPDATED | stale text; 2026-06-15 | corrected vacancy list; 2026-06-22 | CA-01 removed (Gallagher seated June 10) |
| Senate | IA (Ernst open) | Likely R | **Lean R** | Sabato June 2; Cook; internal poll D advantage |
| Senate | OH Special (Husted) | Lean R | **Toss-up** | Sabato June 11 |
| House | MI-08 (McDonald Rivet) | Lean D | **Likely D** | Inside Elections June 11 |
| House | NC-11 (Edwards) | Likely R | **Lean R** | Inside Elections June 11 |
| House | NJ-07 (Kean) | Toss-up | **Lean D** | Inside Elections Tilt D June 11; trending D |
| House | CA-03 (Kiley) | Party=R | **Party=I**, note updated | Switched to Independent March 2026; still caucuses R |

### No action needed
| Tab | Race | Status |
|---|---|---|
| House | CA-14 | VACANT — runoff Aug 18; successor not yet sworn in |
| House | GA-13 | VACANT — special election July 28; successor not yet sworn in |

---

*Sources: [House Press Gallery Party Breakdown](https://pressgallery.house.gov/member-data/party-breakdown) · [Sabato's Crystal Ball Rating Changes](https://centerforpolitics.org/crystalball/2026-rating-changes/) · [Cook Political Report](https://www.cookpolitical.com/ratings) · [Inside Elections](https://www.insideelections.com/ratings/house) · [Ballotpedia Special Elections](https://ballotpedia.org/Special_elections_to_the_119th_United_States_Congress_(2025-2026)) · [RealClearPolling Generic Ballot](https://www.realclearpolling.com/polls/state-of-the-union/generic-congressional-vote)*
