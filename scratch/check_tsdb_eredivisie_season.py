import requests

TSDB_BASE = "https://www.thesportsdb.com/api/v1/json/123"

# Eredivisie ID is 4337, season 2023-2024
r_events = requests.get(f"{TSDB_BASE}/eventsseason.php", params={"id": "4337", "s": "2023-2024"})
events = r_events.json().get("events") or []
print(f"Number of events for Eredivisie 2023-2024: {len(events)}")
