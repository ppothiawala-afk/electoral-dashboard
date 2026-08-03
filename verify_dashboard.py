#!/usr/bin/env python3
"""
verify_dashboard.py — deterministic verification layer for the Electoral Dashboard.

Two modes (combinable):

  --local   Repo-side checks, no network. Run in Cowork during the Monday
            routine and anywhere as a pre-commit sanity check:
              L1  news_analysis.json parses; schema fields present
              L2  news_analysis.json freshness (generated within --max-age days)
              L3  sentiment values in 0-100; outlet leans in -2..2
              L4  every scored (non-baseline) state is in news_config.json
              L5  index.html: DEFAULT_* ratings all in the 7-point enum
              L6  index.html: State News tab wired (TABS + fetch present)
              L7  pending constants_patch.json validates (via validate_patch)
              L8  history.json parses and is chronologically ordered

  --sheet   Live-Sheet checks, needs network + GOOGLE_CREDENTIALS (or
            service_account.json). Run in GitHub Actions AFTER apply:
              S1  Constants invariants: SENATE_R+SENATE_D==100,
                  HOUSE_R+HOUSE_D+HOUSE_I+HOUSE_VACANCIES==435
              S2  Constants LAST_UPDATED parses and is <= --max-age days old
              S3  every Rating in Senate/House/Governors is in the enum
              S4  the most recent constants_patch.applied_*.json actually
                  landed: updates match Constants, row_updates match rows

Failures exit 1 (reds the Actions run). Warnings print but don't fail.
Writes verification_report.json with the full check list either way.

Usage:
  python3 verify_dashboard.py --local
  python3 verify_dashboard.py --sheet --sheet-id <ID>
  python3 verify_dashboard.py --local --sheet --sheet-id <ID>
"""

import argparse
import datetime
import glob
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RATINGS = {"Solid D", "Likely D", "Lean D", "Toss-up", "Lean R", "Likely R", "Solid R"}

results = []  # (check_id, status "PASS"|"WARN"|"FAIL", message)


def record(check, status, msg):
    results.append({"check": check, "status": status, "message": msg})
    icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}[status]
    print(f"  {icon} {check}: {msg}")


# ────────────────────────────── LOCAL MODE ──────────────────────────────

def _refresh_coverage(na, cfg, window_days: int):
    """
    Which configured races actually received fresh articles this cycle?

    L2-freshness only reads the `generated` date stamp, so bumping that field
    satisfies it whether 27 races were rescored or zero. This measures the work
    instead: a configured race counts as refreshed only if it carries at least
    one article dated within `window_days` of `generated`. Returns (fresh, stale)
    as lists of "ST/Type" labels, or None if `generated` is unparseable.
    """
    try:
        gen = datetime.date.fromisoformat(na.get("generated", ""))
    except ValueError:
        return None
    cutoff = gen - datetime.timedelta(days=window_days)
    fresh, stale = [], []
    for st, sdata in cfg.get("states", {}).items():
        for cfg_race in sdata.get("races", []):
            typ = cfg_race.get("type")
            label = f"{st}/{typ}"
            hit = next((r for r in na.get("states", {}).get(st, {}).get("races", [])
                        if r.get("type") == typ), None)
            if hit is None:
                stale.append(f"{label} (absent from news_analysis)")
                continue
            dates = []
            for a in hit.get("articles", []):
                try:
                    dates.append(datetime.date.fromisoformat(a.get("date", "")))
                except ValueError:
                    pass
            if dates and max(dates) >= cutoff:
                fresh.append(label)
            else:
                stale.append(f"{label} (newest {max(dates).isoformat() if dates else 'none'})")
    return fresh, stale


