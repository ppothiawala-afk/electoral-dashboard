#!/usr/bin/env bash
# run_weekly.sh — one weekly pass of the state-media pipeline.
#
# Order matters: collect -> classify -> snapshot -> verify. Verify exits
# non-zero on any FAIL, which reds the CI run.
#
# Env:
#   ANTHROPIC_API_KEY   required for live API classification; omit to use --offline
#   PIPELINE_OFFLINE=1  force keyword-only classification (no API)
#   FIXTURES=fixtures/  run the whole pass against saved XML (no network)
#
# Usage:
#   ./run_weekly.sh                 # live fetch + API classify (needs key)
#   PIPELINE_OFFLINE=1 ./run_weekly.sh
#   FIXTURES=fixtures/ PIPELINE_OFFLINE=1 ./run_weekly.sh   # full offline demo
set -euo pipefail
cd "$(dirname "$0")"

FETCH_ARGS=""
if [[ -n "${FIXTURES:-}" ]]; then
  FETCH_ARGS="--fixtures ${FIXTURES}"
  echo ">> offline fixture mode: ${FIXTURES}"
fi

echo ">> [1/4] fetch_feeds"
python3 fetch_feeds.py ${FETCH_ARGS}

echo ">> [2/4] classify"
if [[ -n "${PIPELINE_OFFLINE:-}" || -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "   (offline keyword classification)"
  python3 classify.py --offline
else
  python3 classify.py
fi

echo ">> [3/4] append_media_history"
python3 append_media_history.py

echo ">> [4/4] verify_pipeline"
python3 verify_pipeline.py

echo ">> done. Outputs: items_raw.json, items_classified.json, media_history.json, verification_report.json"
