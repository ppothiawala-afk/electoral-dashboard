#!/usr/bin/env bash
#
# weekly_commit.sh — gated commit+push for the weekly research run.
#
# Since 2026-07-29 this is run by Claude at the end of the Monday cycle, not
# pasted by hand. It replaces the hand-written git block that failed three ways
# at once that day: zsh parsing "#" comments as arguments, an apostrophe opening
# a quote> continuation, and a silent rename-merge that deleted the pending
# patch while every surface signal reported success.
#
# It refuses to push anything that would break Monday:
#   1. clears stale git locks (they recur in this repo)
#   2. validates the pending patch + runs the full local verifier
#   3. asserts patch-file integrity BEFORE committing
#   4. stages an explicit allowlist — never `git add -A`
#   5. pulls with rename detection OFF, so the archive rename can only ever
#      produce a loud conflict, never a silent content merge
#   6. re-asserts integrity AFTER the merge and ABORTS before pushing if the
#      merge damaged anything
#
# UNATTENDED SAFETY: on any failure after the commit, the repo is rewound to a
# clean, non-conflicted state with the local commit intact and unpushed. It will
# never be left mid-merge for the user to discover later.
#
# Usage:
#   ./weekly_commit.sh "Weekly 2026-08-03: ..."   # commit + push
#   ./weekly_commit.sh --dry-run                  # run all gates, change nothing
#
set -uo pipefail
cd "$(dirname "$0")" || exit 1

DRY_RUN=0
MSG=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    *) MSG="$arg" ;;
  esac
done
[ -z "$MSG" ] && MSG="Weekly $(date +%F): research run"

step()  { printf '\n\033[1m▸ %s\033[0m\n' "$1"; }
die()   { printf '\n\033[31m✖ %s\033[0m\n' "$1" >&2; exit 1; }

# Identity. On the Mac a global identity exists and is used unchanged. From the
# Cowork sandbox there is none, and a merge commit fails just as hard as a
# regular one — so this is exported for the whole process rather than passed per
# command. Nothing is written to .git/config. The email is the account owner's,
# so GitHub still attributes the commit to their account.
if ! git config user.email >/dev/null 2>&1; then
  export GIT_AUTHOR_NAME="cowork-weekly-bot"
  export GIT_AUTHOR_EMAIL="ppothiawala@gmail.com"
  export GIT_COMMITTER_NAME="cowork-weekly-bot"
  export GIT_COMMITTER_EMAIL="ppothiawala@gmail.com"
fi

# Rewind to a clean state, preserving the local commit, then fail.
#
# NEVER `reset --hard` here. On 2026-07-29 this function used it and silently
# destroyed uncommitted edits to weekly-apply.yml, MANUAL_STEPS.md and
# requirements.txt — the Ghost integration work, which is deliberately kept
# uncommitted and is therefore invisible to every other safety net in this
# script. `merge --abort` preserves unstaged changes; `reset --keep` refuses to
# run at all rather than discarding them. If neither can rewind safely, leave
# the repo alone and say so — a human untangling a merge is strictly better than
# a script eating their work.
rewind_and_die() {
  local rewound="repo left as-is (could not rewind safely)"
  if git rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
    git merge --abort 2>/dev/null && rewound="merge aborted; working tree restored"
  elif git rev-parse -q --verify ORIG_HEAD >/dev/null 2>&1; then
    git reset --keep ORIG_HEAD 2>/dev/null && rewound="rewound to pre-merge state"
  fi
  printf '\n\033[31m✖ %s\033[0m\n' "$1" >&2
  printf '\033[33m  %s. Your local commit is intact and NOT pushed.\n' "$rewound" >&2
  printf '  Nothing reached origin. Uncommitted work was not touched.\033[0m\n' >&2
  exit 1
}

# ── 1. stale locks ───────────────────────────────────────────────────────────
step "Clearing stale git locks"
# NOT -maxdepth 1: git also leaves objects/maintenance.lock and
# refs/heads/*.lock, both deeper than one level.
find .git -name '*.lock' -delete 2>/dev/null
remaining=$(find .git -name '*.lock' 2>/dev/null | wc -l | tr -d ' ')
if [ "$remaining" != "0" ]; then
  find .git -name '*.lock' 2>/dev/null >&2
  die "could not remove $remaining git lock file(s) — the filesystem denied unlink. Delete them manually and re-run."
fi
echo "  clean"

# ── 2. pre-flight validation ─────────────────────────────────────────────────
# A pending patch is the normal state, but not the only legitimate one: if the
# apply job ran mid-cycle (manual dispatch, or a re-run) the patch is already
# archived and gone. That is fine — but ONLY if some archive carries this
# cycle's date. Tying it to the newest weekly briefing is what separates
# "applied" from "lost": a patch that vanished without being applied leaves no
# archive bearing that date.
PRE_ARGS=()
if [ -f constants_patch.json ]; then
  step "Validating pending patch"
  python3 validate_patch.py constants_patch.json \
    || die "patch validation failed — fix the patch before committing"
