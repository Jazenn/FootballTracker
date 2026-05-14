"""
Football Calendar Sync (HYBRID)
===============================
Fetches upcoming football matches and adds them to Google Calendar.
- Primary Source:   football-data.org (Free Plan)
- Secondary Source: TheSportsDB (Free) for Women/U21/Friendlies
"""

import sys
import time
import logging
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import (
    FOOTBALL_DATA_KEY, LOOKAHEAD_DAYS,
    FD_COMPETITIONS, FD_TEAMS, FD_NATIONAL_TEAMS,
    TSDB_TEAMS,
    CALENDAR_ID, EVENT_COLOR_ID, REMINDERS,
    DISPLAY_NAME_MAPPING,
)

# --- Logging -------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR   = SCRIPT_DIR.parent
LOG_FILE   = ROOT_DIR / "assets" / "logs" / "football_calendar.log"

# Ensure log directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# --- Auth ----------------------------------------------------------------------
AUTH_DIR         = ROOT_DIR / "assets" / "auth"
TOKEN_PATH       = AUTH_DIR / "token.json"
CREDENTIALS_PATH = AUTH_DIR / "credentials.json"
SCOPES           = ["https://www.googleapis.com/auth/calendar"]

# --- API Constants -------------------------------------------------------------
FD_BASE    = "https://api.football-data.org/v4"
FD_HEADERS = {"X-Auth-Token": FOOTBALL_DATA_KEY}
FD_DELAY   = 6.5  # free tier: 10 requests/min -> wait 6.5s

TSDB_BASE  = "https://www.thesportsdb.com/api/v1/json/123"

# ------------------------------------------------------------------------------
#  GOOGLE CALENDAR AUTH
# ------------------------------------------------------------------------------

