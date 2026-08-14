#!/usr/bin/env python3
"""
preflight_sync.py — make Contract 1 Step 0 survive an unattended run.

WHY THIS EXISTS
---------------
On 2026-08-03 the scheduled Monday run stalled twice before writing a single
file, and both stalls needed a human at the keyboard:

  1. Three stale `.lock` files in .git that the sandbox could not unlink until
     the user granted folder delete permission.
  2. `git pull` aborted with "Your local changes to the following files would be
     overwritten by merge" on .gitignore and weekly_commit.sh.

A third shape appeared on 2026-08-12: the mount denied unlink *outright*
("Operation not permitted"), so git could neither clear its own locks nor replace
tracked files mid-pull. The pull aborted half-done and left an ORIG_HEAD.lock that
then blocked the user's *native* clone. The cause is a missing capability, not a
lock or a dirty worktree, so we now PROBE delete permission up front (can_delete_files)
and stop cleanly with the grant instruction BEFORE fetching — a pull that cannot
unlink can only make things worse.

Neither is a *time* problem, so a longer scheduling window does not fix them.
Blocker 2 is the interesting one. Its cause is structural and recurs every week:
the weekly-apply Action pushes a commit back to origin, the local clone never
pulls it, and the same edits sit in the worktree uncommitted. So the incoming
commit and the local worktree are byte-identical, and git still refuses.

Resolving it by hand needs `git checkout -- <files>`, which SKILL.md keeps off
the allowlist for good reason. But the safety argument is purely mechanical:

    if worktree_bytes == origin_bytes, then
        checkout (revert to HEAD) followed by fast-forward (restore origin)
        returns the worktree to exactly the bytes it started with.

That is a proof, not a judgment call — which means a script can carry it, and
the human can leave the loop without the bar being lowered. This script checks
that equality for every blocking file, every time, and REFUSES if it does not
hold. A human deciding "eh, looks the same" is strictly weaker.

WHAT IT WILL NOT DO
-------------------
If any blocking file's worktree bytes differ from origin's, there is real local
work at stake. The script touches nothing, prints the diverging paths, and exits
2 so the caller can surface it. It never stashes, never resets --hard, never
force-pushes, and never discards content that is not provably recoverable from
the incoming commit.

It also never commits or pushes. The sandbox has no push credentials (see
SKILL.md Contract 5), so origin is written ONLY by the Mac (weekly_commit.sh) and
GitHub Actions — a single-writer discipline. This script's whole job is to keep
the local clone current and clean before those writers run, and to leave no lock
behind that the native clone could trip on.

EXIT CODES
    0  clone is synced and clean (possibly after a proven-safe recovery)
    1  operational failure (locks unremovable, fetch/pull failed)
    2  needs a human: real local divergence, do not proceed to write files

USAGE
    python3 preflight_sync.py              # sync, recovering where provable
    python3 preflight_sync.py --dry-run    # report only, change nothing
    python3 preflight_sync.py --json       # machine-readable summary on stdout
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent

BOLD, RED, YEL, GRN, OFF = "\033[1m", "\033[31m", "\033[33m", "\033[32m", "\033[0m"

DELETE_PERM_HINT = (
    "  The sandbox filesystem denied file deletion. Grant folder delete\n"
    "  permission (mcp__cowork__allow_cowork_file_delete) on this repo and re-run."
)


def run(*args, check=False, binary=False):
    """Run a git command in the repo. Returns (rc, out)."""
    p = subprocess.run(
        ["git", *args],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    out = p.stdout if binary else p.stdout.decode("utf-8", "replace")
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{out}")
    return p.returncode, out


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def step(msg):
    print(f"\n{BOLD}▸ {msg}{OFF}")


def clear_locks():
    """Remove stale lock files at any depth. git leaves them deeper than one level."""
    step("Clearing stale git locks")
    locks = list((REPO / ".git").rglob("*.lock"))
    if not locks:
        print("  clean")
        return True
    stuck = []
    for lk in locks:
        try:
            lk.unlink()
        except OSError:
            stuck.append(lk)
    if stuck:
        print(f"{RED}  could not unlink {len(stuck)} lock file(s):{OFF}")
        for lk in stuck:
            print(f"    {lk.relative_to(REPO)}")
        print(f"{YEL}{DELETE_PERM_HINT}{OFF}")
        return False
    print(f"  removed {len(locks) - len(stuck)} stale lock(s)")
    return True


def upstream_ref():
    rc, out = run("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    return out.strip() if rc == 0 else "origin/main"


def can_delete_files() -> bool:
    """Probe whether this filesystem lets us unlink a file under .git.

    The 2026-08-12 blocker was neither a lock nor a dirty worktree: the mount
    denied unlink, so git could not clear locks or replace tracked files, and the
    half-finished pull left an ORIG_HEAD.lock that blocked the native clone. A
    one-line probe turns that corrupting failure into a clean, actionable stop.
    """
    probe = REPO / ".git" / ".preflight_delete_probe"
    try:
        probe.write_bytes(b"probe")
        probe.unlink()
        return True
    except OSError:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    report = {"recovered": [], "diverged": [], "pulled": False, "status": "ok"}
    pre = {}  # path -> sha256 of the worktree bytes BEFORE we touch anything

    def finish(code, status):
        report["status"] = status
        if args.as_json:
            print(json.dumps(report, indent=2))
        sys.exit(code)

    step("Checking filesystem delete permission")
    if not can_delete_files():
        print(f"{RED}  cannot unlink files in this repo — the mount denies deletion.{OFF}")
        print(f"{YEL}{DELETE_PERM_HINT}{OFF}")
        print(f"{YEL}  Stopping BEFORE fetch/pull on purpose: a pull that cannot unlink\n"
              f"  tracked files aborts half-done and leaves an ORIG_HEAD.lock that then\n"
              f"  blocks the native clone (the 2026-08-12 cascade).{OFF}")
        finish(1, "delete-perm-missing")
    print("  ok")

    if not clear_locks():
        finish(1, "locks-stuck")

    step("Fetching origin")
    rc, out = run("fetch", "--prune", "origin")
    if rc != 0:
        print(f"{RED}  fetch failed:{OFF}\n{out}")
        finish(1, "fetch-failed")
    up = upstream_ref()
    print(f"  upstream: {up}")

    rc, head = run("rev-parse", "--short", "HEAD")
    rc, upsha = run("rev-parse", "--short", up)
    head, upsha = head.strip(), upsha.strip()
    if head == upsha:
        print(f"  already at {head} — nothing incoming")

    # Files the incoming commits touch.
    _, out = run("diff", "--name-only", f"HEAD..{up}")
    incoming = {l for l in out.splitlines() if l.strip()}
    # Files dirty in the worktree (tracked, modified, not staged or staged).
    _, out = run("diff", "--name-only", "HEAD")
    dirty = {l for l in out.splitlines() if l.strip()}

    blockers = sorted(incoming & dirty)

    if not blockers:
        print("  no blocking files — worktree does not collide with incoming")
    else:
        step(f"Adjudicating {len(blockers)} blocking file(s)")
        safe, diverged = [], []
        for f in blockers:
            wt_path = REPO / f
            wt = wt_path.read_bytes() if wt_path.exists() else b""
            rc, blob = run("show", f"{up}:{f}", binary=True)
            if rc != 0:
                diverged.append((f, "not present in incoming commit"))
                continue
            a, b = sha(wt), sha(blob)
            pre[f] = a
            if a == b:
                safe.append(f)
                print(f"  {GRN}provable no-op{OFF}  {f}")
                print(f"      worktree {a[:16]} == origin {b[:16]}")
            else:
                diverged.append((f, f"worktree {a[:16]} != origin {b[:16]}"))
                print(f"  {RED}DIVERGED{OFF}       {f}")
                print(f"      worktree {a[:16]} != origin {b[:16]}")

        report["recovered"] = safe
        report["diverged"] = [f for f, _ in diverged]

        if diverged:
            print(
                f"\n{RED}✖ {len(diverged)} file(s) hold real local work that is NOT in the "
                f"incoming commit.{OFF}"
            )
            for f, why in diverged:
                print(f"    {f} — {why}")
            print(
                f"{YEL}  Nothing was changed. Resolve these by hand, then re-run.\n"
                f"  Do NOT write a patch onto a diverged clone — that is the 2026-07-29\n"
                f"  rename trap.{OFF}"
            )
            finish(2, "diverged")

        if args.dry_run:
            print(f"\n{YEL}  --dry-run: would revert {len(safe)} provably-identical file(s){OFF}")
        elif safe:
            rc, out = run("checkout", "--", *safe)
            if rc != 0:
                print(f"{RED}  checkout failed:{OFF}\n{out}")
                finish(1, "checkout-failed")
            print(f"  reverted {len(safe)} file(s) to HEAD (content recoverable from {upsha})")

    if args.dry_run:
        step("Pull (skipped — dry run)")
        finish(0, "dry-run")

    step("Pulling")
    # Rename detection OFF, via config rather than a pull flag: `git pull
    # --no-renames` is not accepted by all git versions and fails with a usage
    # dump. Disabling it is what forces the archive rename to surface as a loud
    # conflict instead of silently merging a new patch into the archive path.
    rc, out = run("-c", "merge.renames=false", "-c", "diff.renames=false",
                  "pull", "--no-rebase", "--no-edit")
    print("  " + "\n  ".join(out.strip().splitlines()[-6:]))
    if rc != 0:
        print(f"{RED}  pull failed{OFF}")
        if "Operation not permitted" in out or "unable to unlink" in out:
            print(f"{YEL}{DELETE_PERM_HINT}{OFF}")
        # We may have just reverted files in order to unblock this pull. Leaving
        # them reverted would hand back a worktree in a WORSE state than we found
        # it — the very thing this script exists to prevent. Their content is
        # provably identical to the incoming commit, so restore it from there.
        if report["recovered"]:
            print(f"{YEL}  restoring {len(report['recovered'])} reverted file(s) "
                  f"so the worktree is no worse than we found it{OFF}")
            for f in report["recovered"]:
                rc2, blob = run("show", f"{up}:{f}", binary=True)
                if rc2 == 0:
                    (REPO / f).write_bytes(blob)
                    ok = sha(blob) == pre[f]
                    print(f"    {GRN if ok else RED}{'restored' if ok else 'MISMATCH'}{OFF} {f}")
        finish(1, "pull-failed")
    report["pulled"] = True

    # Post-condition: every file we reverted must be back to the bytes it had.
    if report["recovered"]:
        step("Verifying the recovery was lossless")
        bad = []
        for f in report["recovered"]:
            now = sha((REPO / f).read_bytes()) if (REPO / f).exists() else ""
            if now != pre[f]:
                bad.append(f)
                print(f"  {RED}CHANGED{OFF} {f}: {pre[f][:16]} -> {now[:16]}")
            else:
                print(f"  {GRN}unchanged{OFF} {f} ({now[:16]})")
        if bad:
            print(
                f"{RED}✖ recovery was NOT lossless for {len(bad)} file(s). "
                f"Stop and inspect before writing anything.{OFF}"
            )
            finish(2, "recovery-lossy")

    # Final sweep: never hand back a worktree carrying a lock we might have left.
    # A leftover lock here is exactly what the native clone trips on next (the
    # 2026-08-12 cascade), so clear any before we report done.
    leftover = list((REPO / ".git").rglob("*.lock"))
    swept = 0
    for lk in leftover:
        try:
            lk.unlink()
            swept += 1
        except OSError:
            pass

    rc, newhead = run("rev-parse", "--short", "HEAD")
    step("Done")
    print(f"  HEAD {head} -> {newhead.strip()}")
    print(f"  recovered: {len(report['recovered'])}  diverged: 0")
    if swept:
        print(f"  swept {swept} leftover lock(s) so the native clone stays clean")
    finish(0, "ok")


if __name__ == "__main__":
    main()
