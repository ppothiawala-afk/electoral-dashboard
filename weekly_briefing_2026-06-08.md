# Electoral Dashboard — Weekly Briefing
**Week of June 8, 2026**

---

## Chamber Balance

No new changes this week. The House balance remains **217 R / 212 D / 1 I / 5 Vacancies**, matching the official Press Gallery count.

The five open seats are: CA-01 (LaMalfa, R, died Jan 6), CA-14 (Swalwell, D, resigned Apr 14), TX-23 (Gonzales, R, resigned Apr 14), FL-20 (Cherfilus-McCormick, D, resigned Apr 21), GA-13 (David Scott, D, died Apr 22). Special elections for CA-01 and CA-14 are scheduled for August 4 and August 18 respectively, with primaries on June 2 (CA-01) and June 16 (CA-14).

Senate remains **53 R / 47 D** (including independents who caucus with each party).

---

## Notable Rating Shifts (Since Last Week)

### Senate
- **Iowa (Ernst open seat) → Lean R** *(was Likely R)*
  Cook Political Report and Sabato's Crystal Ball both moved the open Iowa Senate seat (Ernst retiring) from Likely Republican to Lean Republican, effective June 2. Josh Turek (D) has improved his position in a state Trump carried comfortably, but Republicans remain slight favorites.
  **⚠️ Sheet flag:** The Iowa Senate row currently shows "Likely R" — should be updated to **Lean R**.

- **Texas Senate → Lean R** *(was Likely R)*
  Cook moved Texas from Likely R to Lean R on June 5 following Ken Paxton's runoff victory over Sen. John Cornyn. Paxton's ethical baggage (bribery allegations, impeachment by the R-controlled House, marital scandal) makes him a substantially weaker nominee than Cornyn would have been. Democrat James Talarico holds a fundraising advantage. This is now a genuinely competitive race on the map.
  **⚠️ Sheet flag:** TX Senate row still lists "John Cornyn" as incumbent and notes "Faces primary from AG Paxton & Rep. Hunt." Primary is resolved — Paxton is the Republican nominee. Update incumbent to **Ken Paxton (R nominee)** and revise notes.

### House
- **AL-02 → needs review**
  Mid-cycle redistricting in Alabama (post-court ruling) redraws AL-02 as a heavily Republican district. Cook shifted this from Solid D to Safe Republican; Crystal Ball moved it to Likely Republican. The sheet currently shows AL-02 as **Solid D** (Shomari Figures, D).
  **⚠️ Sheet flag:** AL-02 rating is stale. With redistricting, Figures' district no longer exists as drawn. Recommend updating to reflect the new map or flagging as redistricted.

- **FL-23 (Moskowitz) → Solid D** *(was Likely D)*
  Cook moved FL-23 to Solid D on June 3 following redistricting adjustments. The sheet shows Likely D — can be updated to Solid D.

- **IA-02 (Hinson) → Lean R** *(was Likely R)*
  Crystal Ball moved IA-02 from Likely to Lean Republican, consistent with the worsening Iowa environment for Republicans.
  **⚠️ Sheet flag:** IA-02 currently shows **Likely R** — update to Lean R.

- **NJ-07, PA-10, WA-03** moved to Toss-up by Inside Elections (late May). These are already listed as Toss-up in the sheet — no action needed.

---

## Environment Narrative

The national environment continues to move toward Democrats. The Silver Bulletin generic ballot average now sits at **D+6.6**, the most Democratic it has been all cycle and nearly identical to the D+6.8 reading at this point in the 2018 cycle — when Democrats gained 40 House seats. However, mid-cycle Republican-driven redistricting in Texas, Florida, Alabama, and Louisiana has added several safe Republican seats to the map, partially offsetting the generic ballot tailwind for Democrats. Analysts broadly expect Democrats to be competitive for the House majority but that structural changes make the path narrower than raw polling suggests.

---

## Candidate News

- **Texas Senate:** Ken Paxton defeated incumbent Sen. John Cornyn in the May 26 GOP runoff. Paxton faces Democrat James Talarico in November. Cook immediately shifted the race from Likely R to Lean R. Talarico leads Paxton in early post-runoff polling.

- **NJ-11 primary (June 2):** Analilia Mejia won the Democratic primary rematch against Joe Hathaway, setting up a November rematch of the April special election, which Mejia won by ~20 points. The seat is safely Democratic.

- **GA-14:** Clay Fuller (R) was sworn in following his April 7 runoff victory over Democrat Shawn Harris. Harris underperformed the D+25 special election overperformance trend but it was still the best Democratic performance in a House special under Trump. Fuller fills the seat vacated by MTG.

- **Retirements:** 58 House members (36 R, 24 D) have announced they will not seek re-election — a record pace. No new major retirement announcements confirmed this specific week.

---

## Sheet Flags — Action Required

| Priority | Tab | Race/Row | Issue | Action |
|----------|-----|----------|-------|--------|
| 🔴 High | Senate | Iowa (Ernst) | Rating shows Likely R; both Cook & Crystal Ball now Lean R | Update to **Lean R** |
| 🔴 High | Senate | Texas (Cornyn row) | Incumbent listed as Cornyn, notes reference primary. Primary resolved. | Update incumbent to **Paxton (R nominee)**, update notes |
| 🔴 High | House | AL-02 | Rating shows Solid D; mid-cycle redistricting makes this a safe R seat | Review redistricting impact; likely update to **Likely R or Solid R** |
| 🟡 Medium | House | IA-02 (Hinson) | Rating shows Likely R; Crystal Ball moved to Lean R | Update to **Lean R** |
| 🟡 Medium | House | FL-23 (Moskowitz) | Rating shows Likely D; Cook moved to Solid D | Update to **Solid D** |
| 🟢 Low | Constants | NOTES field | Lists "GA-14" as vacancy; should be "GA-13" (David Scott). GA-14 (Fuller) has been filled. | Correct vacancy list in NOTES |

---

## Cron Job Note

The local `run_weekly_update.sh` script handles automated Google Sheet rating updates at 1pm PST today. Check `update_log.txt` to confirm it ran successfully.

---

*Sources: [House Press Gallery Party Breakdown](https://pressgallery.house.gov/member-data/party-breakdown) · [Cook Political Report](https://www.cookpolitical.com/ratings) · [Sabato's Crystal Ball](https://centerforpolitics.org/crystalball/2026-rating-changes/) · [Inside Elections](https://insideelections.com/ratings/house) · [Silver Bulletin Generic Ballot](https://www.natesilver.net/p/generic-ballot-average-2026-nate-silver-bulletin-congress-polls) · [The Hill / Texas Senate](https://thehill.com/homenews/campaign/5896436-texas-senate-race-rating-shift/)*