def get_calendar_service():
    creds = None
    
    # Priority 1: GOOGLE_TOKEN_JSON environment variable (ideal for CI)
    env_token = os.environ.get("GOOGLE_TOKEN_JSON")
    if env_token:
        log.info("Loading Google credentials from GOOGLE_TOKEN_JSON environment variable...")
        try:
            creds = Credentials.from_authorized_user_info(json.loads(env_token), SCOPES)
        except Exception as e:
            log.warning(f"Failed to load credentials from GOOGLE_TOKEN_JSON: {e}")

    # Priority 2: Local token.json file
    if not creds and TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log.info("Refreshing Google token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                log.error(f"Failed to refresh token: {e}")
                creds = None # Force re-auth
        
        if not creds or not creds.valid:
            # Check for credentials in environment variable
            env_creds = os.environ.get("GOOGLE_CREDENTIALS_JSON")
            if env_creds:
                 log.info("Loading Google client secrets from GOOGLE_CREDENTIALS_JSON environment variable...")
                 flow = InstalledAppFlow.from_client_config(json.loads(env_creds), SCOPES)
            elif CREDENTIALS_PATH.exists():
                 log.info("Loading Google client secrets from credentials.json file...")
                 flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            else:
                log.error(f"\n[ERROR] No Google credentials found. Set GOOGLE_TOKEN_JSON or GOOGLE_CREDENTIALS_JSON, or place credentials.json at {CREDENTIALS_PATH}")
                sys.exit(1)

            if os.environ.get("CI"):
                log.error("[ERROR] Browser authorization is not possible in a CI environment. Please provide a valid GOOGLE_TOKEN_JSON.")
                sys.exit(1)
                
            log.info("Opening browser for Google Calendar authorization...")
            creds = flow.run_local_server(port=0)

        # Save the updated token back to file if possible (local runs)
        if not os.environ.get("CI"):
            try:
                TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
                TOKEN_PATH.write_text(creds.to_json())
                log.info(f"Updated token saved to {TOKEN_PATH}")
            except Exception as e:
                log.warning(f"Could not save token.json: {e}")
                
    return build("calendar", "v3", credentials=creds)


# ------------------------------------------------------------------------------
#  FOOTBALL-DATA.ORG (Primary)
# ------------------------------------------------------------------------------

def fd_get(endpoint: str, params: dict = None) -> list[dict]:
    """GET from football-data.org. Returns list of match dicts."""
    url = f"{FD_BASE}/{endpoint}"
    try:
        r = requests.get(url, headers=FD_HEADERS, params=params, timeout=15)
        if r.status_code == 429:
            log.warning("  Rate limited - waiting 65s...")
            time.sleep(65)
            r = requests.get(url, headers=FD_HEADERS, params=params, timeout=15)
        
        if r.status_code == 403:
            log.warning(f"  403 for {endpoint} - skipped (plan restriction)")
            return []
            
        r.raise_for_status()
        return r.json().get("matches", [])
    except Exception as e:
        log.error(f"  FD Error: {e}")
        return []


def fd_to_match(m: dict) -> dict:
    """Normalize a football-data.org match."""
    home = m.get("homeTeam", {}).get("name")
    away = m.get("awayTeam", {}).get("name")
    
    if not home or not away:
        return None

    return {
        "id":          f"fd_{m['id']}",
        "utcDate":     m["utcDate"],
        "competition": {"name": m["competition"]["name"]},
        "homeTeam":    {"name": home},
        "awayTeam":    {"name": away},
        "stage":       m.get("stage", ""),
    }


def collect_fd_matches() -> dict:
    today = datetime.now(timezone.utc).date()
    end   = today + timedelta(days=LOOKAHEAD_DAYS)
    params = {"dateFrom": today.isoformat(), "dateTo": end.isoformat()}
    
    collected = {}
    
    # 1. Specific Clubs (Liverpool)
    for team in FD_TEAMS:
        log.info(f"  Fetching for Team: {team['name']}...")
        matches = fd_get(f"teams/{team['id']}/matches", params)
        for m in matches:
            match = fd_to_match(m)
            if match:
                collected[match["id"]] = match
        log.info(f"       -> {len(matches)} match(es)")
        time.sleep(FD_DELAY)

    # 2. Competitions (Knockouts & National Search for official games)
    national_names = [t['name'].split("(")[0].strip() for t in FD_NATIONAL_TEAMS]
    
    for code in FD_COMPETITIONS:
        log.info(f"  Competition: {code} (Processing)...")
        matches = fd_get(f"competitions/{code}/matches", params)
        added_count = 0
        national_count = 0
        
        for m in matches:
            match = fd_to_match(m)
            if not match: continue

            stage = m.get("stage")
            is_knockout = code == "CL" and stage in ["LAST_16", "QUARTER_FINALS", "SEMI_FINALS", "FINAL"]
            
            is_national = False
            for nat_name in national_names:
                if nat_name in match["homeTeam"]["name"] or nat_name in match["awayTeam"]["name"]:
                    is_national = True
                    break
            
            if is_knockout or is_national:
                if match["id"] not in collected:
                    collected[match["id"]] = match
                    if is_knockout: added_count += 1
                    if is_national: national_count += 1
        
        if added_count > 0: log.info(f"       -> {added_count} knockout match(es) added")
        if national_count > 0: log.info(f"       -> {national_count} national team match(es) added")
        time.sleep(FD_DELAY)

    return collected


# ------------------------------------------------------------------------------
#  THESPORTSDB (Secondary)
# ------------------------------------------------------------------------------

def tsdb_get_next_events(team_id: int) -> list[dict]:
    try:
        r = requests.get(f"{TSDB_BASE}/eventsnext.php", params={"id": team_id}, timeout=15)
        r.raise_for_status()
        return r.json().get("events") or []
    except Exception as e:
        log.error(f"  TheSportsDB error for team {team_id}: {e}")
        return []


def tsdb_to_match(event: dict, team_name: str) -> dict | None:
    date_str = event.get("dateEvent")
    time_str = event.get("strTime") or "00:00:00"

    if not date_str: return None

    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError: return None

    today = datetime.now(timezone.utc)
    if dt < today - timedelta(hours=6) or dt > today + timedelta(days=LOOKAHEAD_DAYS):
        return None

    return {
        "id":          f"tsdb_{event['idEvent']}",
        "utcDate":     dt.isoformat(),
        "competition": {"name": event.get("strLeague", team_name)},
        "homeTeam":    {"name": event.get("strHomeTeam", "")},
        "awayTeam":    {"name": event.get("strAwayTeam", "")},
        "stage":       event.get("strRound", ""),
    }


def collect_tsdb_matches() -> dict:
    collected = {}
    for team in TSDB_TEAMS:
        name = team["name"]
        tid  = team["id"]
        log.info(f"  Fetching from TheSportsDB: {name}...")

        events = tsdb_get_next_events(tid)
        count = 0
        for event in events:
            match = tsdb_to_match(event, name)
            if match:
                collected[match["id"]] = match
                count += 1
        log.info(f"       -> {count} match(es) within lookahead")
        time.sleep(1)
    return collected


# ------------------------------------------------------------------------------
#  GOOGLE CALENDAR
# ------------------------------------------------------------------------------

def get_display_category(match: dict) -> str:
    comp_name = match["competition"]["name"]
    home_name = match["homeTeam"]["name"]
    away_name = match["awayTeam"]["name"]

    if comp_name in DISPLAY_NAME_MAPPING:
        return DISPLAY_NAME_MAPPING[comp_name]

    sorted_keys = sorted(DISPLAY_NAME_MAPPING.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in home_name or key in away_name:
            return DISPLAY_NAME_MAPPING[key]
    return comp_name


def build_calendar_event(match: dict) -> dict:
    raw_date = match["utcDate"]
    if raw_date.endswith("Z"): raw_date = raw_date[:-1] + "+00:00"
    start_dt = datetime.fromisoformat(raw_date)
    end_dt   = start_dt + timedelta(hours=2)

    home        = match["homeTeam"]["name"]
    away        = match["awayTeam"]["name"]
    competition = match["competition"]["name"]
    category    = get_display_category(match)

    description = f"{home} vs {away}\n\nCompetition: {competition}"
    if match.get("stage"): description += f"\nStage: {match['stage']}"

    return {
        "summary":     f"⚽ {category}",
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "UTC"},
        "end":   {"dateTime": end_dt.isoformat(),   "timeZone": "UTC"},
        "colorId": EVENT_COLOR_ID,
        "reminders": {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": m} for m in REMINDERS],
        },
        "extendedProperties": {
            "private": {
                "footballMatchId": str(match["id"]),
                "addedBy":         "FootballCalendarSync",
            }
        },
    }


def sync_to_calendar(service, matches: dict) -> tuple[int, int, int]:
    added = updated = errors = 0
    log.info("  Fetching existing events for optimization...")
    existing_events = {}
    try:
        result = service.events().list(
            calendarId=CALENDAR_ID,
            privateExtendedProperty="addedBy=FootballCalendarSync",
            maxResults=2500
        ).execute()
        for item in result.get("items", []):
            m_id = item.get("extendedProperties", {}).get("private", {}).get("footballMatchId")
            if m_id: existing_events[m_id] = item["id"]
        log.info(f"  Found {len(existing_events)} existing events in calendar.")
    except Exception as e:
        log.warning(f"  Could not pre-fetch events: {e}")

    for match_id, match in matches.items():
        existing_id = existing_events.get(match_id)
        event_body  = build_calendar_event(match)
        try:
            if existing_id:
                service.events().patch(calendarId=CALENDAR_ID, eventId=existing_id, body=event_body).execute()
                log.info(f"  [UPDATED] {match['homeTeam']['name']} vs {match['awayTeam']['name']}")
                updated += 1
            else:
                service.events().insert(calendarId=CALENDAR_ID, body=event_body).execute()
                log.info(f"  [ADDED]   {match['homeTeam']['name']} vs {match['awayTeam']['name']}")
                added += 1
        except Exception as e:
            log.info(f"  [FAILED]  {match['homeTeam']['name']} vs {match['awayTeam']['name']} - {e}")
            errors += 1
    
    deleted = 0
    for m_id, event_id in existing_events.items():
        if m_id not in matches:
            try:
                service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
                deleted += 1
            except Exception as e:
                log.warning(f"  [FAILED DELETE] {m_id}: {e}")
    if deleted > 0: log.info(f"  [PURGED]  {deleted} legacy/unwanted matches from calendar.")
    return added, updated, errors


def main():
    log.info("=" * 60)
    log.info("Football Calendar Sync (Hybrid — TheSportsDB Edition)")
    log.info("=" * 60)

    service = get_calendar_service()
    
    log.info("\nFetching matches from football-data.org...")
    matches = collect_fd_matches()
    
    log.info("\nFetching matches from TheSportsDB (National Teams)...")
    tsdb_matches = collect_tsdb_matches()
    matches.update(tsdb_matches)
    
    log.info(f"\nTotal unique matches: {len(matches)}")
    if not matches:
        log.info("Nothing to sync.")
        return

    log.info("\nSyncing to Google Calendar...")
    added, updated, errors = sync_to_calendar(service, matches)

    log.info("\n" + "=" * 60)
    log.info(f"  Added:   {added}")
    log.info(f"  Updated: {updated}")
    log.info(f"  Errors:  {errors}")
    log.info("=" * 60)

if __name__ == "__main__":
    main()
