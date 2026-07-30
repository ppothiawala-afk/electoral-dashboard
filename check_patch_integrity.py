#!/usr/bin/env python3
"""
check_patch_integrity.py — guard against the constants_patch rename trap.

WHY THIS EXISTS (incident 2026-07-29)
-------------------------------------
The Monday apply job archives the pending patch by *renaming* it:
    constants_patch.json -> constants_patch.applied_YYYY-MM-DD.json
and pushes that commit back. If a NEW constants_patch.json is committed locally
while the clone is still behind origin, the subsequent `git pull` detects a
100%-similarity rename and merges the new content *into the archive path* —
with no conflict and a harmless-looking diffstat. The result is:

  * no pending constants_patch.json  -> Monday applies nothing, silently
  * an archive holding the WRONG week's content -> audit trail corrupted

Neither validate_patch.py nor verify_dashboard.py --local catches this: L7
treats "no pending patch" as "nothing to validate" and passes green.

WHAT IT CHECKS
--------------
1. A pending constants_patch.json exists and parses (unless --no-pending-ok).
2. No archive's LAST_UPDATED is *later* than its own filename date.
   Later  = new content merged into an old archive = the rename trap.
   Earlier = normal. Archives are named for the date the patch was APPLIED,
   while LAST_UPDATED is the date the research was WRITTEN, so e.g. the
   2026-07-15 archive legitimately reads 2026-07-14.

Exit 0 = clean, exit 1 = problem (with recovery instructions printed).
"""

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-pending-ok", action="store_true",
                    help="do not require a pending constants_patch.json "
                         "(use post-apply, when the patch has been archived)")
    ap.add_argument("--consumed-ok", metavar="LAST_UPDATED",
                    help="post-merge use: the pending patch may be absent, but ONLY if some "
                         "archive now carries this LAST_UPDATED value — i.e. the apply job "
                         "legitimately consumed it. Distinguishes a real apply from the "
                         "rename trap, which also makes the pending patch disappear.")
    args = ap.parse_args()

    problems, notes = [], []

    def archive_with(last_updated):
        for f in sorted(HERE.glob("constants_patch.applied_*.json")):
            try:
                if json.loads(f.read_text()).get("updates", {}).get("LAST_UPDATED") == last_updated:
                    return f.name
            except Exception:  # noqa: BLE001
                pass
        return None

    pending = HERE / "constants_patch.json"
    if not pending.exists():
        if args.no_pending_ok:
            notes.append("no pending constants_patch.json (allowed)")
        elif args.consumed_ok:
            found = archive_with(args.consumed_ok)
            if found:
                notes.append(f"pending patch ({args.consumed_ok}) was consumed and archived "
                             f"as {found} — the apply job ran")
            else:
                problems.append(
                    f"pending constants_patch.json vanished and NO archive carries its "
                    f"LAST_UPDATED {args.consumed_ok} — the patch was lost, not applied")
        else:
            problems.append(
                "no pending constants_patch.json — Monday's apply job would "
                "have nothing to apply")
    else:
        try:
            lu = json.loads(pending.read_text())["updates"]["LAST_UPDATED"]
            notes.append(f"pending constants_patch.json -> LAST_UPDATED {lu}")
        except Exception as e:  # noqa: BLE001
            problems.append(f"pending constants_patch.json unreadable: {e}")

    archives = sorted(HERE.glob("constants_patch.applied_*.json"))
    for f in archives:
        m = re.search(r"applied_(\d{4}-\d{2}-\d{2})", f.name)
        if not m:
            continue
        named = m.group(1)
        try:
            written = json.loads(f.read_text()).get("updates", {}).get("LAST_UPDATED")
        except Exception as e:  # noqa: BLE001
            problems.append(f"{f.name}: unreadable ({e})")
            continue
        if written and written > named:
            problems.append(
                f"{f.name} holds LAST_UPDATED {written}, which is NEWER than its "
                f"own filename date {named} — this is the rename trap: newer "
                f"content was merged into an older archive")

    notes.append(f"{len(archives)} archive(s) checked")

    for n in notes:
        print(f"  ok   {n}")
    if not problems:
        print("✅ patch files intact.")
        return 0

    print()
    for p in problems:
        print(f"❌ {p}")
    print("""
RECOVERY
  Find the two commits involved:
      git log --oneline -6
  Restore the archive from the apply-job commit, and the pending patch from
  your own research commit:
      git show <bot-commit>:constants_patch.applied_YYYY-MM-DD.json > constants_patch.applied_YYYY-MM-DD.json
      git show <research-commit>:constants_patch.json > constants_patch.json
  Then re-run:
      python3 validate_patch.py constants_patch.json
      python3 check_patch_integrity.py
""")
    return 1


if __name__ == "__main__":
    sys.exit(main())
