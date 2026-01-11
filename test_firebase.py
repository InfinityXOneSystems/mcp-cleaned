import json

from firebase_helper import quick_status, save_config_locally, validate_config

print("\n=== FIREBASE VALIDATION TEST ===")
try:
    cfg = json.load(open("firebase_config.json", "r", encoding="utf-8"))
    report = validate_config(cfg)
    print("Report:", report)
    path = save_config_locally(cfg)
    print("Saved:", path)
    status = quick_status()
    print("Status:", status)
    print("\n✅ Firebase validation complete")
except Exception as e:
    print("❌ Error:", e)
