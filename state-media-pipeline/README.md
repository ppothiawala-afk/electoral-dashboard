# State-Media RSS Pipeline — Layer 0 + Project 1

A verified, scheduled ingestion pipeline over public **state-level media RSS
feeds across all 50 states**, plus the **State Media Coverage Tracker**
dashboard (Project 1) on top of it. Built to mirror the Electoral Dashboard
architecture: *scheduled collection → keyword pre-filter → AI classification
with locked definitions → verification layer → static dashboard → accumulating
history.*

> **Counts, not judgments.** This pipeline classifies and **counts** coverage.
> There is **no sentiment analysis anywhere** — a deliberate design decision.
> Per-item outputs are countable facts only: topic tags, entities mentioned,
> state, outlet, feed URL, item URL, and publish date. Because every output is
> a fact, verification can be near-exhaustive (see `verify_pipeline.py`).

---

## Architecture

```
feeds_config.json  ──►  fetch_feeds.py   ──►  items_raw.json
 (50-state registry)     feedparser, dedup      (deduped items, no tags)
                                                   │
topics_config.json  ──►  classify.py      ──►  items_classified.json
 (locked topics +         keyword prefilter        (topics + entities;
  keyword prefilter)      → API or --offline         NO sentiment)
                                                   │
                          append_media_history.py ──► media_history.json
                           (weekly per-state/topic       (the lookback product;
                            volume + top entities)         append-only history)
                                                   │
                          verify_pipeline.py  ──►  verification_report.json
                           (provenance, allowed tags, reproducible counts,
                            50-state presence, dedup rate, no-sentiment guard)
                                                   │
                          dashboard.html  ◄── reads media_history.json
                           (national mix, heat map,     + items_classified.json
                            per-state drilldown, week-picker lookback)

discover_feeds.py ──► feeds_patch.json ──► apply_feeds_patch.py ──► feeds_config.json
 (validate candidates,   (PROPOSALS ONLY,     (human-approved merge +
  health-check registry)   human review gate)   audit copy)
```

### Files

| File | Role |
|---|---|
| `feeds_config.json` | 50-state feed registry (outlet, feed_url, type, status, validation) |
| `topics_config.json` | **Locked** topic definitions + keyword pre-filter lists + entity hints |
| `fetch_feeds.py` | feedparser collection; normalize; dedup; `--fixtures` offline mode |
| `classify.py` | keyword pre-filter → API **or** `--offline` topic tags + entities |
| `append_media_history.py` | weekly per-state/per-topic volume + top-entity snapshot |
| `verify_pipeline.py` | deterministic verification; writes `verification_report.json` |
| `discover_feeds.py` | feed discovery + health-check; emits `feeds_patch.json` (proposals) |
| `apply_feeds_patch.py` | merges a human-approved patch; writes an audit copy |
| `dashboard.html` | single-file static dashboard (Chart.js via cdnjs) |
| `run_weekly.sh` | one weekly pass: fetch → classify → snapshot → verify |
| `github-workflow-media.yml` | CI workflow template (**not** auto-activated — see below) |
| `fixtures/` | saved feed XML for no-network testing |

---

## Quick start (offline demo — no API key, no network)

```bash
cd state-media-pipeline
pip install -r requirements.txt

# full offline pass against saved fixtures:
FIXTURES=fixtures/ PIPELINE_OFFLINE=1 ./run_weekly.sh

# then serve the dashboard (fetch() needs HTTP, not file://):
python3 -m http.server 8000
# open http://localhost:8000/dashboard.html
```

## Live run (real feeds + API classification)

```bash
export ANTHROPIC_API_KEY=sk-...
./run_weekly.sh            # live fetch, batched Haiku classification
# or force keyword-only classification even with a key:
PIPELINE_OFFLINE=1 ./run_weekly.sh
```

`classify.py` always runs the **keyword pre-filter first** and only sends
survivors to the API in batches (with a `--max-api-items` hard cap), so API
cost is bounded. `--offline` skips the API entirely and tags from the keyword
lists alone. Skip/score ratios are logged every run.

---

## The feed registry