def _briefing_chamber_claims(text: str):
    """
    Pull every chamber-balance claim out of a briefing's prose.

    Briefings have used three shapes across the archive, so we try all of them:
      inline pipe   "218R | 212D | 1I | 4V House / 53R | 47D | 2I Senate"
      inline slash  "53 R / 47 D / 3 I"
      markdown row  "| **House** | 218 | 212 | 1 | 4 | 435 |"

    Returns a list of (field, value, snippet). Two deliberate narrowings, both
    of which exist to stop the parser inventing claims:

    1. SCOPE — only the "## Chamber Balance" section is read. Current-state
       figures live there by template; numbers elsewhere are commentary.
    2. FIRST WINS — only the first value seen for each field counts. The
       template leads with the authoritative "Confirmed: ..." line and then
       elaborates, and elaboration can legitimately contain other compositions.
       The 2026-07-29 briefing is the proof case: it says "53 R / 47 D / 3 I,
       unchanged" and then, one sentence later, "the *registration* split is
       53 R / 45 D / 2 I". Both are true; only the first is a claim about what
       the dashboard publishes. Without first-wins this check would hard-FAIL a
       perfectly correct briefing and abort an unattended run — the exact
       brittleness that would make the gate worse than no gate.

    It also matches only these structured shapes, never a bare number near a
    label, so a sentence like "SENATE_I changed 3 -> 2" is ignored.
    """
    t = text.replace("**", "").replace("\\*", "").replace("*", "")

    # Narrow to the Chamber Balance section when the template heading is present.
    m = re.search(r"^##\s*Chamber Balance\s*$", t, re.I | re.M)
    if m:
        rest = t[m.end():]
        nxt = re.search(r"^##\s+", rest, re.M)
        t = rest[: nxt.start()] if nxt else rest

    out = []

    # House: three-digit R then D, optional I and vacancies.
    for m in re.finditer(
        r"(\d{3})\s*R\s*[|/]\s*(\d{3})\s*D"
        r"(?:\s*[|/]\s*(\d{1,2})\s*I)?"
        r"(?:\s*[|/]\s*(\d{1,2})\s*V)?",
        t, re.I,
    ):
        snip = m.group(0).strip()
        out.append(("HOUSE_R", int(m.group(1)), snip))
        out.append(("HOUSE_D", int(m.group(2)), snip))
        if m.group(3) is not None:
            out.append(("HOUSE_I", int(m.group(3)), snip))
        if m.group(4) is not None:
            out.append(("HOUSE_VACANCIES", int(m.group(4)), snip))

    # Senate: two-digit R then D, optional I.
    for m in re.finditer(
        r"(\d{2})\s*R\s*[|/]\s*(\d{2})\s*D(?:\s*[|/]\s*(\d{1,2})\s*I)?", t, re.I
    ):
        snip = m.group(0).strip()
        out.append(("SENATE_R", int(m.group(1)), snip))
        out.append(("SENATE_D", int(m.group(2)), snip))
        if m.group(3) is not None:
            out.append(("SENATE_I", int(m.group(3)), snip))

    # Markdown table rows: | House | 218 | 212 | 1 | 4 | 435 |
    for m in re.finditer(
        r"\|\s*(House|Senate)\s*\|\s*(\d{2,3})\s*\|\s*(\d{2,3})\s*\|\s*(\d{1,2})", t, re.I
    ):
        ch = m.group(1).upper()
        snip = m.group(0).strip()
        out.append((f"{ch}_R", int(m.group(2)), snip))
        out.append((f"{ch}_D", int(m.group(3)), snip))
        out.append((f"{ch}_I", int(m.group(4)), snip))

    # First wins — see the docstring. Later mentions are elaboration, not claims.
    first, seen = [], set()
    for f, v, s in out:
        if f not in seen:
            seen.add(f)
            first.append((f, v, s))
    return first


