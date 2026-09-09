import requests
import json

TSDB_BASE = "https://www.thesportsdb.com/api/v1/json/123"

# Query events for season
r_events = requests.get(f"{TSDB_BASE}/eventsseason.php", params={"id": "5840", "s": "2026-2027"})
events = r_events.json().get("events") or []
print(f"Number of events: {len(events)}")
for e in events[:10]:
    print(f"- {e.get('strEvent')} (Teams: {e.get('idHomeTeam')} vs {e.get('idAwayTeam')}) on {e.get('dateEvent')} {e.get('strTime')}")
