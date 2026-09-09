import requests
import json

TSDB_BASE = "https://www.thesportsdb.com/api/v1/json/123"

# Search team Liverpool
r_team = requests.get(f"{TSDB_BASE}/searchteams.php", params={"t": "Liverpool"})
teams = r_team.json().get("teams") or []
if teams:
    liverpool_id = teams[0]["idTeam"]
    print(f"Liverpool ID: {liverpool_id}")
    
    # Get next events
    r_events = requests.get(f"{TSDB_BASE}/eventsnext.php", params={"id": liverpool_id})
    events = r_events.json().get("events") or []
    print(f"Number of next events: {len(events)}")
    for e in events[:5]:
        print(f"- {e.get('strEvent')} on {e.get('dateEvent')} {e.get('strTime')}")
else:
    print("Liverpool not found")