def check_briefing_consistency():
    """
    L11 — the briefing's prose must agree with the patch the Sheet will receive.

    WHY: on 2026-08-03 SENATE_I was corrected 3 -> 2 in constants_patch.json,
    history.json and SKILL.md, but the briefing — the document humans actually
    read — still said "3I" in two places. Nothing in the pipeline noticed. It was
    caught only because the user happened to ask for the briefing to be updated.
    On an unattended run that backstop does not exist.

    FAILURE MODEL (deliberate, see below): a detected contradiction is
    unambiguous and hard-FAILS. A failure to EXTRACT is not evidence of anything
    — briefings vary in format — so it WARNs and lets the run proceed. Without
    that asymmetry a brittle prose parser could abort an otherwise-good
    autonomous run, trading a rare silent error for a frequent loud one.
    """
    patch_p = HERE / "constants_patch.json"
    if not patch_p.exists():
        record("L11-briefing", "PASS", "no pending patch (nothing to reconcile)")
        return
    briefs = sorted(HERE.glob("weekly_briefing_*.md"))
    if not briefs:
        record("L11-briefing", "WARN", "no weekly briefing found to reconcile")
        return
    brief = briefs[-1]
    try:
        updates = json.loads(patch_p.read_text()).get("updates", {})
        claims = _briefing_chamber_claims(brief.read_text())
    except Exception as e:  # noqa: BLE001
        record("L11-briefing", "WARN", f"could not read: {e}")
        return

    checked = [(f, v, s) for f, v, s in claims if f in updates]
    if not checked:
        record("L11-briefing", "WARN",
               f"{brief.name}: no chamber figures found in a recognised format — "
               f"consistency with the patch is UNVERIFIED, not confirmed")
        return

    bad = [(f, v, s) for f, v, s in checked if v != updates[f]]
    if bad:
        detail = "; ".join(
            f"briefing says {f}={v} but patch says {updates[f]} (in \"{s}\")"
            for f, v, s in bad[:4]
        )
        record("L11-briefing", "FAIL",
               f"{brief.name} contradicts constants_patch.json — {detail}")
    else:
        record("L11-briefing", "PASS",
               f"{brief.name}: {len(checked)} chamber figures agree with the patch")


