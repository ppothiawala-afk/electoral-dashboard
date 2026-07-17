# Marketing-Ops Pipeline Clones — Planning Doc (v2)

**Status:** Planning only. No build until P-funk says go.
**Date:** 2026-07-16 (v2 — supersedes 2026-07-05 plan; ABM tracker dropped)
**Purpose:** Reuse the Electoral Dashboard architecture (scheduled collection → AI scoring → verification → dashboard) for three marketing-ops portfolio projects — **all three now running on a single shared data pipeline: public state-level media RSS feeds, all 50 states.**

**Build order:** 0) Shared RSS ingestion layer → 1) State Media Coverage Tracker → 2) Competitive Share-of-Voice Monitor → 3) Performance Intelligence Dashboard. **No sentiment scoring anywhere** (decision 2026-07-16): the pipeline captures and classifies coverage — counts, not judgments. Predictive components become possible once months of history accumulate (see Roadmap).

**Portfolio thesis (upgraded):** One verified data pipeline feeding three distinct analytical products. This is a stronger consulting story than three separate clones — it demonstrates that the *expensive* part (reliable ingestion + verification) is built once, and new "products" are just new scoring rubrics and views on top. That's exactly how enterprise marketing-ops platforms are architected. Client translation: swap "state media feeds" for "industry trade press / competitor content / brand mentions" and every one of these becomes a billable engagement (media monitoring, competitive SoV, content intelligence).

---

## Layer 0: Shared RSS ingestion pipeline (build first — everything depends on it)

**One-liner:** Scheduled collection of public state-level media RSS feeds across all 50 states, deduplicated and topic-tagged, feeding all three dashboards.

**Architecture (inherited from Electoral Dashboard):**

| Layer | Electoral Dashboard | RSS pipeline |
|---|---|---|
| Scheduler | GitHub Actions cron (weekly) | Same; ingestion likely daily or 2–3×/week (RSS items expire from feeds), scoring/rollup weekly |
| Collection | `fetch_news.py` + WebSearch | `fetch_feeds.py` + `feedparser`; feed registry in `feeds_config.json` (state → outlets → feed URLs) |
| Pre-filter | — | Keyword/regex relevance filter before AI scoring (cost control; RSS volume ≫ WebSearch volume) |
| AI scoring | Claude scores relevance/sentiment | Classification only, no sentiment: per-item topic tagging (climate / politics / economic development / environmental legislation) + entity extraction. Objective, cheap, verifiable. |
| Validation | `validate_patch.py` + `verify_dashboard.py` | Same pattern; plus feed-health checks (see discovery agent below). **Still the differentiator.** |
| History | `sentiment_history.json` | `media_history.json` — weekly per-state, per-topic snapshots (volume, topic mix, entities) = the lookback feature. History is the product: every week of accumulation makes the dashboard more valuable. |
| Serving | Google Sheet + static HTML | Same; each of the three projects gets its own dashboard reading the shared corpus |

**Feed registry — the real work:**
- Target 3–5 reliable feeds per state; anchor sources: States Newsroom affiliates (~40 states, RSS-friendly), NPR member stations, Stateline, state press-association member lists, AP state wires where available.
- Registry schema per feed: state, outlet name, feed URL, type (nonprofit/public/commercial), status (active/dead/flagged), date added, discovery source.
- Expect churn — outlets kill feeds, paywall, or fold. This is why the discovery agent (below) exists.

**Classification notes (sentiment dropped 2026-07-16):**
- No sentiment scoring. Per-item outputs: topic tags (an item may carry multiple), entities mentioned, state, outlet, date. All countable facts — no judgment calls, so verification can be near-exhaustive.
- Topic definitions still locked in config (what counts as "economic development" vs. "politics") so classification stays consistent across runs.
- Headline + summary sufficient for classification; no full-text fetch needed (respects paywalls and runtime).
- Dedup across feeds (same AP story in 30 outlets) before classification — hash on normalized title + date.

**Volume/cost discipline:** keyword pre-filter → Claude scoring only on survivors; batch scoring; cap per-run item counts; log skip/score ratios in the verification report.

---

## Feed Discovery Agent (recurring, human-in-the-loop)

**One-liner:** A scheduled job that scans for new usable feeds, validates them, and *proposes* registry additions — never auto-adds.

**Honest framing:** in GitHub Actions this is a script with Claude API calls, not a live subagent; in Cowork it can run as a scheduled task where Claude does the scanning interactively. Either way the workflow is:

1. **Discover:** WebSearch for state/local news outlets per state (rotate states each run); crawl known directories (States Newsroom, NPR stations, press associations); RSS autodiscovery on candidate homepages (`<link rel="alternate" type="application/rss+xml">`).
2. **Validate:** fetch candidate feed → parses cleanly, ≥N items in last 30 days, item quality (real articles vs. aggregator spam), topical relevance scored by Claude against the four topics.
3. **Propose:** emit `feeds_patch.json` (same pattern as `constants_patch.json`) with candidates + rationale. P-funk approves; `apply` step merges into registry. No unreviewed feed enters the pipeline — consistent with the existing verification philosophy.
4. **Health-check existing feeds** on the same schedule: flag dead/stale/drifted feeds for removal. Discovery and decay handled by the same job.

