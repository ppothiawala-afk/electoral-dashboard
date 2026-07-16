# Weekly Monday Routine — review the patch & push before 1 PM PT

The scheduled task runs Monday ~5:08 AM and leaves two files in this folder:
`weekly_briefing_YYYY-MM-DD.md` and `constants_patch.json`. Your job before
1 PM PT is to review them and push. Takes ~5 minutes.

## Step 1 — Read the briefing (2 min)

Open the new `weekly_briefing_YYYY-MM-DD.md`. Look for:

- A **⚠️ PIPELINE ALERT** at the top. If present, STOP — don't push. Ask
  Claude to investigate (it means last week's patch never applied or the
  history entry is missing).
- The **Sheet Updates** table at the bottom — this is exactly what the patch
  will change. Spot-check anything surprising by clicking the inline source
  links. If a rating move looks wrong, ask Claude to double-check it before
  pushing.

## Step 2 — Sanity-check the patch (1 min)

```bash
cd ~/Documents/Claude/Projects/Electoral\ Dashboard
python3 validate_patch.py constants_patch.json
```

Expect `✅ constants_patch.json is valid.` (The task already ran this, but
it's cheap insurance.) If it errors, don't push — ask Claude to fix it.

## Step 3 — Pull, then push (1 min)

```bash
git pull
git add -A
git commit -m "Weekly patch and briefing"
git push
```

The `git pull` first grabs last Monday's Actions commit (the archived patch
and updated history) so your push doesn't get rejected.

## Step 4 — Nothing (the machines take over)

At 1 PM PT the GitHub Actions job validates and applies the patch to the
Google Sheet, archives it, and commits the results back. If it fails you'll
see a red run (and an email from GitHub) — the patch stays in place for a
retry, nothing is lost.

The job now ends with a **post-apply verification step**
(`verify_dashboard.py --local --sheet`): it re-reads the Sheet, asserts the
435/100 invariants and rating enums, and confirms the patch actually landed
row-by-row. A red run after "Verify Sheet" means the Sheet doesn't match the
patch — ask Claude to investigate.

## About the Verification section in briefings

Since July 2026 the Monday research task fact-checks itself: it spawns
independent subagent verifiers (ratings moves, chamber membership,
candidate matchups) that get only the claims — not the sources — and
re-research them from scratch. The briefing's **Verification** section shows
the result: all ✅ is normal; any ⚠️ item is something the verifiers
contradicted or couldn't confirm, with the action taken. Give ⚠️ lines your
attention during Step 1.

## Step 5 — State News sentiment (automatic since 2026-07-16)

The **State News** tab reads `news_analysis.json`. As of 2026-07-16 the
Monday scheduled task refreshes it on every run (skill CONTRACT 3.9):
fresh headlines per `news_config.json` race via web search, Claude
rescores sentiment, rewrites `news_analysis.json`, resyncs the On Deck
fallback articles in `index.html`, and runs
`python3 append_sentiment_history.py`. You no longer need to ask — just
make sure `news_analysis.json`, `sentiment_history.json`, and
`index.html` are in your Step 3 push (the briefing's git block will list
them). If the briefing has no State News note or the verifier warns on
L2-freshness, the refresh was skipped — ask Claude to run it.

After a primary resolves (MI Aug 4, KS Aug 4, WI Aug 11, AK Aug 18,
AZ Jul 21, NH Sep 8), ask Claude to also update the candidate lists in
`news_config.json`.

## If you miss a Monday

No harm. The patch just sits unapplied until the next Monday run (or you can
trigger it anytime: GitHub → Actions → Weekly Sheet Apply → Run workflow).
Next week's task will lead its briefing with a pipeline alert reminding you.

## Shortcut

You can also just open Cowork on Monday morning and say:
**"Review this week's electoral patch with me and push it."**
Claude will walk through the briefing, validate, and prep the push commands.