def check_local(max_age_days: int, refresh_window_days: int = 10):
    print("LOCAL checks:")

    # L1/L2/L3 — news_analysis.json
    try:
        na = json.loads((HERE / "news_analysis.json").read_text())
        record("L1-parse", "PASS", f"news_analysis.json parses ({len(na.get('states', {}))} states)")
    except Exception as e:  # noqa: BLE001
        record("L1-parse", "FAIL", f"news_analysis.json: {e}")
        na = None

    if na:
        try:
            gen = datetime.date.fromisoformat(na.get("generated", "1970-01-01"))
            age = (datetime.date.today() - gen).days
            if age <= max_age_days:
                record("L2-freshness", "PASS", f"generated {gen} ({age}d old)")
            else:
                # WARN not FAIL: stale news shouldn't red a Sheet-apply run;
                # the Monday Cowork routine is where staleness gets fixed.
                record("L2-freshness", "WARN", f"generated {gen} is {age}d old (max {max_age_days}) — run the weekly news refresh")
        except ValueError:
            record("L2-freshness", "FAIL", f"bad generated date: {na.get('generated')!r}")

        bad = []
        for st, sdata in na.get("states", {}).items():
            for r in sdata.get("races", []):
                if not (0 <= r.get("sentiment", -1) <= 100):
                    bad.append(f"{st}/{r.get('type')}: sentiment {r.get('sentiment')}")
                for o in r.get("outlets", []):
                    if o.get("lean") is not None and not (-2 <= o["lean"] <= 2):
                        bad.append(f"{st}/{r.get('type')}: outlet lean {o['lean']}")
                for c in r.get("candidates", []):
                    if not (0 <= c.get("sentiment", -1) <= 100):
                        bad.append(f"{st}/{r.get('type')}: candidate {c.get('name')} sentiment")
        record("L3-ranges", "FAIL" if bad else "PASS",
               "; ".join(bad[:5]) if bad else "all sentiment/lean values in range")

    # L4 — scored states covered by config
    try:
        cfg = json.loads((HERE / "news_config.json").read_text())
        if na:
            scored = {st for st, s in na["states"].items()
                      if not s.get("baseline") and any(not r.get("baseline") for r in s["races"])}
            missing = sorted(scored - set(cfg.get("states", {}).keys()))
            record("L4-config", "WARN" if missing else "PASS",
                   f"scored states missing from config: {missing}" if missing
                   else f"all {len(scored)} scored states present in news_config.json")
        bad_leans = {k: v for k, v in cfg.get("outlet_lean", {}).items() if not (-2 <= v <= 2)}
        if bad_leans:
            record("L4-leans", "FAIL", f"outlet_lean out of range: {bad_leans}")

        # L2b — did the refresh actually touch every configured race?
        if na:
            cov = _refresh_coverage(na, cfg, refresh_window_days)
            if cov is None:
                record("L2b-coverage", "WARN", "cannot compute: generated date unparseable")
            else:
                fresh, stale = cov
                total = len(fresh) + len(stale)
                if not stale:
                    record("L2b-coverage", "PASS",
                           f"all {total} configured races refreshed "
                           f"(article within {refresh_window_days}d of generated)")
                else:
                    shown = "; ".join(stale[:8])
                    more = f" (+{len(stale) - 8} more)" if len(stale) > 8 else ""
                    record("L2b-coverage", "WARN",
                           f"{len(fresh)}/{total} configured races refreshed — "
                           f"{len(stale)} stale: {shown}{more}")
    except Exception as e:  # noqa: BLE001
        record("L4-config", "FAIL", f"news_config.json: {e}")

    # L5/L6 — index.html
    try:
        html = (HERE / "index.html").read_text()
        found = set(re.findall(r'rating:"([^"]+)"', html))
        bad = found - RATINGS
        record("L5-enums", "FAIL" if bad else "PASS",
               f"invalid ratings in index.html fallbacks: {bad}" if bad
               else "all fallback ratings in 7-point enum")
        ok = '"State News"' in html and "news_analysis.json" in html
        record("L6-wiring", "PASS" if ok else "FAIL",
               "State News tab + JSON fetch wired" if ok else "State News tab or fetch missing from index.html")
    except Exception as e:  # noqa: BLE001
        record("L5-enums", "FAIL", f"index.html: {e}")

    # L7 — pending patch validates
    pending = HERE / "constants_patch.json"
    if pending.exists():
        r = subprocess.run([sys.executable, str(HERE / "validate_patch.py"), str(pending)],
                           capture_output=True, text=True)
        record("L7-patch", "PASS" if r.returncode == 0 else "FAIL",
               "pending patch validates" if r.returncode == 0
               else f"validate_patch failed: {(r.stdout + r.stderr)[-200:]}")
    else:
        record("L7-patch", "PASS", "no pending patch (nothing to validate)")

    # L9 — sentiment time-series includes the current analysis snapshot
    try:
        sh = json.loads((HERE / "sentiment_history.json").read_text())
        dates = [s["date"] for s in sh.get("snapshots", [])]
        gen = na.get("generated") if na else None
        if gen and gen in dates:
            record("L9-timeseries", "PASS", f"{len(dates)} snapshots; current ({gen}) recorded")
        else:
            record("L9-timeseries", "WARN",
                   f"snapshot for {gen} missing — run append_sentiment_history.py after each news refresh")
    except FileNotFoundError:
        record("L9-timeseries", "WARN", "sentiment_history.json not found — run append_sentiment_history.py")
    except Exception as e:  # noqa: BLE001
        record("L9-timeseries", "FAIL", f"sentiment_history.json: {e}")

    # L10 — every cited URL must be a deep link to an article, not a publisher homepage
    try:
        from urllib.parse import urlparse

        def homepage_only(urls):
            bad = []
            for u in urls:
                p = urlparse(u)
                if p.scheme in ("http", "https") and p.path in ("", "/") and not p.query:
                    bad.append(u)
            return bad

        bad = []
        html = (HERE / "index.html").read_text()
        demo = re.search(r"const DEMO_NEWS = \[(.*?)\n\];", html, re.S)
        if demo:
            bad += [f"index.html DEMO_NEWS: {u}"
                    for u in homepage_only(re.findall(r'url:"([^"]+)"', demo.group(1)))]
        if na:
            for st, s in na.get("states", {}).items():
                for r in s.get("races", []):
                    bad += [f"news_analysis.json {st}/{r.get('type')}: {a.get('url')}"
                            for a in r.get("articles", [])
                            if homepage_only([a.get("url", "")])]
        record("L10-links", "FAIL" if bad else "PASS",
               f"homepage-only links (must deep-link to the article): {bad[:5]}" if bad
               else "all article links are deep links")
    except Exception as e:  # noqa: BLE001
        record("L10-links", "FAIL", f"link check: {e}")

    # L8 — history.json ordering
    try:
        hist = json.loads((HERE / "history.json").read_text())
        entries = hist if isinstance(hist, list) else hist.get("weeks", hist.get("entries", []))
        dates = [e.get("date") or e.get("week") for e in entries if isinstance(e, dict)]
        dates = [d for d in dates if d]
        record("L8-history", "PASS" if dates == sorted(dates) else "WARN",
               f"{len(entries)} entries, chronological" if dates == sorted(dates)
               else "history.json entries not in chronological order")
    except Exception as e:  # noqa: BLE001
        record("L8-history", "WARN", f"history.json: {e}")

    # L11 — briefing prose vs the patch the Sheet will receive
    check_briefing_consistency()


