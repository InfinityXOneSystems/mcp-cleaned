"""
Firebase Integration Helper (Modular & Safe)
- Validates provided Firebase config (client JSON)
- Initializes Admin SDK if service account is available
- Exposes optional helpers for Firestore/Auth/Storage
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

# Optional imports for admin SDK
try:
    import firebase_admin
    from firebase_admin import auth, credentials, firestore, storage
except Exception:
    firebase_admin = None
    credentials = None
    firestore = None
    auth = None
    storage = None

CRED_DIR = Path.home() / "AppData/Local/InfinityXOne/CredentialManager"
LOCAL_CONFIG_PATH = CRED_DIR / "firebase-config.json"
LOCAL_SA_PATH = CRED_DIR / "firebase-admin-sa.json"


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the provided Firebase client config (not admin SA).
    Returns a report dict with fields present/missing.
    """
    report = {"valid": True, "issues": []}
    # Required top-level keys
    required_top = ["project_info", "client", "configuration_version"]
    for key in required_top:
        if key not in config:
            report["valid"] = False
            report["issues"].append(f"missing key: {key}")
    # project_info
    pi = config.get("project_info", {})
    for k in ["project_number", "project_id"]:
        if k not in pi:
            report["valid"] = False
            report["issues"].append(f"missing project_info.{k}")
    # client/api_key current_key
    try:
        api_key = config["client"][0]["api_key"][0]["current_key"]
        if not (isinstance(api_key, str) and api_key.startswith("AIza")):
            report["issues"].append("api_key.current_key format unexpected")
    except Exception:
        report["valid"] = False
        report["issues"].append("missing client[0].api_key[0].current_key")
    return report


def save_config_locally(config: Dict[str, Any]) -> str:
    CRED_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOCAL_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return str(LOCAL_CONFIG_PATH)


def init_admin() -> Optional[firebase_admin.App]:
    """Initialize Firebase Admin if service account JSON is present.
    Returns the app or None if not initialized.
    """
    if firebase_admin is None:
        return None
    if LOCAL_SA_PATH.exists():
        try:
            cred = credentials.Certificate(str(LOCAL_SA_PATH))
            if not firebase_admin._apps:
                return firebase_admin.initialize_app(cred)
            return list(firebase_admin._apps.values())[0]
        except Exception:
            return None
    return None


def get_db():
    return firestore.client() if firestore else None


def get_auth():
    return auth if auth else None


def get_bucket() -> Optional[storage.bucket.Bucket]:
    return storage.bucket() if storage else None


def quick_status() -> Dict[str, Any]:
    """Return a quick status snapshot for tests."""
    cfg_exists = LOCAL_CONFIG_PATH.exists()
    sa_exists = LOCAL_SA_PATH.exists()
    admin_app = init_admin()
    return {
        "config_path": str(LOCAL_CONFIG_PATH),
        "config_exists": cfg_exists,
        "sa_path": str(LOCAL_SA_PATH),
        "sa_exists": sa_exists,
        "admin_initialized": admin_app is not None,
    }


if __name__ == "__main__":
    # Local smoke test
    try:
        config = json.load(open("firebase_config.json", "r", encoding="utf-8"))
        rep = validate_config(config)
        print("Validation:", rep)
        p = save_config_locally(config)
        print("Saved to:", p)
        print("Status:", quick_status())
    except Exception as e:
        print("Error:", e)
