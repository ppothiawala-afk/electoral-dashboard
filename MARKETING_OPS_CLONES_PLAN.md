# Marketing-Ops Pipeline Clones — Planning Doc

**Status:** Planning only. No build until P-funk says go.
**Date:** 2026-07-05
**Purpose:** Reuse the Electoral Dashboard architecture (scheduled collection → AI scoring → verification → dashboard) for three marketing-ops portfolio projects. Build sequentially, ship each to demo quality before starting the next.

**Build order:** 1) ABM Account-Signal Tracker → 2) Competitive Share-of-Voice Monitor → 3) Content-Performance Intelligence Dashboard.

**Portfolio thesis:** Same verified-AI-pipeline architecture, multiple domains. Proves "marketing-ops-transferable infrastructure" rather than asserting it. Pairs with the electoral dashboard case study planned for parvezpothiawala.com post-midterms.

---

## Shared architecture (inherited from Electoral Dashboard)

| Layer | Electoral Dashboard | Reused as |
|---|---|---|
| Scheduler | GitHub Actions cron (weekly) | Same, one workflow per project or matrix job |
| Collection | `fetch_news.py` + WebSearch queries from `news_config.json` | Same pattern; per-project config file defines entities + query templates |
| AI scoring | Claude scores news relevance/sentiment → `news_analysis.json` | Same; per-project scoring rubric in config |
| Patch mechanism | `constants_patch.json` → `apply_constants_patch.py` → Sheet | Same; per-project patch schema |
| Validation | `validate_patch.py` + `verify_dashboard.py` (local + sheet checks) | Same; per-project check definitions. **This is the differentiator — AI + verification.** |
| History | `sentiment_history.json` + `append_sentiment_history.py` | Same; weekly snapshots accumulate = trend lines |
| Serving | Google Sheet + static HTML (index.html, history.html) | Same; new Sheet per project |
| Briefings | `weekly_briefing_*.md` | Same; auto-generated weekly digest per project |

Estimated effort per clone: a fraction of the original build — mostly new config, scoring rubric, sheet layout, and verification checks. No new infrastructure.

---

## Project 1: ABM Account-Signal Tracker (build first)

**One-liner:** Automated account intelligence for a target-account list, refreshed weekly, AI-scored for buying intent, with a verification layer.

**Why first:** Closest 1:1 mapping to the electoral dashboard; most directly sellable ("fixed-scope engagement you could quote tomorrow"); sits inside existing demand gen + marketing ops service pillars.

**Concept mapping:**
- Races → 50–100 named target accounts (fictional ICP — see below)
- Race ratings → intent ratings (Hot / Warm / Cool) with AI rationale
- State News tab → account signal feed
- Chamber balance → pipeline coverage summary (accounts by tier/stage)
- Weekly briefing → "accounts that moved this week" digest

**Signals to collect (public sources only):** funding rounds, executive hires/departures, product launches, layoffs/restructuring, tech-stack changes, expansion/office news, earnings mentions, partnership announcements.

**Scoring rubric (draft):** Each signal scored for (a) relevance to the offering, (b) buying-intent direction (+/-), (c) urgency/recency weight. Account-level rating = weighted rollup with decay on stale signals. Every rating must carry a one-line rationale citing the triggering signal — no unexplained scores (verification checks enforce this).

**Verification checks (draft):** rating values in allowed set; every rating has ≥1 cited signal with date; no signal older than N weeks driving a Hot rating; account list in patch matches config roster exactly (no extra/missing rows — lesson from the extra-column write bug); sheet totals match JSON.

**Demo data:** Fictional-but-realistic ICP list in a niche P-funk consults in (fully demo-able, zero confidentiality risk). Need from P-funk at build time: which niche/vertical, rough ICP profile (size, industry, geography), and the hypothetical offering the intent scoring is anchored to.

**Deliverables:** config file (roster + queries + rubric), Sheet dashboard (Overview / Signal Feed / History tabs), weekly briefing generator, verification checks, portfolio write-up.

---

## Project 2: Competitive Share-of-Voice Monitor (build second)

**One-liner:** Scheduled tracking of competitor content, PR, and reviews; AI-scored messaging themes; trend dashboard.

**Fit:** positioning / GTM strategy engagements.

**Concept mapping:** entities = 5–10 competitors in a chosen category; signals = press releases, blog/content cadence, review-site mentions, campaign launches; scoring = messaging-theme classification + share-of-voice share per theme per week; history layer shows theme momentum over time.

**Open questions for build time:** which category to demo; whether review-site data is fetchable within web-content restrictions; theme taxonomy (fixed vs. AI-proposed then locked).

---

## Project 3: Content-Performance Intelligence Dashboard (build last)

**One-liner:** GA4 / Search Console data in; AI-scored content decay and refresh priorities out.

**Fit:** content-heavy client engagements.

**Why last:** Needs API credentials and a real property. Options: P-funk's own site (parvezpothiawala.com GA4/GSC — smallest but real), a willing client property (anonymized), or a demo property. Decide at build time.

**Concept mapping:** entities = URLs/content pieces; signals = impressions, clicks, position, engagement trends; scoring = decay detection + refresh-priority ranking with rationale; verification = scored URLs must exist in source data, metrics must match API pull.

---

## Sequencing & portfolio integration

1. **Now:** planning only (this doc).
2. **On go:** build Project 1 to demo quality. Note: earlier start = more accumulated weekly snapshots = stronger demo ("a tracker with history beats one born the week you pitch it").
3. **Post-midterms (Nov 5 scheduled task):** electoral dashboard portfolio section for parvezpothiawala.com. If Project 1 is live by then, present both as the same architecture in two domains.
4. Projects 2–3 follow sequentially, each shipped before the next starts.

**Framing (applies to all):** "Automated intelligence pipeline — scheduled data collection (CI/CD), AI-assisted scoring, validation layer, executive dashboard." Architecture over subject matter. AI + verification = the trust story enterprise clients ask about.
