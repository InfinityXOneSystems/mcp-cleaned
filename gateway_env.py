"""
Centralized gateway environment loader.
Loads environment variables from real environment, `.env` file (if present),
and provides warnings for missing credentials. Designed for local dev; for
production migrate secrets to Secret Manager and set env vars in Cloud Run.
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ENV_SAMPLE = {
    "GOOGLE_APPLICATION_CREDENTIALS": "C:\\path\\to\\service-account.json",
    "FIRESTORE_PROJECT": "infinity-x-one-systems",
    "FIRESTORE_COLLECTION": "mcp_memory",
    "FRONTEND_SERVICE_URL": "https://frontend-service-...run.app",
    "GATEWAY_URL": "https://gateway-...run.app",
    "SERVICE_MODE": "single",
}


def load_dotenv_file(dotenv_path: Path):
    try:
        if not dotenv_path.exists():
            return
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith("#"):
                    continue
                if "=" not in ln:
                    continue
                k, v = ln.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception as e:
        logger.warning(f"Failed to load .env file {dotenv_path}: {e}")


def init_gateway_env():
    """Initialize environment variables for the gateway.

    Order of precedence:
    1. Existing OS environment variables
    2. `.env` file in repo root
    3. Defaults from ENV_SAMPLE (only for informational purposes)
    """
    # Load .env from repo root
    root = Path(__file__).parent
    dotenv = root / ".env"
    load_dotenv_file(dotenv)

    # Warn about important credentials
    creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set. Firestore and GCP clients will fail without credentials.")
    else:
        # normalize path
        p = Path(creds)
        if not p.exists():
            logger.warning(f"GOOGLE_APPLICATION_CREDENTIALS file not found at {creds}")

    # Provide helpful debug info (non-sensitive)
    for k in ["FIRESTORE_PROJECT", "FRONTEND_SERVICE_URL", "GATEWAY_URL", "SERVICE_MODE"]:
        v = os.environ.get(k) or ENV_SAMPLE.get(k)
        logger.debug(f"ENV {k}={v}")

    return True