- **Backbone:** the **States Newsroom** nonprofit network — 39 state affiliates
  (e.g. Colorado Newsline, Ohio Capital Journal, Michigan Advance) plus 11
  partner nonprofits (CalMatters, CT Mirror, Honolulu Civil Beat, Mississippi
  Today, New York Focus, Texas Tribune, VTDigger, WyoFile). Together these
  cover **all 50 states**. All are WordPress sites using the standard `/feed/`
  endpoint. A national **Stateline** feed (`state: "US"`) is included as a
  cross-state source.
- **Validation:** every feed carries a `validation` block. Feeds marked
  `validated: true` were confirmed live (content-type `application/rss+xml`) on
  the `added` date; the rest are pattern-derived from the official affiliate
  roster and are re-checked live by `discover_feeds.py --health-check` at
  runtime. No feed URL was invented — every outlet appears in the States
  Newsroom roster.
- **Growth:** the registry currently carries ~1 vetted primary feed per state.
  Expanding to the 2–5-per-state target (NPR member stations, additional
  nonprofits) is exactly what the **human-gated discovery agent** is for:
  `discover_feeds.py` proposes, a human approves, `apply_feeds_patch.py` merges.

### Feed discovery + health check (human-in-the-loop)

```bash
# propose additions from a candidate list (validated before proposing):
python3 discover_feeds.py --candidates candidates.json

# flag dead/stale feeds already in the registry:
python3 discover_feeds.py --health-check

# review feeds_patch.json, then:
python3 apply_feeds_patch.py --dry-run   # preview
python3 apply_feeds_patch.py             # merge + write audit copy
```

Nothing is ever auto-added or auto-removed. This mirrors the Electoral
Dashboard's `constants_patch` review gate.

---

## Verification

`verify_pipeline.py` runs the plan-doc checks and exits non-zero on any FAIL:

- **V1** all 50 states covered by ≥1 feed
- **V2** every item cites feed URL + item URL + publish date
- **V3** every topic tag is in the locked allowed set
- **V4** dashboard counts reproduce **exactly** by recomputing from the raw items
- **V5** all 50 states present in the latest snapshot, or explicitly flagged `low_volume`
- **V6** dedup rate logged
- **V7** **no-sentiment guard** — fails if any `sentiment`/`score`/`rating`/etc. key appears on an item
- **V8** history snapshots chronologically ordered

---

## CI / scheduling

`github-workflow-media.yml` is a ready-to-use GitHub Actions template. It is
**intentionally not placed in `.github/workflows/`** — activate it manually when
you're ready:

1. Copy it to `.github/workflows/media-pipeline.yml`.
2. Add the `ANTHROPIC_API_KEY` repo secret.
3. (Optional) enable the commit step to persist weekly snapshots.

Ingestion can run more often than scoring (RSS items expire from feeds); the
template runs the whole pass weekly and can be dialed to 2–3×/week.

---

## Deliberate exclusions & deferrals

- **Sentiment analysis is intentionally excluded** (decision 2026-07-16). The
  product is coverage *counts and classification*, not judgments. This is what
  makes near-exhaustive verification possible and is the core trust story.
- **Predictive layer is deferred.** Coverage-cycle forecasting, anomaly
  detection, and narrative-propagation modeling become credible only once
  months of `media_history.json` have accumulated. History is the product:
  worthless at week 1, compelling at month 3. Nothing predictive is built yet —
  by design.
- **Projects 2 (Share-of-Voice) and 3 (Performance Intelligence)** are
  additional *views* on this same corpus; the expensive part (reliable,
  verified ingestion) is built once here.

## Testing notes

The end-to-end test runs entirely offline against `fixtures/` (real outlet
metadata; representative WordPress-RSS item structure), because the build
sandbox blocks outbound HTTP and the fetch tool returns XML bodies as opaque
binary. The `fixtures/` files therefore model the real feeds' structure rather
than being byte-for-byte captures; the live scripts use `feedparser` over the
network in CI. The `2026-07-10` history snapshot is a **synthetic seed** (scaled
from the first real run) so the lookback/trend UI is demonstrable at week 1 —
it is replaced by real snapshots as weeks accumulate.
