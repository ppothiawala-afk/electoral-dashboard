# Manual steps — do these yourself, in order

The automated fixes are in place. The following require your credentials / accounts / local
machine and must be done by you. **Order matters** — especially getting `.gitignore` committed
before anything else so the private key never lands on GitHub.

---

## 0. Delete two local cruft files the sandbox could not remove

The sandbox mount blocked `unlink`, so these are still on disk. They are already covered by
`.gitignore` (so they won't be pushed), but remove them locally for tidiness:

```bash
cd ~/Documents/Claude/Projects/Electoral\ Dashboard
rm -f ".~lock.Electoral Dashboard Data.xlsx#"
rm -rf __pycache__
```

---

## 1. Git init + first push (⚠️ .gitignore FIRST)

The folder is not yet a git repo. **Confirm `.gitignore` exists and lists `service_account.json`
before running `git add`** — this is the one step where a mistake leaks the private key.

```bash
cd ~/Documents/Claude/Projects/Electoral\ Dashboard

# 1a. Sanity-check the ignore is working BEFORE adding anything:
git init
git status --ignored | grep service_account.json    # must appear under "Ignored files"

# 1b. Stage everything (the key should NOT be staged):
git add -A
git status | grep service_account.json    # must print NOTHING. If it appears, STOP.

git commit -m "Electoral Dashboard: automation, validator, evals, consolidated skill"

# 1c. Point at the existing GitHub Pages repo and push.
# Use the repo that serves ppothiawala-afk.github.io/electoral-dashboard/.
git branch -M main
git remote add origin git@github.com:ppothiawala-afk/electoral-dashboard.git   # adjust name if different
git push -u origin main
```

If Pages serves from a `gh-pages` branch or a `/docs` folder instead of `main` root, match that
layout when pushing (the important thing is `index.html`, `history.html`, and `history.json`
end up at the served path).

---

## 2. Confirm the key was never previously pushed, then ROTATE it regardless

The live private key in `service_account.json` (`electoral-updater@…`) may have been exposed if
this folder was ever pushed before. Even if not, rotate it now as hygiene — it's cheap.

- Check GitHub → the repo → search history for `service_account.json` or `private_key`. If it
  ever appears in any commit, treat the key as compromised.
- **Rotate in Google Cloud Console:**
  1. IAM & Admin → Service Accounts → `electoral-updater@electoral-dashboard-…`.
  2. **Keys** tab → **Add key → Create new key → JSON** → download.
  3. Replace your local `service_account.json` with the new file.
  4. Delete the **old** key from the same Keys tab so it can no longer authenticate.
- Re-run step 3 below with the new key so Actions uses it.

---

## 3. Add the GOOGLE_CREDENTIALS secret to GitHub

The workflow reads the service account from a base64-encoded secret (no key file in CI).

```bash
cd ~/Documents/Claude/Projects/Electoral\ Dashboard
base64 -i service_account.json | pbcopy      # macOS: base64 now on your clipboard
```

Then in the GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**
- Name: `GOOGLE_CREDENTIALS`
- Value: paste the base64 string.

(Do NOT commit the base64 anywhere — it decodes straight back to the private key.)

---

## 4. Enable Actions and run the workflow once manually

1. Repo → **Actions** tab → enable workflows if prompted.
2. Select **"Weekly Sheet Apply"** → **Run workflow** (`workflow_dispatch`) on `main`.
3. Watch the run. It should:
   - validate the pending `constants_patch.json` (the 2026-06-29 patch),
   - run `update_sheet.py`,
   - run `apply_constants_patch.py`, which applies the 6/29 patch and archives it as
     `constants_patch.applied_<date>.json`,
   - commit the archive + updated `history.json` back to the repo.
4. **Verify** in the Google Sheet that the 6/29 changes landed (TX Senate → Lean R with
   Talarico as challenger; FL-09 → Likely R; FL-14 → Lean R; the MO/TN/TX-09/TX-32/TX-35
   corrections; LAST_UPDATED → 2026-06-29) and that `constants_patch.json` is now gone from the
   repo (archived). If the run shows red, the patch is left in place by design — read the log.

> Note: the 2026-06-29 `history.json` entry has already been added for you (it was missing).
> `history.html` only reflects it once `history.json` is pushed; the Actions commit step keeps
> it in sync going forward.

---

## 5. Copy the consolidated skill into the Claude scheduled-task folder

The sandbox could not write outside the project folder, so the canonical skill for the
scheduled task is staged at `skills/SCHEDULED_TASK_SKILL.md` (correct frontmatter + identical
body to `skills/electoral-dashboard-updater/SKILL.md`). Overwrite the stale copy:

```bash
cp ~/Documents/Claude/Projects/Electoral\ Dashboard/skills/SCHEDULED_TASK_SKILL.md \
   ~/Documents/Claude/Scheduled/electoral-dashboard-updater/SKILL.md
```

This replaces the old version that told Claude to write the Sheet directly via the Drive MCP
(which can't work and contradicts the patch mechanism).

---

## 6. Disable the old Mac cron (and optionally the Claude scheduled task)

GitHub Actions now owns the deterministic apply layer, so the local cron is redundant and was
unreliable anyway (TCC / sleep / silent failures).

```bash
crontab -e
# Delete or comment out the line that runs run_weekly_update.sh, then save.
crontab -l    # confirm it's gone
```

Optionally, in the Claude desktop app, disable or delete the `electoral-dashboard-updater`
**scheduled task** — the research step is now human-in-the-loop (you trigger the skill in
Cowork when you want the briefing). Keep the skill itself; just drop the schedule.

---

## Done checklist

- [ ] `.gitignore` committed; `service_account.json` confirmed NOT in git.
- [ ] Repo pushed; Pages serving `index.html` / `history.html` / `history.json`.
- [ ] Key rotated; old key deleted in GCP.
- [ ] `GOOGLE_CREDENTIALS` secret added.
- [ ] Workflow run once via dispatch; 6/29 patch applied & archived; Sheet verified.
- [ ] Scheduled-task `SKILL.md` overwritten with the canonical version.
- [ ] Mac cron disabled; Claude scheduled task disabled (optional).
- [ ] Local `.~lock…` and `__pycache__` deleted.