**Cadence:** monthly discovery sweep + weekly health check is probably right; decide at build.

**Portfolio value:** "self-maintaining source registry with human approval gate" is a legitimately impressive line for the deck — it answers the #1 objection to media-monitoring pipelines (source rot).

---

## Project 1: State Media Coverage Tracker (replaces ABM tracker)

**One-liner:** All-50-states tracking of state media coverage across four topics — climate, politics, economic development, environmental legislation — classified and counted, visualized with trend lines and a verification layer. Its own dashboard, separate from the Electoral Dashboard.

**Concept mapping:**
- Races → 50 states × 4 topics
- Race ratings → per-state, per-topic coverage volume + week-over-week change
- State News tab → classified article feed (filterable by state/topic)
- Chamber balance → national rollup (coverage volume + topic mix)
- Weekly briefing → "what moved this week" digest (biggest volume swings, emerging story clusters)

**Dashboard components (draft):** national topic-mix overview; state heat map per topic; per-state drilldown (volume trend, top entities, recent items); lookback view — pick any past week and see the coverage landscape as it was (this is the feature that compounds: worthless at week 1, compelling at month 3).

**Verification checks (draft):** every item cites source feed + URL + date; state/topic tags in allowed sets; counts on dashboard reproducible from raw items; no state silently missing from a weekly snapshot (all 50 present or explicitly flagged low-volume); sheet totals match JSON; dedup rate logged.

**Deliverables:** feeds registry, ingestion + scoring scripts, Sheet dashboard (Overview / Article Feed / Trends tabs), weekly briefing generator, verification checks, portfolio write-up.

---

## Project 2: Competitive Share-of-Voice Monitor (same corpus, new lens)

**One-liner:** Share-of-voice analysis over the same RSS corpus — who/what dominates coverage per topic per state, and how narratives shift week to week.

**Concept mapping:** entities = extracted from scored items (politicians, agencies, companies, industries — entity extraction is already in the Layer-0 rubric); SoV = entity share of coverage per topic/state/week; theme classification shows message momentum.

**Open questions for build time:** entity taxonomy — fixed list vs. AI-proposed-then-locked; whether SoV demo focuses on political actors (natural fit to corpus) or industries (closer to client use case). Client translation is direct: same math, entities become brands/competitors.

**Marginal build cost:** low — no new ingestion; new rollup logic + dashboard views.

---

## Project 3: Performance Intelligence Dashboard (same corpus, meta lens)

**One-liner:** Intelligence on the coverage itself — outlet output trends, topic mix shifts, coverage gaps ("which states/topics are under-covered"), narrative velocity (how fast stories propagate across states).

**Note:** this replaces the original GA4/GSC content-performance concept, which needed API credentials and a real property — a dependency now eliminated. If a GA4 demo is still wanted post-midterms for content-engagement clients, it can return as a Project 4; not planned now.

**Concept mapping:** entities = outlets and topics; signals = volume, cadence, topic mix, propagation lag; scoring = trend/anomaly detection with rationale; verification = every claim traceable to counted items.

**Marginal build cost:** low — analytical layer over existing corpus + history.

---

## Roadmap: predictive components (post-history, not designed yet)

Once several months of `media_history.json` exist, the corpus supports forecasting — none of this is built or designed until the data justifies it:
- Coverage-cycle forecasting: predict next-week volume per state/topic from seasonality + momentum (legislative sessions create strong cycles).
- Anomaly detection: flag states/topics deviating from their own baseline ("environmental legislation coverage in Ohio is 3× its trailing average").
- Narrative propagation: given a story cluster appearing in N states, estimate spread to others (needs the Project 3 propagation-lag data).
- Client translation: "predict when your category heats up in the trade press" — a genuinely differentiated pitch, but only credible with real history behind it. Which is the argument for starting Layer 0 quietly and early.

---

## Sequencing & portfolio integration

1. **Now:** planning only (this doc). Separate Cowork project to be created for the build; this doc is self-contained to seed it.
2. **On go:** Layer 0 + feed registry first (this is ~60% of total effort), then Project 1 to demo quality. Earlier start = more accumulated weekly snapshots = stronger demo.
3. **Post-midterms (Nov 5 task):** electoral dashboard portfolio section for parvezpothiawala.com; if Project 1 is live, present as "same verified-pipeline architecture, second domain — and one pipeline feeding three products."
4. Projects 2–3 are views on the shared corpus; each shipped before the next starts, but both benefit from every week of Layer-0 history accumulated in the meantime.

**Quiet-and-separate rule (2026-07-16):** this work must not compete with Electoral Dashboard upkeep before Nov 3. Layer 0 can start early and accumulate history silently; dashboards and portfolio framing wait.

**Framing (applies to all):** "One verified ingestion pipeline, three analytical products — scheduled collection (CI/CD), AI classification with locked definitions, human-gated source discovery, validation layer, executive dashboards, and a predictive roadmap earned by accumulated history." Architecture over subject matter. Counts-not-judgments + verification + source-registry hygiene = the trust story enterprise clients ask about.
