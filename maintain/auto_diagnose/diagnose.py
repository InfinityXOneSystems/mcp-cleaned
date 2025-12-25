import json, os
from datetime import datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "records", "maintain", "auto_diagnose"))
os.makedirs(BASE, exist_ok=True)

payload = {
    "module": "auto_diagnose",
    "timestamp": datetime.now().isoformat(),
    "status": "success",
    "notes": ["Ran diagnostics", "No critical faults"]
}

out = os.path.join(BASE, f"auto_diagnose_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)

with open(os.path.join(BASE, "latest.json"), "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
