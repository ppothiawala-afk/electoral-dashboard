#!/usr/bin/env python3
"""
check_consistency.py -- L13: keep restated facts from drifting out of sync.

WHY: canonical facts (SENATE_I=2, the two Senate independents, HOUSE=435) get
hard-coded into prose, comments, seed scripts and configs all over the repo. When
one is corrected the copies rot. On 2026-08-03 SENATE_I was fixed and five stale
copies survived -- including setup_constants_tab.py, a SEED script that would have
silently re-written the old value if run (found 2026-08-12). Nothing checked that
the copies agreed with the corrected value. This does.

Two checks, both driven by facts.json:
  L13a-facts  (FAIL): every STRUCTURAL assignment of a static constant in a LIVE
                      .py/.json file equals the canonical value. Precise, so a
                      re-introduced landmine (a seed script, a stray patch) fails
                      loudly. Historical artifacts and eval fixtures are excluded.
  L13b-drift  (WARN): fuzzy prose patterns (a "three independents" count,
                      Murkowski-as-independent, a bare stale SENATE_I value in
                      prose, a 103 Senate overlap sum) that USUALLY mean stale
                      docs. WARN, with a corrective-context exemption, because
                      prose varies and a false FAIL is worse than a visible warn.

note_target_rating() is a separate helper used by verify_dashboard.py's sheet-mode
S5-cellnote check to flag a rating cell that disagrees with a forecaster move
written in its own Notes (the GA-Sen 2026-08-12 lag).

Stdlib only. Exit 0 clean / 1 on any FAIL.  Usage: python3 check_consistency.py
"""

import json
import re
import sys
from fnmatch import fnmatch
from pathlib import Path

HERE = Path(__file__).resolve().parent

RATINGS = {"Solid D", "Likely D", "Lean D", "Toss-up", "Lean R", "Likely R", "Solid R"}


def load_facts(here=HERE):
    return json.loads((here / "facts.json").read_text(encoding="utf-8"))


def _excluded(rel: str, facts) -> bool:
    for d in facts.get("exclude_dirs", []):
        if rel == d or rel.startswith(d + "/"):
            return True
    name = rel.split("/")[-1]
    for g in facts.get("exclude_globs", []):
        if fnmatch(name, g) or fnmatch(rel, g):
            return True
    return False


def _iter_files(here, facts, exts):
    for p in sorted(here.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        rel = p.relative_to(here).as_posix()
        if _excluded(rel, facts):
            continue
        try:
            yield rel, p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue


def static_drift(here, facts):
    """L13a -- structural constant assignments must equal the canonical value."""
    problems = []
    for key, want in facts.get("constant_asserts", {}).items():
        pat = re.compile(r'["\']?%s["\']?\s*[:=]\s*(\d+)' % re.escape(key))
        for rel, text in _iter_files(here, facts, {".py", ".json"}):
            for m in pat.finditer(text):
                got = int(m.group(1))
                if got != want:
                    line = text[:m.start()].count("\n") + 1
                    problems.append(f"{rel}:{line} {key}={got} (canonical {want})")
    return problems


def prose_drift(here, facts):
    """L13b -- fuzzy stale-doc patterns, WARN, with corrective-context exemption."""
    warns = []
    exempt = [s.lower() for s in facts.get("exempt_line_contains", [])]
    pats = [(d["name"], re.compile(d["regex"], re.I)) for d in facts.get("drift_patterns", [])]
    for rel, text in _iter_files(here, facts, {".py", ".json", ".md", ".html"}):
        for i, ln in enumerate(text.splitlines(), 1):
            low = ln.lower()
            if any(e in low for e in exempt):
                continue
            for name, pat in pats:
                if pat.search(ln):
                    warns.append(f"{rel}:{i} [{name}] {ln.strip()[:90]}")
    return warns


# ── cell-vs-note helper (used by verify_dashboard.py sheet mode) ──────────────

_MOVE_RE = re.compile(
    r"(Solid|Safe|Likely|Leans?|Toss[- ]?up|Tilt)\s*([DR])?"
    r"\s*(?:->|→|to)\s*"
    r"(Solid|Safe|Likely|Leans?|Toss[- ]?up|Tilt)\s*([DR])?",
    re.I,
)


def _norm(tier, dr):
    t = tier.lower().replace(" ", "").replace("-", "")
    if t.startswith("toss"):
        return "Toss-up"
    if t == "tilt":
        return None  # IE-only tier; per route 3 it never sets a cell
    base = {"solid": "Solid", "safe": "Solid", "likely": "Likely",
            "lean": "Lean", "leans": "Lean"}.get(t)
    if not base or not dr:
        return None
    return f"{base} {dr.upper()}"


def note_target_rating(note: str):
    """Return the LAST forecaster-move target rating named in a Notes cell,
    normalized to the 7-point enum, or None. 'Safe' -> 'Solid'; 'Tilt' is ignored
    (IE-only, never a cell value per route 3, SKILL.md 2.3a)."""
    if not note:
        return None
    target = None
    for m in _MOVE_RE.finditer(note):
        t = _norm(m.group(3), m.group(4))
        if t in RATINGS:
            target = t
    return target


def check(here=HERE):
    facts = load_facts(here)
    results = []
    fails = static_drift(here, facts)
    if fails:
        results.append(("L13a-facts", "FAIL",
                        f"{len(fails)} constant(s) disagree with facts.json: "
                        + "; ".join(fails[:5])))
    else:
        results.append(("L13a-facts", "PASS",
                        "all structural constant assignments match facts.json"))
    warns = prose_drift(here, facts)
    if warns:
        results.append(("L13b-drift", "WARN",
                        f"{len(warns)} possible stale-doc mention(s): "
                        + "; ".join(warns[:5])))
    else:
        results.append(("L13b-drift", "PASS", "no stale-doc drift patterns found"))
    return results


def main():
    icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}
    results = check()
    for cid, status, msg in results:
        print(f"  {icon[status]} {cid}: {msg}")
    sys.exit(1 if any(s == "FAIL" for _, s, _ in results) else 0)


if __name__ == "__main__":
    main()