else
  step "No pending patch — verifying this cycle's patch was applied, not lost"
  NEWEST_BRIEF=$(ls -1 weekly_briefing_*.md 2>/dev/null | sort | tail -1 \
                 | sed 's/.*weekly_briefing_\(.*\)\.md/\1/')
  [ -z "$NEWEST_BRIEF" ] && die "no pending patch and no weekly briefing to reconcile against"
  echo "  newest briefing: $NEWEST_BRIEF"
  PRE_ARGS=(--consumed-ok "$NEWEST_BRIEF")
fi

step "Running local verifier"
python3 verify_dashboard.py --local \
  || die "verifier reported FAILURES — resolve them before committing"

step "Asserting patch-file integrity (pre-commit)"
python3 check_patch_integrity.py "${PRE_ARGS[@]}" \
  || die "patch files are already damaged — repair before committing"

# ── 3. stage an explicit allowlist ───────────────────────────────────────────
# Deliberately excludes .github/workflows/*, publish_to_ghost.py,
# WEBSITE_PLAN.md, MANUAL_STEPS.md and requirements.txt: the Ghost integration
# is intentionally uncommitted until its secrets exist, and committing the
# workflow without the script would break the Monday job.
# verification_report.json is gitignored and would error if named.
step "Staging weekly files"
for p in \
  constants_patch.json \
  'constants_patch.applied_*.json' \
  history.json \
  corrections.json \
  election_calendar.json \
  news_config.json \
  news_analysis.json \
  sentiment_history.json \
  index.html \
  'weekly_briefing_*.md' \
  check_patch_integrity.py \
  verify_dashboard.py \
  validate_patch.py \
  weekly_commit.sh \
  skills/electoral-dashboard-updater/SKILL.md
do
  git add -A -- $p 2>/dev/null || true
done
git --no-pager diff --cached --stat || true

# Nothing to stage is not the same as nothing to do: Claude can commit from the
# Cowork sandbox but cannot push (no GitHub credentials there), so this script
# is often re-run later purely to ship commits that already exist.
SKIP_COMMIT=0
if git diff --cached --quiet; then
  UNPUSHED=$(git rev-list --count '@{u}..HEAD' 2>/dev/null || echo 0)
  if [ "$UNPUSHED" = "0" ]; then
    echo "  nothing staged and nothing unpushed — already up to date"
    exit 0
  fi
  echo "  nothing new to stage, but $UNPUSHED unpushed commit(s) — will sync and push those"
  SKIP_COMMIT=1
fi

if [ "$DRY_RUN" -eq 1 ]; then
  step "DRY RUN — all gates passed, nothing committed or pushed"
  git reset -q
  exit 0
fi

# ── 4. commit ────────────────────────────────────────────────────────────────
if [ "$SKIP_COMMIT" -eq 0 ]; then
  step "Committing"
  git commit -m "$MSG" || die "commit failed"
else
  step "Skipping commit (shipping existing unpushed commits)"
fi

# Remember the pending patch's LAST_UPDATED before syncing. If the apply job ran
# while this cycle was in progress, the merge will legitimately remove the
# pending patch and add its archive — which must NOT be mistaken for the rename
# trap, whose signature is identical apart from where the content ends up.
PENDING_LU=""
if [ -f constants_patch.json ]; then
  PENDING_LU=$(python3 -c "import json;print(json.load(open('constants_patch.json'))['updates']['LAST_UPDATED'])" 2>/dev/null || echo "")
fi

# ── 5. rename-safe pull ──────────────────────────────────────────────────────
# merge.renames=false is the whole point: with rename detection ON, git merges a
# new constants_patch.json INTO constants_patch.applied_*.json with no conflict.
# With it OFF, the same situation surfaces as a modify/delete conflict.
step "Syncing with origin (rename detection disabled)"
if ! git -c merge.renames=false pull --no-rebase --no-edit; then
  rewind_and_die "pull hit a conflict. If it named constants_patch.json as deleted upstream and modified locally, that is the archive rename: re-run Contract 1 Step 0 first, or resolve with 'git add constants_patch.json && git commit --no-edit' then re-run this script."
fi

# ── 6. post-merge integrity gate ─────────────────────────────────────────────
step "Re-asserting patch-file integrity (post-merge)"
POST_ARGS=()
[ -n "$PENDING_LU" ] && POST_ARGS=(--consumed-ok "$PENDING_LU")
python3 check_patch_integrity.py "${POST_ARGS[@]}" \
  || rewind_and_die "the merge damaged the patch files (see RECOVERY above). ABORTED BEFORE PUSH."

# ── 7. push, with one retry if origin moved underneath us ────────────────────
step "Pushing"
if ! git push; then
  echo "  push rejected — origin moved; syncing once and retrying"
  git -c merge.renames=false pull --no-rebase --no-edit \
    || rewind_and_die "retry pull conflicted"
  python3 check_patch_integrity.py "${POST_ARGS[@]}" \
    || rewind_and_die "retry merge damaged the patch files. ABORTED BEFORE PUSH."
  git push || die "push failed twice — origin may be protected or the network is down"
fi

# ── 8. confirm ───────────────────────────────────────────────────────────────
step "Done"
python3 -c "import json;print('  pending patch LAST_UPDATED:', json.load(open('constants_patch.json'))['updates']['LAST_UPDATED'])"
echo "  pushed: $(git rev-parse --short HEAD)"
echo "  Monday's apply job will pick this up."
