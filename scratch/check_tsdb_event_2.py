import requests
import json

TSDB_BASE = "https://www.thesportsdb.com/api/v1/json/123"
r = requests.get(f"{TSDB_BASE}/lookupevent.php", params={"id": "2454917"})
print(json.dumps(r.json(), indent=2))
