import json
import os
from datetime import datetime


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def write_json_record(base_dir: str, relative_dir: str, base_name: str, payload: dict) -> str:
    """Write a timestamped JSON record under base_dir/relative_dir/base_name_YYYYMMDD_HHMMSS.json"""
    ensure_dir(os.path.join(base_dir, relative_dir))
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{base_name}_{ts}.json"
    out_path = os.path.join(base_dir, relative_dir, file_name)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    # Also write/update latest.json
    latest_path = os.path.join(base_dir, relative_dir, "latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return out_path
