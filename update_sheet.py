#!/usr/bin/env python3
"""
Electoral Dashboard — Google Sheets Auto-Updater
================================================
Scrapes current 2026 race ratings from public sources and writes them
directly to your Google Sheet (all 4 tabs: Senate, House, Governors, StateLeg).

Sources used (all free / public):
  - Wikipedia (race ratings tables, incumbents, seat counts)
  - Sabato's Crystal Ball (centerforpolitics.org)
  - Ballotpedia

Setup: See SETUP_GUIDE.md in this folder.
Run:   python3 update_sheet.py --sheet-id YOUR_SHEET_ID
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ── Configuration ─────────────────────────────────────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = Path(__file__).parent / "service_account.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Canonical 7-point rating scale used by the dashboard
VALID_RATINGS = {"Solid D", "Likely D", "Lean D", "Toss-up", "Lean R", "Likely R", "Solid R"}

# ── Chamber-balance invariants ────────────────────────────────────────────────
# HOUSE counts are EXCLUSIVE: HOUSE_R + HOUSE_D + HOUSE_I + HOUSE_VACANCIES == 435.
# SENATE counts OVERLAP: SENATE_R + SENATE_D == 100, with the two independents
# (Sanders-VT, King-ME) counted INSIDE those caucus totals; Murkowski-AK is R, not
# an independent (corrected 2026-08-03). SENATE_I (=2) is informational and a
# SUBSET of R/D — it is NOT added on top. Never "correct" the Senate to 100 by
# subtracting SENATE_I from R/D.
HOUSE_TOTAL_SEATS = 435
SENATE_TOTAL_SEATS = 100

# ── Rating normaliser ──────────────────────────────────────────────────────────

RATING_MAP = {
    # Sabato / Wikipedia short variants → canonical
    "safe d": "Solid D", "solid d": "Solid D",
    "likely d": "Likely D",
    "lean d": "Lean D", "tilt d": "Lean D",
    "tossup": "Toss-up", "toss-up": "Toss-up", "toss up": "Toss-up",
    "lean r": "Lean R", "tilt r": "Lean R",
    "likely r": "Likely R",
    "safe r": "Solid R", "solid r": "Solid R",
    # flip variants — strip "(flip)" and map the base
    "lean d (flip)": "Lean D", "lean r (flip)": "Lean R",
    "likely d (flip)": "Likely D", "likely r (flip)": "Likely R",
    "solid d (flip)": "Solid D", "solid r (flip)": "Solid R",
    "tossup (flip)": "Toss-up",
    # Wikipedia wikilink full-name variants  [[Lean Democratic]]  [[Solid Republican]]
    "solid democratic": "Solid D", "safe democratic": "Solid D",
    "likely democratic": "Likely D",
    "lean democratic": "Lean D", "tilt democratic": "Lean D",
    "lean republican": "Lean R", "tilt republican": "Lean R",
    "likely republican": "Likely R",
    "solid republican": "Solid R", "safe republican": "Solid R",
    # with trailing "seat" suffix: [[Safe Democratic seat]]
    "solid democratic seat": "Solid D", "safe democratic seat": "Solid D",
    "likely democratic seat": "Likely D", "lean democratic seat": "Lean D",
    "lean republican seat": "Lean R", "likely republican seat": "Likely R",
    "solid republican seat": "Solid R", "safe republican seat": "Solid R",
    "toss-up seat": "Toss-up",
}

def norm_rating(raw: str) -> str:
    if not raw:
        return ""
    key = raw.strip().lower().replace("–", "-")
    # strip trailing "(flip)" etc.
    key = re.sub(r"\s*\(flip\)\s*", "", key).strip()
    return RATING_MAP.get(key, raw.strip())


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def fetch(url: str, retries: int = 3):
    """Fetch a URL and return a BeautifulSoup object (for HTML pages)."""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return BeautifulSoup(r.text, "lxml")
        except Exception as e:
            print(f"  [fetch] attempt {attempt+1} failed for {url}: {e}")
            time.sleep(3 * (attempt + 1))
    return None


# ── Scrapers ──────────────────────────────────────────────────────────────────

def _parse_ratings_table(soup, state_col: int = 0, rating_col: int = 4) -> dict:
    """
    Generic helper: find the first sortable wikitable on a Wikipedia page and
    extract state → rating from the specified column indices.

    Wikipedia election ratings pages share a consistent table structure:
      col 0 = State (or District)
      col 4 = Cook Political Report rating (first rater, most authoritative)

    We use Cook as the canonical source; if that cell is empty we fall back
    to the next non-empty rater column.

    Returns dict: state_text → canonical_rating_str
    """
    ratings = {}
    # Wikipedia uses class="wikitable" (sometimes also "sortable")
    tables = soup.find_all("table", class_="wikitable")
    for table in tables:
        rows = table.find_all("tr")
        # Skip header rows; look for data rows that have a state/district in col 0
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) <= max(state_col, rating_col):
                continue
            state_text = cells[state_col].get_text(separator=" ", strip=True)
            if not state_text:
                continue
            # Try the primary rating column, then fall back left-to-right through rater cols
            rating = ""
            for ci in range(rating_col, min(rating_col + 4, len(cells))):
                raw = cells[ci].get_text(separator=" ", strip=True)
                candidate = norm_rating(raw)
                if candidate in VALID_RATINGS:
                    rating = candidate
                    break
            if rating:
                ratings[state_text] = rating
    return ratings


def scrape_senate_ratings() -> dict:
    """
    Fetch 2026 Senate race ratings from the Wikipedia HTML page.

    The page has a clean wikitable with columns:
      State | PVI | Senator | Last election | Cook | IE | Sabato | WH
    We parse the Cook column (index 4) for each state that has a rating.

    Returns dict keyed by state abbrev → {rating, source}.
    """
    url = "https://en.wikipedia.org/wiki/2026_United_States_Senate_elections"
    print(f"  Fetching Senate ratings from Wikipedia HTML...")
    soup = fetch(url)
    if not soup:
        print("  WARNING: Could not fetch Senate ratings page.")
        return {}

    ratings = {}
    # The ratings table on the Senate page: State col=0, Cook col=4
    raw_map = _parse_ratings_table(soup, state_col=0, rating_col=4)

    for state_text, rating in raw_map.items():
        # state_text may be "Maine" or "North Carolina" or "Ohio (special)"
        clean = re.sub(r"\s*\(.*?\)", "", state_text).strip().title()
        abbr = STATE_NAME_TO_ABBR.get(clean)
        if abbr:
            ratings[abbr] = {"rating": rating, "source": "Wikipedia/HTML"}

    print(f"  Found {len(ratings)} Senate ratings from Wikipedia HTML.")
    return ratings


def scrape_house_ratings() -> dict:
    """
    Fetch 2026 House competitive race ratings from the Wikipedia HTML ratings page.

    The page has a wikitable with columns:
      District | CPVI | Incumbent | Last result | Cook | IE | Sabato | WH
    The District cell contains a link whose href encodes state and district number,
    e.g. /wiki/Arizona%27s_6th_congressional_district

    Returns dict keyed by (state_abbr, district_str) → {rating, source}.
    """
    url = "https://en.wikipedia.org/wiki/2026_United_States_House_of_Representatives_election_ratings"
    print(f"  Fetching House ratings from Wikipedia HTML...")
    soup = fetch(url)
    if not soup:
        print("  WARNING: Could not fetch House ratings page.")
        return {}

    competitive = {}

    # district link pattern: /wiki/State%27s_Nth_congressional_district
    # or /wiki/State%27s_at-large_congressional_district
    dist_link_pat = re.compile(
        r"/wiki/([A-Za-z_%27]+)%27s_(\d+)(?:st|nd|rd|th)?(?:_at-large)?_congressional_district",
        re.I
    )
    at_large_pat = re.compile(
        r"/wiki/([A-Za-z_%27]+)%27s_at-large_congressional_district",
        re.I
    )

    tables = soup.find_all("table", class_="wikitable")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) < 5:
                continue

            # Extract district from link in first cell
            first_cell = cells[0]
            link = first_cell.find("a", href=True)
            if not link:
                continue
            href = link.get("href", "")

            state_name = None
            dist_num = None

            # Try numbered district first
            m = dist_link_pat.search(href)
            if m:
                state_name = m.group(1).replace("%27", "'").replace("_", " ").title()
                dist_num = m.group(2).zfill(2)
            else:
                # At-large district
                m2 = at_large_pat.search(href)
                if m2:
                    state_name = m2.group(1).replace("%27", "'").replace("_", " ").title()
                    dist_num = "00"  # at-large

            if not state_name or dist_num is None:
                continue

            abbr = STATE_NAME_TO_ABBR.get(state_name)
            if not abbr:
                continue

            # Cook rating is column 4 (index 4); fall back to cols 5,6,7 if blank
            rating = ""
            for ci in range(4, min(8, len(cells))):
                raw = cells[ci].get_text(separator=" ", strip=True)
                candidate = norm_rating(raw)
                if candidate in VALID_RATINGS:
                    rating = candidate
                    break

            if rating:
                competitive[(abbr, dist_num)] = {"rating": rating, "source": "Wikipedia/HTML"}

    print(f"  Found {len(competitive)} competitive House districts from Wikipedia HTML.")
    return competitive


def scrape_governor_ratings() -> dict:
    """
    Fetch 2026 gubernatorial race ratings from the Wikipedia HTML page.

    Returns dict keyed by state abbrev → {rating, source}.
    """
    url = "https://en.wikipedia.org/wiki/2026_United_States_gubernatorial_elections"
    print(f"  Fetching Governor ratings from Wikipedia HTML...")
    soup = fetch(url)
    if not soup:
        print("  WARNING: Could not fetch Governor ratings page.")
        return {}

    ratings = {}
    raw_map = _parse_ratings_table(soup, state_col=0, rating_col=4)

    for state_text, rating in raw_map.items():
        clean = re.sub(r"\s*\(.*?\)", "", state_text).strip().title()
        abbr = STATE_NAME_TO_ABBR.get(clean)
        if abbr:
            ratings[abbr] = {"rating": rating, "source": "Wikipedia/HTML"}

    print(f"  Found {len(ratings)} Governor ratings from Wikipedia HTML.")
    return ratings


def _margin_to_rating(r_seats: int, d_seats: int, total: int, is_dlcc_target: bool = False) -> str:
    """
    Convert a chamber's current R/D seat counts into a dashboard rating.

    The 7-point scale is approximated from seat margin as a % of total seats:
      D margin > 20%  → Solid D
      D margin 10-20% → Likely D
      D margin 3-10%  → Lean D
      margin ±3%      → Toss-up
      R margin 3-10%  → Lean R
      R margin 10-20% → Likely R
      R margin > 20%  → Solid R

    If the chamber is on the DLCC target list, we nudge one step toward D
    (reflects the competitive designation independent of raw seat margin).
    """
    if total <= 0:
        return "N/A"
    net = (d_seats - r_seats) / total * 100  # positive = D advantage
    if net > 20:
        base = "Solid D"
    elif net > 10:
        base = "Likely D"
    elif net > 3:
        base = "Lean D"
    elif net > -3:
        base = "Toss-up"
    elif net > -10:
        base = "Lean R"
    elif net > -20:
        base = "Likely R"
    else:
        base = "Solid R"

    # DLCC-targeted chambers nudge one step toward D (competitiveness signal)
    if is_dlcc_target:
        nudge = {
            "Solid R": "Likely R", "Likely R": "Lean R",
            "Lean R": "Toss-up", "Toss-up": "Lean D",
            "Lean D": "Lean D",  # already competitive
        }
        base = nudge.get(base, base)

    return base


def scrape_stateleg_ratings() -> dict:
    """
    Derive 2026 state legislative chamber ratings from Ballotpedia seat counts.

    Unlike Senate/House races, no rating service publishes a 7-point scale for
    state legislative chambers. Instead we:
      1. Scrape current R/D seat counts from Ballotpedia's chamber table.
      2. Convert the seat margin % into our 7-point scale via _margin_to_rating().
      3. Apply a competitive nudge for chambers on the DLCC target list.

    Returns dict keyed by state abbrev → {senate_rating, house_rating}.
    """
    url = "https://ballotpedia.org/State_legislative_elections,_2026"
    print(f"  Fetching StateLeg seat counts from Ballotpedia...")
    soup = fetch(url)
    if not soup:
        print("  WARNING: Could not fetch Ballotpedia StateLeg page.")
        return {}

    # DLCC target chambers (from their official 2026 announcement)
    DLCC_TARGETS = {
        "AK", "AZ", "MI", "MN", "NH", "PA", "WI",  # top targets (both chambers)
        "GA", "ME", "NE", "TX",                      # pickup opportunities
    }

    # Parse the seat-count table: State | Chamber | Republican | Democratic | Other | Vacancies | Total
    chamber_data = {}  # state_abbr → {"senate": {...}, "house": {...}}

    tables = soup.find_all("table", class_="wikitable")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) < 7:
                continue
            state_text = cells[0].get_text(strip=True)
            chamber_text = cells[1].get_text(strip=True).lower()
            try:
                r_seats = int(re.sub(r"[^\d]", "", cells[2].get_text(strip=True)) or 0)
                d_seats = int(re.sub(r"[^\d]", "", cells[3].get_text(strip=True)) or 0)
                total   = int(re.sub(r"[^\d]", "", cells[6].get_text(strip=True)) or 0)
            except (ValueError, IndexError):
                continue

            state_name = re.sub(r"\s*\(.*?\)", "", state_text).strip().title()
            abbr = STATE_NAME_TO_ABBR.get(state_name)
            if not abbr or total == 0:
                continue

            is_target = abbr in DLCC_TARGETS
            rating = _margin_to_rating(r_seats, d_seats, total, is_dlcc_target=is_target)

            if abbr not in chamber_data:
                chamber_data[abbr] = {}

            if "senate" in chamber_text:
                chamber_data[abbr]["senate_rating"] = rating
            elif "house" in chamber_text or "assembly" in chamber_text:
                chamber_data[abbr]["house_rating"] = rating

    # Ensure both keys exist for each state
    ratings = {}
    for abbr, data in chamber_data.items():
        if "senate_rating" in data or "house_rating" in data:
            ratings[abbr] = {
                "senate_rating": data.get("senate_rating", "N/A"),
                "house_rating":  data.get("house_rating",  "N/A"),
            }

    print(f"  Found {len(ratings)} StateLeg chamber ratings from Ballotpedia.")
    return ratings


# ── State name → abbreviation lookup ─────────────────────────────────────────

STATE_NAME_TO_ABBR = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA",
    "Colorado":"CO","Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA",
    "Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA",
    "Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD",
    "Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS",
    "Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH",
    "New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC",
    "North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA",
    "Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN",
    "Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA",
    "West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY",
}


# ── Google Sheets writer ──────────────────────────────────────────────────────

def get_sheets_service(service_account_file: Path):
    # Prefer environment variable (base64-encoded JSON) over file
    env_creds = os.environ.get("GOOGLE_CREDENTIALS")
    if env_creds:
        try:
            info = json.loads(base64.b64decode(env_creds).decode("utf-8"))
            creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            print("  ✓ Loaded credentials from GOOGLE_CREDENTIALS environment variable.")
            return build("sheets", "v4", credentials=creds)
        except Exception as e:
            print(f"  WARNING: Failed to load GOOGLE_CREDENTIALS env var: {e}")
            print("  Falling back to service_account.json file...")
    # Fall back to file
    creds = service_account.Credentials.from_service_account_file(
        str(service_account_file), scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def read_sheet(service, sheet_id: str, tab: str) -> list[list]:
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{tab}!A:Z"
    ).execute()
    return result.get("values", [])


def write_sheet(service, sheet_id: str, tab: str, values: list[list]):
    body = {"values": values}
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{tab}!A1",
        valueInputOption="RAW",
        body=body,
    ).execute()
    print(f"  ✓ Wrote {len(values)-1} data rows to '{tab}' tab.")


def update_ratings_in_tab(
    service, sheet_id: str, tab: str,
    rating_col_name: str,
    key_cols: list[str],
    new_ratings: dict,
    extra_col_map=None,
) -> int:
    """
    Generic function to update rating (and optionally other) columns in a tab.
    - key_cols: column names whose combined values form the lookup key
    - new_ratings: dict mapping key tuple → {rating: ..., ...}
    - extra_col_map: {col_name: dict_key} for additional columns to update
    Returns number of cells updated.
    """
    rows = read_sheet(service, sheet_id, tab)
    if not rows:
        print(f"  WARNING: {tab} tab is empty.")
        return 0

    header = rows[0]
    try:
        rating_col_idx = header.index(rating_col_name)
    except ValueError:
        print(f"  WARNING: Column '{rating_col_name}' not found in {tab}. Headers: {header}")
        return 0

    key_col_idxs = []
    for kc in key_cols:
        try:
            key_col_idxs.append(header.index(kc))
        except ValueError:
            print(f"  WARNING: Key column '{kc}' not found in {tab}.")
            return 0

    extra_idxs = {}
    if extra_col_map:
        for col_name, dict_key in extra_col_map.items():
            try:
                extra_idxs[header.index(col_name)] = dict_key
            except ValueError:
                pass  # column not found, skip

    updated = 0
    for i, row in enumerate(rows[1:], 1):
        # Pad row if needed
        while len(row) <= max(rating_col_idx, *key_col_idxs, *(extra_idxs.keys() or [0])):
            row.append("")

        key = tuple(row[idx] if idx < len(row) else "" for idx in key_col_idxs)
        # Single-key case: unwrap tuple
        lookup_key = key[0] if len(key) == 1 else key

        if lookup_key in new_ratings:
            data = new_ratings[lookup_key]
            new_rating = data.get("rating","") if isinstance(data, dict) else str(data)
            if new_rating in VALID_RATINGS and row[rating_col_idx] != new_rating:
                print(f"    {tab} | {lookup_key}: {row[rating_col_idx]} → {new_rating}")
                row[rating_col_idx] = new_rating
                updated += 1
            # Update extra columns (these count as changes too — without this,
            # a tab with only Challenger/Notes edits and no rating change would
            # never be written back and the edits would be silently dropped)
            for col_idx, dict_key in extra_idxs.items():
                val = data.get(dict_key,"") if isinstance(data, dict) else ""
                if val and col_idx < len(row) and row[col_idx] != val:
                    print(f"    {tab} | {lookup_key}: extra col update ({dict_key})")
                    row[col_idx] = val
                    updated += 1

        rows[i] = row

    if updated > 0:
        write_sheet(service, sheet_id, tab, rows)
    else:
        print(f"  No rating changes detected in '{tab}'.")

    return updated


# ── Constants tab updater ─────────────────────────────────────────────────────

def check_chamber_invariants(merged: dict) -> list:
    """
    Validate chamber-balance invariants against a merged view of the Constants
    values (existing sheet values overlaid with the pending updates). Returns a
    list of human-readable error strings; empty means OK.

    HOUSE (exclusive): HOUSE_R + HOUSE_D + HOUSE_I + HOUSE_VACANCIES == 435.
    SENATE (overlapping): SENATE_R + SENATE_D == 100. SENATE_I is a subset of the
    caucus totals and is NOT added on top — do not net it out.
    """
    errors = []

    def _as_int(k):
        try:
            return int(merged[k])
        except (KeyError, TypeError, ValueError):
            return None

    house_keys = ["HOUSE_R", "HOUSE_D", "HOUSE_I", "HOUSE_VACANCIES"]
    if all(k in merged for k in house_keys):
        vals = [_as_int(k) for k in house_keys]
        if all(v is not None for v in vals):
            if sum(vals) != HOUSE_TOTAL_SEATS:
                errors.append(
                    f"HOUSE invariant: {vals[0]}R+{vals[1]}D+{vals[2]}I+{vals[3]}V="
                    f"{sum(vals)} != {HOUSE_TOTAL_SEATS} (exclusive counts)."
                )

    if "SENATE_R" in merged and "SENATE_D" in merged:
        r, d = _as_int("SENATE_R"), _as_int("SENATE_D")
        if r is not None and d is not None and (r + d) != SENATE_TOTAL_SEATS:
            errors.append(
                f"SENATE invariant: {r}R+{d}D={r + d} != {SENATE_TOTAL_SEATS}. "
                f"Independents are counted INSIDE R/D — do not subtract SENATE_I."
            )
    return errors


def update_constants(service, sheet_id: str, updates: dict) -> int:
    """
    Updates specific keys in the Constants tab without overwriting the whole tab.
    updates: dict of {key_name: new_value}
    Returns number of values changed.
    """
    rows = read_sheet(service, sheet_id, "Constants")
    if not rows:
        print("  WARNING: Constants tab not found or empty. Run setup_constants_tab.py first.")
        return 0

    # Build a key → row-index map (row 0 is header)
    key_to_row = {}
    for i, row in enumerate(rows):
        if row and str(row[0]).strip():
            key_to_row[str(row[0]).strip()] = i

    # ── Invariant gate ────────────────────────────────────────────────────────
    # Merge existing sheet values with the pending updates, then check the 435
    # and Senate==100 invariants BEFORE writing anything. A violation means the
    # update is internally inconsistent — refuse rather than corrupt the Sheet.
    merged = {}
    for key, ridx in key_to_row.items():
        merged[key] = rows[ridx][1] if len(rows[ridx]) > 1 else ""
    merged.update(updates)
    inv_errors = check_chamber_invariants(merged)
    if inv_errors:
        print("  ERROR: Constants write REFUSED — chamber-balance invariants violated:")
        for e in inv_errors:
            print(f"    - {e}")
        return 0

    changed = 0
    import datetime
    for key, new_val in updates.items():
        if key in key_to_row:
            row_idx = key_to_row[key]
            current_val = str(rows[row_idx][1]) if len(rows[row_idx]) > 1 else ""
            if current_val != str(new_val):
                print(f"    Constants | {key}: {current_val} → {new_val}")
                while len(rows[row_idx]) < 2:
                    rows[row_idx].append("")
                rows[row_idx][1] = new_val
                changed += 1
        else:
            # Key doesn't exist yet — append it
            rows.append([key, new_val, ""])
            changed += 1

    # Always update LAST_UPDATED
    today = datetime.date.today().isoformat()
    if "LAST_UPDATED" in key_to_row:
        rows[key_to_row["LAST_UPDATED"]][1] = today
    else:
        rows.append(["LAST_UPDATED", today, ""])

    if changed > 0:
        write_sheet(service, sheet_id, "Constants", rows)
    else:
        print("  No Constants changes detected.")

    return changed


def _parse_balance_from_text(text):
    """Parse R/D/I/vacancy counts from a House party breakdown page text."""
    r_match = re.search(r"(\d{3})\s*Republicans", text, re.I)
    d_match = re.search(r"(\d{3})\s*Democrats", text, re.I)
    v_match = re.search(r"(\d+)\s*Vacanc", text, re.I)
    i_match = re.search(r"(\d+)\s*(?:Other|Independent)", text, re.I)
    if not r_match or not d_match:
        return None
    return {
        "HOUSE_R": int(r_match.group(1)),
        "HOUSE_D": int(d_match.group(1)),
        "HOUSE_I": int(i_match.group(1)) if i_match else 0,
        "HOUSE_VACANCIES": int(v_match.group(1)) if v_match else 0,
    }


def scrape_house_balance(current_vacancies: int = 0):
    """
    Scrapes current House party balance from two official sources and validates.

    Rules applied before writing to the sheet:
    1. R + D + I + Vacancies must equal 435. If not, something is stale — skip write.
    2. Vacancies are NEVER reduced below a higher known value purely because the
       press gallery page hasn't been updated yet (vacancy floor). The page carries
       a disclaimer that it only updates when departures are read on the floor.
    3. If the scraped vacancy count is LOWER than the current sheet value, the page
       is lagging: we DO NOT invent replacement seat counts. Instead we skip the
       write for this source and flag for manual review (return None from the
       caller's perspective if no source is trustworthy). This replaces the old
       proportional-rescale behaviour, which fabricated R/D/I seat counts that
       never existed (audit finding 2.6 / §3).

    Args:
        current_vacancies: existing HOUSE_VACANCIES value from the Constants tab,
                           used as a floor for the vacancy count.
    Returns dict: {HOUSE_R, HOUSE_D, HOUSE_I, HOUSE_VACANCIES} or None on failure.
    """
    TOTAL_SEATS = HOUSE_TOTAL_SEATS

    for label, url in [
        ("Press Gallery",    "https://pressgallery.house.gov/member-data/party-breakdown"),
        ("Radio-TV Gallery", "https://radiotv.house.gov/house-data/party-breakdown"),
    ]:
        print(f"  Scraping House balance from {label}...")
        soup = fetch(url)
        if not soup:
            print(f"  WARNING: Could not fetch {label} page.")
            continue

        result = _parse_balance_from_text(soup.get_text(" ", strip=True))
        if not result:
            print(f"  WARNING: Could not parse R/D counts from {label}.")
            continue

        r, d, i, v = result["HOUSE_R"], result["HOUSE_D"], result["HOUSE_I"], result["HOUSE_VACANCIES"]
        total = r + d + i + v
        print(f"  {label}: {r}R / {d}D / {i}I / {v} vacancies (total={total})")

        if total != TOTAL_SEATS:
            print(f"  WARNING: Total {total} ≠ {TOTAL_SEATS}. Page likely stale — skipping this source.")
            continue

        # Vacancy floor: if the scraped vacancy count is LOWER than what we
        # already know, the page is lagging. Do NOT invent replacement seat
        # counts by rescaling — skip this source and flag for manual review.
        if v < current_vacancies:
            print(f"  WARNING: Scraped vacancies ({v}) < current sheet value ({current_vacancies}).")
            print(f"  {label} page likely lags (updates only when departures are read on the floor).")
            print(f"  SKIPPING this source — will not fabricate R/D/I seat counts. Flag for manual review.")
            continue

        print(f"  ✓ Using {label} data.")
        return result

    print("  WARNING: Could not get a validated House balance from any source.")
    print("  Skipping Constants chamber-balance write — FLAG FOR MANUAL REVIEW.")
    return None


# ── Main orchestrator ─────────────────────────────────────────────────────────

def run_update(sheet_id: str, dry_run: bool = False):
    print("=" * 60)
    print("Electoral Dashboard — Google Sheets Updater")
    print("=" * 60)

    # ── Auth ──
    if not os.environ.get("GOOGLE_CREDENTIALS") and not SERVICE_ACCOUNT_FILE.exists():
        print(f"\nERROR: No credentials found.")
        print(f"  Option 1: Set the GOOGLE_CREDENTIALS environment variable (recommended)")
        print(f"  Option 2: Place service_account.json at:\n    {SERVICE_ACCOUNT_FILE}")
        print("See SETUP_GUIDE.md for instructions.")
        sys.exit(1)

    print("\n[1/6] Authenticating with Google Sheets API...")
    service = get_sheets_service(SERVICE_ACCOUNT_FILE)
    print("  ✓ Authenticated.")

    # ── Scrape via Wikipedia REST API ──
    print("\n[2/6] Fetching Senate ratings (Wikipedia HTML)...")
    senate_ratings = scrape_senate_ratings()

    print("\n[3/6] Fetching Governor ratings (Wikipedia HTML)...")
    gov_ratings = scrape_governor_ratings()

    print("\n[4/6] Fetching House ratings (Wikipedia HTML)...")
    house_competitive = scrape_house_ratings()

    print("\n[5/6] Fetching StateLeg ratings (Wikipedia HTML)...")
    stateleg_ratings = scrape_stateleg_ratings()

    print("\n[6/6] Scraping House chamber balance (pressgallery.house.gov)...")
    # Read current vacancy count from sheet first so we can use it as a floor
    current_vacancies = 0
    try:
        constants_rows = read_sheet(service, sheet_id, "Constants")
        for row in constants_rows:
            if row and str(row[0]).strip() == "HOUSE_VACANCIES" and len(row) > 1:
                current_vacancies = int(row[1]) if str(row[1]).isdigit() else 0
                break
        print(f"  Current sheet vacancy count: {current_vacancies}")
    except Exception as e:
        print(f"  Could not read current vacancy count: {e}")
    house_balance = scrape_house_balance(current_vacancies=current_vacancies)

    if dry_run:
        print("\n[DRY RUN] Scraped data summary:")
        print(f"  Senate ratings found:   {len(senate_ratings)}")
        print(f"  Governor ratings found: {len(gov_ratings)}")
        print(f"  House competitive:      {len(house_competitive)}")
        print(f"  StateLeg ratings:       {len(stateleg_ratings)}")
        if house_balance:
            print(f"  House balance:          {house_balance}")
        print("\nDry run complete — no changes written to sheet.")
        return

    # ── Write to Sheets ──
    print("\n[Updating Google Sheet...]")

    # All three race tabs now flow through the single generic updater
    # update_ratings_in_tab(), instead of three hand-maintained inline loops.
    # This removes the drift risk that produced the Murkowski incident (the old
    # inline Senate path filtered "Up in 2026 == YES" while the generic path
    # relied on key_cols — two behaviours that had to be kept in sync by hand).
    #
    # Senate/Governors have TWO rows per state, so we key on the compound
    # (State, YES-flag) pair and only build entries for the seat up in 2026.
    # scrape_* dicts are keyed by state abbr; we re-key them to the compound
    # tuple the generic updater expects.

    # Senate: key_cols=["State","Up in 2026"], only the seat up in 2026.
    senate_keyed = {(state, "YES"): data for state, data in senate_ratings.items()}
    print("  Senate:")
    update_ratings_in_tab(
        service, sheet_id, "Senate",
        rating_col_name="Rating",
        key_cols=["State", "Up in 2026"],
        new_ratings=senate_keyed,
    )

    # Governors: key_cols=["State","Election 2026"], only the seat up in 2026.
    gov_keyed = {(state, "YES"): data for state, data in gov_ratings.items()}
    print("  Governors:")
    update_ratings_in_tab(
        service, sheet_id, "Governors",
        rating_col_name="Rating",
        key_cols=["State", "Election 2026"],
        new_ratings=gov_keyed,
    )

    # House: key_cols=["State","District"]. Normalise district to zero-padded
    # two-char strings to match the sheet's key format.
    house_keyed = {(state, str(dist).zfill(2)): data
                   for (state, dist), data in house_competitive.items()}
    print("  House:")
    update_ratings_in_tab(
        service, sheet_id, "House",
        rating_col_name="Rating",
        key_cols=["State", "District"],
        new_ratings=house_keyed,
    )

    # StateLeg: key = State, update SenateRating and HouseRating
    rows = read_sheet(service, sheet_id, "StateLeg")
    if rows:
        header = rows[0]
        try:
            state_idx = header.index("State")
            sen_r_idx = header.index("SenateRating")
            hou_r_idx = header.index("HouseRating")
            updated_sl = 0
            for i, row in enumerate(rows[1:], 1):
                state = row[state_idx] if state_idx < len(row) else ""
                if state in stateleg_ratings:
                    while len(row) <= max(sen_r_idx, hou_r_idx): row.append("")
                    data = stateleg_ratings[state]
                    s_new = data.get("senate_rating","")
                    h_new = data.get("house_rating","")
                    changed = False
                    if s_new in VALID_RATINGS and row[sen_r_idx] != s_new:
                        print(f"    StateLeg | {state} Senate: {row[sen_r_idx]} → {s_new}")
                        row[sen_r_idx] = s_new; changed = True; updated_sl += 1
                    if h_new in VALID_RATINGS and row[hou_r_idx] != h_new:
                        print(f"    StateLeg | {state} House:  {row[hou_r_idx]} → {h_new}")
                        row[hou_r_idx] = h_new; changed = True; updated_sl += 1
                    if changed:
                        rows[i] = row
            if updated_sl > 0:
                write_sheet(service, sheet_id, "StateLeg", rows)
            else:
                print("  No StateLeg rating changes detected.")
        except ValueError as e:
            print(f"  WARNING: StateLeg column issue: {e}")

    # ── Constants tab: update chamber balance ──
    print("\n[Updating Constants tab...]")
    if house_balance:
        update_constants(service, sheet_id, house_balance)
    else:
        print("  Skipping Constants update — could not scrape House balance.")

    print("\n✅ Update complete!")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Electoral Dashboard Google Sheet")
    parser.add_argument("--sheet-id", required=True,
                        help="Google Sheet ID (from the URL: /d/SHEET_ID/edit)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Scrape only — don't write to Google Sheet")
    parser.add_argument("--service-account", type=str, default=None,
                        help="Path to service_account.json (default: same folder as script)")
    args = parser.parse_args()

    if args.service_account:
        SERVICE_ACCOUNT_FILE = Path(args.service_account)

    run_update(sheet_id=args.sheet_id, dry_run=args.dry_run)
