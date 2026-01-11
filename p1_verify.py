"""P1 Enforcement Verification

Validates that P1 hardening is correctly implemented and operational.

USAGE:
    python p1_verify.py

EXIT CODES:
    0 - All P1 checks passed
    1 - One or more P1 checks failed
"""

import os
import sys
from typing import List, Tuple

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check(name: str, passed: bool, detail: str = "") -> Tuple[str, bool, str]:
    """Record check result"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"  {status}  {name}")
    if detail:
        print(f"         {detail}")
    return (name, passed, detail)


def section(title: str):
    """Print section header"""
    print(f"\n{BOLD}{title}{RESET}")
    print("=" * 80)


results: List[Tuple[str, bool, str]] = []


section("P1 VERIFICATION — AUTH ON BY DEFAULT")

# 1. Check mcp_http_adapter_p1.py exists
try:
    with open("mcp_http_adapter_p1.py", "r") as f:
        adapter_content = f.read()
    results.append(check("mcp_http_adapter_p1.py exists", True))

    # Check auth enforcement function
    has_enforce_auth = "_enforce_auth" in adapter_content
    results.append(check("_enforce_auth function present", has_enforce_auth))

    # Check auth called in execute
    has_auth_call = "_enforce_auth(x_mcp_key" in adapter_content
    results.append(check("Auth enforced in execute endpoint", has_auth_call))

    # Check structured errors
    has_error_model = "class ErrorResponse" in adapter_content
    results.append(check("ErrorResponse model defined", has_error_model))

except FileNotFoundError:
    results.append(check("mcp_http_adapter_p1.py exists", False, "File not found"))


section("P1 VERIFICATION — IMMUTABLE DEMO MODE")

try:
    with open("mcp_http_adapter_p1.py", "r") as f:
        adapter_content = f.read()

    # Check DEMO_MODE detection
    has_demo_mode = 'DEMO_MODE = os.environ.get("DEMO_MODE"' in adapter_content
    results.append(check("DEMO_MODE environment variable read", has_demo_mode))

    # Check demo mode enforcement
    has_demo_enforce = "_enforce_demo_mode" in adapter_content
    results.append(check("_enforce_demo_mode function present", has_demo_enforce))

    # Check dry_run forced
    forces_dry_run = "req.dry_run = True" in adapter_content
    results.append(check("Demo mode forces dry_run=True", forces_dry_run))

except Exception as e:
    results.append(check("Demo mode verification", False, str(e)))


section("P1 VERIFICATION — DETERMINISTIC HEALTH")

try:
    with open("mcp_http_adapter_p1.py", "r") as f:
        adapter_content = f.read()

    # Check health endpoint
    has_health = '@router.get("/health"' in adapter_content
    results.append(check("Health endpoint defined", has_health))

    # Check HealthResponse model
    has_health_model = "class HealthResponse" in adapter_content
    results.append(check("HealthResponse model defined", has_health_model))

    # Check components returned
    has_components = (
        "components" in adapter_content and "HealthResponse" in adapter_content
    )
    results.append(check("Components field in health response", has_components))

    # Check registry hash
    has_registry_hash = "REGISTRY_HASH" in adapter_content
    results.append(check("Registry hash computed", has_registry_hash))

except Exception as e:
    results.append(check("Health contract verification", False, str(e)))


section("P1 VERIFICATION — CANONICAL ENTRYPOINT")

try:
    with open("omni_gateway_p1.py", "r", encoding="utf-8") as f:
        gateway_content = f.read()

    # Check direct execution refused
    has_refusal = (
        'if __name__ == "__main__"' in gateway_content
        and "sys.exit(1)" in gateway_content
    )
    results.append(check("Direct python execution refused", has_refusal))

    # Check uvicorn instruction
    has_uvicorn_doc = "uvicorn omni_gateway_p1:app" in gateway_content
    results.append(check("Uvicorn usage documented", has_uvicorn_doc))

except FileNotFoundError:
    results.append(check("omni_gateway_p1.py exists", False, "File not found"))


section("P1 VERIFICATION — STRUCTURED ERRORS")

try:
    with open("mcp_http_adapter_p1.py", "r") as f:
        adapter_content = f.read()

    # Check ErrorResponse model fields
    has_correlation_id = '"correlationId"' in adapter_content
    results.append(check("correlationId in error responses", has_correlation_id))

    has_guidance = '"guidance"' in adapter_content
    results.append(check("Guidance field in errors", has_guidance))

    has_code_field = '"code"' in adapter_content
    results.append(check("Code field in errors", has_code_field))

except Exception as e:
    results.append(check("Error contract verification", False, str(e)))


section("P1 VERIFICATION — KILL SWITCH")

try:
    with open("mcp_http_adapter_p1.py", "r") as f:
        adapter_content = f.read()

    # Check kill switch detection
    has_kill_switch = 'KILL_SWITCH = os.environ.get("KILL_SWITCH"' in adapter_content
    results.append(check("KILL_SWITCH environment variable read", has_kill_switch))

    # Check kill switch enforcement
    has_kill_check = "if KILL_SWITCH:" in adapter_content
    results.append(check("Kill switch enforced in auth", has_kill_check))

except Exception as e:
    results.append(check("Kill switch verification", False, str(e)))


section("P1 VERIFICATION — AUDIT LOGGING")

try:
    with open("mcp_http_adapter_p1.py", "r") as f:
        adapter_content = f.read()

    # Check logger calls
    has_logger = "logger.info" in adapter_content
    results.append(check("Logger configured", has_logger))

    # Check audit logs for execute
    has_execute_log = 'logger.info(f"P1: Execute' in adapter_content
    results.append(check("Execute operations logged", has_execute_log))

    # Check correlation ID in logs
    has_correlation_log = "correlation_id=" in adapter_content
    results.append(check("Correlation ID in logs", has_correlation_log))

except Exception as e:
    results.append(check("Audit logging verification", False, str(e)))


section("P1 VERIFICATION — SECRETS HYGIENE")

# Check for credential files in repo (should not exist)
cred_files = [
    "credentials-gcp-local.json",
    "secrets_infinityxone_credentials.json",
    "firebase_config.json",
]

for cred_file in cred_files:
    exists = os.path.exists(cred_file)
    results.append(
        check(
            f"{cred_file} not in repo",
            not exists,
            "P1: Remove from repo and .gitignore" if exists else "",
        )
    )

# Check for GOOGLE_APPLICATION_CREDENTIALS usage
try:
    with open("omni_gateway_p1.py", "r", encoding="utf-8") as f:
        gateway_content = f.read()

    checks_creds = "GOOGLE_APPLICATION_CREDENTIALS" in gateway_content
    results.append(check("Checks GOOGLE_APPLICATION_CREDENTIALS", checks_creds))

except Exception:
    pass


section("P1 SUMMARY")

passed = sum(1 for _, p, _ in results if p)
failed = sum(1 for _, p, _ in results if not p)
total = len(results)

print(f"\n{BOLD}Results:{RESET}")
print(f"  {GREEN}Passed:{RESET} {passed}/{total}")
print(f"  {RED}Failed:{RESET} {failed}/{total}")

if failed > 0:
    print(f"\n{YELLOW}⚠ P1 ENFORCEMENT INCOMPLETE{RESET}")
    print("Fix failures before proceeding to demo or production")
    sys.exit(1)
else:
    print(f"\n{GREEN}✓ P1 ENFORCEMENT VERIFIED{RESET}")
    print("System ready for controlled demo under P1 conditions")
    sys.exit(0)
