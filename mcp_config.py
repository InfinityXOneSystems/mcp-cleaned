"""
MCP HTTP Adapter Configuration
Loads environment variables and provides defaults for secure operation
"""

import os
from typing import Optional

# ===== MCP ADAPTER AUTH =====
MCP_API_KEY = os.environ.get("MCP_API_KEY", "default-key-change-me")
MCP_ENABLE_AUTH = os.environ.get("MCP_ENABLE_AUTH", "true").lower() == "true"
MCP_READ_ONLY = os.environ.get("MCP_READ_ONLY", "false").lower() == "true"

# ===== SECURITY =====
MCP_ALLOWED_ORIGINS = os.environ.get("MCP_ALLOWED_ORIGINS", "*").split(",")
MCP_REQUIRE_HTTPS = os.environ.get("MCP_REQUIRE_HTTPS", "false").lower() == "true"

# ===== RATE LIMITING =====
MCP_RATE_LIMIT_ENABLED = os.environ.get("MCP_RATE_LIMIT_ENABLED", "true").lower() == "true"
MCP_RATE_LIMIT_CRITICAL = int(os.environ.get("MCP_RATE_LIMIT_CRITICAL", "10"))  # per hour
MCP_RATE_LIMIT_HIGH = int(os.environ.get("MCP_RATE_LIMIT_HIGH", "100"))  # per minute
MCP_RATE_LIMIT_MEDIUM = int(os.environ.get("MCP_RATE_LIMIT_MEDIUM", "1000"))  # per hour

# ===== LOGGING =====
MCP_LOG_LEVEL = os.environ.get("MCP_LOG_LEVEL", "INFO")
MCP_LOG_EXECUTION = os.environ.get("MCP_LOG_EXECUTION", "true").lower() == "true"

# ===== FIRESTORE (Memory Backend) =====
MCP_FIRESTORE_PROJECT = os.environ.get("FIRESTORE_PROJECT", "infinity-x-one-systems")
MCP_FIRESTORE_COLLECTION = os.environ.get("FIRESTORE_COLLECTION", "mcp_memory")
MCP_USE_FIRESTORE = os.environ.get("MCP_USE_FIRESTORE", "true").lower() == "true"

# ===== CLOUD RUN DETECTION =====
MCP_RUNNING_ON_CLOUD_RUN = os.environ.get("K_SERVICE") is not None
MCP_CLOUD_RUN_REGION = os.environ.get("K_REGION", "us-east1")
MCP_CLOUD_RUN_REVISION = os.environ.get("K_REVISION", "unknown")

# ===== CUSTOM GPT COMPATIBILITY =====
# Enable Custom GPT-specific behaviors
MCP_CUSTOM_GPT_MODE = os.environ.get("MCP_CUSTOM_GPT_MODE", "true").lower() == "true"

# Custom GPT Auto-Builder expects this format
MCP_OPENAI_COMPATIBLE = True

# ===== WARNINGS & VALIDATION =====
if MCP_API_KEY == "default-key-change-me" and MCP_ENABLE_AUTH:
    import logging
    logging.warning(
        "⚠ WARNING: MCP_API_KEY is set to default value. "
        "Change MCP_API_KEY environment variable in production."
    )

if MCP_REQUIRE_HTTPS and not MCP_RUNNING_ON_CLOUD_RUN:
    import logging
    logging.debug(
        "HTTPS requirement enabled but not on Cloud Run. "
        "Some features may be unavailable."
    )


def get_config_summary() -> dict:
    """Return configuration summary for logging"""
    return {
        "auth_enabled": MCP_ENABLE_AUTH,
        "read_only": MCP_READ_ONLY,
        "rate_limiting": MCP_RATE_LIMIT_ENABLED,
        "firestore_enabled": MCP_USE_FIRESTORE,
        "custom_gpt_mode": MCP_CUSTOM_GPT_MODE,
        "cloud_run": MCP_RUNNING_ON_CLOUD_RUN,
        "region": MCP_CLOUD_RUN_REGION if MCP_RUNNING_ON_CLOUD_RUN else "local"
    }