# ────────────────────────────── SHEET MODE ──────────────────────────────

def check_sheet(sheet_id: str, max_age_days: int):
    print("SHEET checks:")
    sys.path.insert(0, str(HERE))
    from update_sheet import get_sheets_service, read_sheet  # noqa: PLC0415

    service = get_sheets_service(HERE / "service_account.json")

    def as_dicts(tab):
        rows = read_sheet(service, sheet_id, tab)
        if not rows:
            return []
        header = rows[0]
        return [dict(zip(header, r + [""] * (len(header) - len(r)))) for r in rows[1:]]

    # S1/S2 — Constants invariants + freshness
    consts = {r.get("Key", r.get("Constant", "")): r.get("Value", "") for r in as_dicts("Constants")}

    def num(k):
        try:
            return int(str(consts.get(k, "")).strip())
        except ValueError:
            return None

    sr, sd = num("SENATE_R"), num("SENATE_D")
    if sr is None or sd is None:
        record("S1-senate", "FAIL", f"missing SENATE_R/SENATE_D in Constants (got {sr},{sd})")
    else:
        record("S1-senate", "PASS" if sr + sd == 100 else "FAIL",
               f"SENATE {sr}R+{sd}D = {sr + sd} (must be 100; independents overlap by design)")
    hr, hd, hi, hv = num("HOUSE_R"), num("HOUSE_D"), num("HOUSE_I"), num("HOUSE_VACANCIES")
    if None in (hr, hd, hi, hv):
        record("S1-house", "FAIL", "missing HOUSE_* constants")
    else:
        tot = hr + hd + hi + hv
        record("S1-house", "PASS" if tot == 435 else "FAIL",
               f"HOUSE {hr}R+{hd}D+{hi}I+{hv}vac = {tot} (must be 435)")

    lu = consts.get("LAST_UPDATED", "")
    try:
        age = (datetime.date.today() - datetime.date.fromisoformat(lu)).days
        record("S2-fresh", "PASS" if age <= max_age_days else "FAIL",
               f"Constants LAST_UPDATED {lu} ({age}d old)")
    except ValueError:
        record("S2-fresh", "FAIL", f"Constants LAST_UPDATED unparseable: {lu!r}")

    # S3 — rating enums per tab
    for tab, flag_col in [("Senate", "Up in 2026"), ("Governors", "Election 2026"), ("House", None)]:
        bad = []
        for r in as_dicts(tab):
            if flag_col and str(r.get(flag_col, "")).strip().upper() != "YES":
                continue
            rating = str(r.get("Rating", "")).strip()
            if rating and rating not in RATINGS:
                bad.append(f"{r.get('State')}:{rating!r}")
        record(f"S3-{tab.lower()}", "FAIL" if bad else "PASS",
               f"invalid ratings: {bad[:5]}" if bad else f"{tab} ratings all valid")

    # S4 — latest applied patch actually landed
    applied = sorted(glob.glob(str(HERE / "constants_patch.applied_*.json")))
    if not applied:
        record("S4-landed", "WARN", "no archived patches found to verify")
        return
    patch = json.loads(Path(applied[-1]).read_text())
    label = Path(applied[-1]).name
    mismatches = []
    for k, v in patch.get("updates", {}).items():
        if k == "LAST_UPDATED":
            # update_sheet.py stamps LAST_UPDATED with the APPLY date (by design;
            # this fixed the old staleness-display bug). The patch carries the
            # research date, so comparing them yields a false S4 failure whenever
            # a patch is applied on a later day than it was written.
            continue
        actual = str(consts.get(k, "")).strip()
        if actual != str(v).strip():
            mismatches.append(f"Constants.{k}: patch={v!r} sheet={actual!r}")
    for tab, spec in patch.get("row_updates", {}).items():
        rows = as_dicts(tab)
        key_cols = spec.get("key_cols", [])
        col_map = spec.get("extra_col_map", {})
        for change in spec.get("changes", []):
            key = change["key"] if isinstance(change["key"], list) else [change["key"]]
            match = [r for r in rows
                     if [str(r.get(kc, "")).strip() for kc in key_cols] == [str(k).strip() for k in key]]
            if len(match) != 1:
                mismatches.append(f"{tab} key {key}: {len(match)} rows matched")
                continue
            row = match[0]
            if "rating" in change and str(row.get(spec.get("rating_col", "Rating"), "")).strip() != change["rating"]:
                mismatches.append(f"{tab} {key} rating: patch={change['rating']!r} sheet={row.get('Rating')!r}")
            for col, field in col_map.items():
                if field in change and col in row:
                    if str(row[col]).strip() != str(change[field]).strip():
                        mismatches.append(f"{tab} {key} {col}: patch={change[field]!r} sheet={row[col]!r}")
    record("S4-landed", "FAIL" if mismatches else "PASS",
           f"{label} mismatches: " + "; ".join(mismatches[:5]) if mismatches
           else f"{label} fully landed on the Sheet")


# ────────────────────────────────── main ─────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--sheet-id", default="")
    ap.add_argument("--max-age", type=int, default=10, help="max staleness in days")
    ap.add_argument("--refresh-window", type=int, default=10,
                    help="L2b: a configured race counts as refreshed only if it has an "
                         "article dated within this many days of news_analysis.generated")
    args = ap.parse_args()
    if not (args.local or args.sheet):
        ap.error("pass --local and/or --sheet")

    if args.local:
        check_local(args.max_age, args.refresh_window)
    if args.sheet:
        if not args.sheet_id:
            ap.error("--sheet requires --sheet-id")
        check_sheet(args.sheet_id, args.max_age)

    fails = [r for r in results if r["status"] == "FAIL"]
    warns = [r for r in results if r["status"] == "WARN"]
    report = {
        "run": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "passed": len(results) - len(fails) - len(warns),
        "warnings": len(warns), "failures": len(fails),
        "checks": results,
    }
    (HERE / "verification_report.json").write_text(json.dumps(report, indent=2))
    print(f"\n{report['passed']} passed · {len(warns)} warnings · {len(fails)} FAILURES"
          f" → verification_report.json")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
