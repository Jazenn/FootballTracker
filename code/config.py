"""
Football Calendar - Configuration (HYBRID MODEL)
================================================
This configuration uses:
1. football-data.org (Free Plan) -> Major Leagues & Men's National Teams.
2. TheSportsDB (Free) -> Women & U21 National Teams & Friendlies.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file (looked up from root)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# ─── API Keys ──────────────────────────────────────────────────────────────────
FOOTBALL_DATA_KEY = os.getenv("API_FOOTBALL_DATA") or os.getenv("FOOTBALL_DATA_KEY")

# ─── Lookahead window ──────────────────────────────────────────────────────────
LOOKAHEAD_DAYS = 60

# ─── Primary: football-data.org (Free & Current) ───────────────────────────────
FD_COMPETITIONS = [
    "CL",   # UEFA Champions League
    "EC",   # European Championship
    "WC",   # World Cup
]

# Club IDs for football-data.org
FD_TEAMS = [
    {"id": 64,  "name": "Liverpool FC"},
]

# National Team IDs for football-data.org
FD_NATIONAL_TEAMS = [
    {"id": 8,   "name": "Netherlands (Men)"},
]

# ─── Secondary: TheSportsDB Teams (Free) ───────────────────────
# Used for teams not covered well by football-data.org (Women, O21, Friendlies)
TSDB_TEAMS = [
    {"id": 133905, "name": "Elftal mannen"},
    {"id": 136818, "name": "Elftal vrouwen"},
    {"id": 140210, "name": "Elftal O21"},
]

# ─── Display Name Mapping ──────────────────────────────────────────────────────
# Maps internal names to your preferred Dutch titles after the ⚽ emoji.
DISPLAY_NAME_MAPPING = {
    "UEFA Champions League": "Champions League",
    "Premier League":         "Premier League",
    "Eredivisie":             "Eredivisie",
    "Netherlands":           "Elftal mannen",
    "Netherlands (Men)":      "Elftal mannen",
    "Elftal mannen":         "Elftal mannen",
    "Netherlands Women":     "Elftal vrouwen",
    "Elftal vrouwen":        "Elftal vrouwen",
    "Netherlands U21":       "Elftal O21",
    "Elftal O21":            "Elftal O21",
    "Jong Oranje":           "Elftal O21",
}

# ─── Google Calendar settings ──────────────────────────────────────────────────
CALENDAR_ID = "griffioen.jason@gmail.com"
EVENT_COLOR_ID = "6"  # Tangerine (orange)

REMINDERS = [
    180,    # 3 hours before
    15,     # 15 minutes before
]

# ─── Custom Matches / Manual Overrides ─────────────────────────────────────────
# You can manually specify matches here that are not in the APIs (e.g. closed-door friendlies).
# Example format:
# CUSTOM_MATCHES = [
#     {
#         "id":          "custom_uzbekistan_2026",
#         "utcDate":     "2026-06-08T18:45:00Z",
#         "competition": {"name": "International Friendlies"},
#         "homeTeam":    {"name": "Netherlands"},
#         "awayTeam":    {"name": "Uzbekistan"},
#         "stage":       "Friendly",
#     }
# ]
CUSTOM_MATCHES = []

