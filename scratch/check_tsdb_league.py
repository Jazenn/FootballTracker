import requests
import json

TSDB_BASE = "https://www.thesportsdb.com/api/v1/json/123"

# Get next events for League 5840 (Womens World Cup Qualifying UEFA)
r_events = requests.get(f"{TSDB_BASE}/eventsnextleague.php", params={"id": "5840"})
events = r_events.json().get("events") or []
print(f"Number of next events for League 5840: {len(events)}")
for e in events[:5]:
    print(f"- {e.get('strEvent')} (Teams: {e.get('idHomeTeam')} vs {e.get('idAwayTeam')}) on {e.get('dateEvent')} {e.get('strTime')}")
