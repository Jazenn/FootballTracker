"""
Team & League ID Finder
========================
Look up team or league IDs on API-Football (api-sports.io).

Usage:
  python find_team_id.py <team name>
  python find_team_id.py --leagues <country>

Examples:
  python find_team_id.py Netherlands
  python find_team_id.py Liverpool
  python find_team_id.py --leagues Netherlands
  python find_team_id.py --leagues England
"""

import sys
import requests
from config import API_FOOTBALL_KEY

BASE    = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}


def search_teams(query: str):
    print(f"\nSearching teams for '{query}'...\n")
    try:
        r = requests.get(f"{BASE}/teams", headers=HEADERS, params={"search": query}, timeout=15)
        r.raise_for_status()
        results = r.json().get("response", [])
    except Exception as e:
        print(f"Error: {e}")
        return

    if not results:
        print("  No results found. Try a shorter search term.")
        return

    print(f"  {'ID':<8} {'Name':<40} {'Country'}")
    print(f"  {'-'*8} {'-'*40} {'-'*20}")
    for item in results:
        t = item.get("team", {})
        print(f"  {t.get('id',''):<8} {t.get('name',''):<40} {t.get('country','')}")


def search_leagues(country: str):
    print(f"\nSearching leagues for country '{country}'...\n")
    try:
        r = requests.get(f"{BASE}/leagues", headers=HEADERS, params={"country": country}, timeout=15)
        r.raise_for_status()
        results = r.json().get("response", [])
    except Exception as e:
        print(f"Error: {e}")
        return

    if not results:
        print("  No results found.")
        return

    print(f"  {'ID':<8} {'Name':<40} {'Type'}")
    print(f"  {'-'*8} {'-'*40} {'-'*15}")
    for item in results:
        lg = item.get("league", {})
        print(f"  {lg.get('id',''):<8} {lg.get('name',''):<40} {lg.get('type','')}")


def main():
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(0)

    if args[0] == "--leagues":
        country = " ".join(args[1:]) if len(args) > 1 else ""
        if not country:
            print("Please provide a country name, e.g.: python find_team_id.py --leagues Netherlands")
            sys.exit(1)
        search_leagues(country)
    else:
        search_teams(" ".join(args))


if __name__ == "__main__":
    main()
