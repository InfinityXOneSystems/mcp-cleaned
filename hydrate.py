import json
import os
from datetime import datetime

import httpx

# Config (can be overridden by env)
OWNER_NAME = os.environ.get("OWNER_NAME", "Neo")
ORG_NAME = os.environ.get("ORG_NAME", "Infinity X One Systems")
PRIMARY_REGION = os.environ.get("PRIMARY_REGION", "us-east1")
TIMEZONE = os.environ.get("TIMEZONE", "America/New_York")

MCP_AGENT_BASE = os.environ.get(
    "MCP_AGENT_BASE", "https://mcp-agent-896380409704.us-east1.run.app"
)
MEMORY_GATEWAY_BASE = os.environ.get(
    "MEMORY_GATEWAY_BASE", "https://memory-gateway-896380409704.us-east1.run.app"
)
ORCHESTRATOR_BASE = os.environ.get(
    "ORCHESTRATOR_BASE", "https://orchestrator-896380409704.us-east1.run.app"
)

SECRET_NAME = os.environ.get(
    "GCP_SA_SECRET", "projects/896380409704/secrets/workspace-sa-json"
)
MCP_API_KEY = os.environ.get("MCP_API_KEY")

HEADERS = {}
if MCP_API_KEY:
    HEADERS["Authorization"] = f"Bearer {MCP_API_KEY}"

client = httpx.Client(timeout=20.0)


def call(url, method="GET", json_body=None, allow_404=False):
    try:
        if method == "GET":
            r = client.get(url, headers=HEADERS)
        else:
            r = client.post(url, headers=HEADERS, json=json_body)
        if r.status_code == 404 and allow_404:
            return None
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return r.text
    except Exception as e:
        return {
            "__error": str(e),
            "status_code": (
                getattr(e, "response", None).status_code
                if getattr(e, "response", None) is not None
                else None
            ),
        }


def load_service_account():
    url = f"{MCP_AGENT_BASE}/gcp/load_service_account"
    body = {"secret_name": SECRET_NAME}
    print("-> Loading service account from Secret Manager via MCP...")
    res = call(url, method="POST", json_body=body)
    return res


def load_github_app_config():
    """Load GitHub App configuration from Secret Manager"""
    url = f"{MCP_AGENT_BASE}/gcp/get_secret"
    body = {"secret_name": "projects/896380409704/secrets/github-app-config"}
    print("-> Loading GitHub App config from Secret Manager...")
    res = call(url, method="POST", json_body=body, allow_404=True)
    if res and "__error" not in res:
        return json.loads(res.get("data", "{}"))
    return None


def load_github_app_private_key():
    """Load GitHub App private key from Secret Manager"""
    url = f"{MCP_AGENT_BASE}/gcp/get_secret"
    body = {"secret_name": "projects/896380409704/secrets/github-app-private-key"}
    print("-> Loading GitHub App private key from Secret Manager...")
    res = call(url, method="POST", json_body=body, allow_404=True)
    if res and "__error" not in res:
        return res.get("data", "")
    return None


def save_github_credentials():
    """Save GitHub App credentials locally"""
    cred_dir = os.path.expanduser(
        "C:/Users/JARVIS/AppData/Local/InfinityXOne/CredentialManager"
    )
    os.makedirs(cred_dir, exist_ok=True)

    # Load GitHub App config
    app_config = load_github_app_config()
    if app_config:
        config_path = os.path.join(cred_dir, ".github-app-config.json")
        with open(config_path, "w") as f:
            json.dump(app_config, f, indent=2)
        print(f"  ✓ GitHub App config saved: {config_path}")

    # Load GitHub App private key
    private_key = load_github_app_private_key()
    if private_key:
        key_path = os.path.join(cred_dir, "github-app-private-key.pem")
        with open(key_path, "w") as f:
            f.write(private_key)
        print(f"  ✓ GitHub App private key saved: {key_path}")

    return app_config, private_key


def hydrate_memory():
    # try /recall then /memory/rehydrate
    url1 = f"{MEMORY_GATEWAY_BASE}/recall"
    url2 = f"{MEMORY_GATEWAY_BASE}/memory/rehydrate"
    print("-> Attempting memory recall from MEMORY_GATEWAY...")
    res = call(url1, method="POST", json_body={"owner": OWNER_NAME}, allow_404=True)
    if res is None:
        res = call(
            url2,
            method="POST",
            json_body={"namespace": "default", "limit": 20},
            allow_404=True,
        )
    return res


def discover_mcp():
    info = {}
    print("-> Checking MCP health and info...")
    info["health"] = call(f"{MCP_AGENT_BASE}/health", "GET", allow_404=True)
    info["info"] = call(f"{MCP_AGENT_BASE}/info", "GET", allow_404=True)
    # try tools endpoint
    info["tools"] = call(f"{MCP_AGENT_BASE}/tools", "GET", allow_404=True)
    return info


def validate_orchestrator():
    print("-> Validating Orchestrator")
    o = {}
    o["health"] = call(f"{ORCHESTRATOR_BASE}/health", "GET", allow_404=True)
    o["info"] = call(f"{ORCHESTRATOR_BASE}/info", "GET", allow_404=True)
    # probe execute endpoint
    o["execute_probe"] = call(
        f"{ORCHESTRATOR_BASE}/execute",
        "POST",
        json_body={"probe": True},
        allow_404=True,
    )
    return o


def load_firebase_config():
    """Load Firebase client config from Secret Manager"""
    url = f"{MCP_AGENT_BASE}/gcp/get_secret"
    body = {"secret_name": "projects/896380409704/secrets/firebase-config"}
    print("-> Loading Firebase config from Secret Manager...")
    res = call(url, method="POST", json_body=body, allow_404=True)
    if res and "__error" not in res:
        try:
            return json.loads(res.get("data", "{}"))
        except Exception:
            return None
    return None


def load_gemini_key():
    """Load Gemini API key from Secret Manager"""
    url = f"{MCP_AGENT_BASE}/gcp/get_secret"
    body = {"secret_name": "projects/896380409704/secrets/gemini-api-key"}
    print("-> Loading Gemini API key from Secret Manager...")
    res = call(url, method="POST", json_body=body, allow_404=True)
    if res and "__error" not in res:
        return res.get("data", "")
    return None


def save_firebase_credentials():
    """Save Firebase config and Gemini key locally (CredentialManager)"""
    cred_dir = os.path.expanduser(
        "C:/Users/JARVIS/AppData/Local/InfinityXOne/CredentialManager"
    )
    os.makedirs(cred_dir, exist_ok=True)
    saved = {"config": False, "gemini": False}

    fb_cfg = load_firebase_config()
    if fb_cfg:
        cfg_path = os.path.join(cred_dir, "firebase-config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(fb_cfg, f, indent=2)
        print(f"  ✓ Firebase config saved: {cfg_path}")
        saved["config"] = True

    gemini = load_gemini_key()
    if gemini:
        env_path = os.path.join(cred_dir, ".env.firebase")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(f"GEMINI_KEY={gemini}\n")
        print(f"  ✓ Gemini key saved: {env_path}")
        saved["gemini"] = True

    return saved


def load_openai_key():
    url = f"{MCP_AGENT_BASE}/gcp/get_secret"
    body = {"secret_name": "projects/896380409704/secrets/openai-api-key"}
    print("-> Loading OpenAI API key from Secret Manager...")
    res = call(url, method="POST", json_body=body, allow_404=True)
    if res and "__error" not in res:
        return res.get("data", "")
    return None


def save_openai_credentials():
    cred_dir = os.path.expanduser(
        "C:/Users/JARVIS/AppData/Local/InfinityXOne/CredentialManager"
    )
    os.makedirs(cred_dir, exist_ok=True)
    key = load_openai_key()
    if key:
        env_path = os.path.join(cred_dir, ".env.openai")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(f"OPENAI_API_KEY={key}\n")
        print(f"  ✓ OpenAI key saved: {env_path}")
        return {"key_saved": True}
    return {"key_saved": False}


def load_hostinger_key():
    """Load Hostinger API key from Secret Manager"""
    url = f"{MCP_AGENT_BASE}/gcp/get_secret"
    body = {"secret_name": "projects/896380409704/secrets/hostinger-api-key"}
    print("-> Loading Hostinger API key from Secret Manager...")
    res = call(url, method="POST", json_body=body, allow_404=True)
    if res and "__error" not in res:
        return res.get("data", "")
    return None


def save_hostinger_credentials():
    """Save Hostinger API key locally (CredentialManager)"""
    cred_dir = os.path.expanduser(
        "C:/Users/JARVIS/AppData/Local/InfinityXOne/CredentialManager"
    )
    os.makedirs(cred_dir, exist_ok=True)
    key = load_hostinger_key()
    if key:
        env_path = os.path.join(cred_dir, ".env.hostinger")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(f"HOSTINGER_API_KEY={key}\n")
        print(f"  ✓ Hostinger key saved: {env_path}")
        return {"key_saved": True}
    return {"key_saved": False}


def main():
    summary = {"hydration_time": datetime.utcnow().isoformat() + "Z"}
    print("\n===== INFINITY XOS HYDRATOR START =====")
    # STEP 1: load SA
    sa = load_service_account()
    summary["service_account"] = sa

    # STEP 2: hydrate memory
    mem = hydrate_memory()
    summary["memory"] = mem

    # STEP 3: discover MCP
    mcp = discover_mcp()
    summary["mcp"] = mcp

    # STEP 4: validate orchestrator
    orch = validate_orchestrator()
    summary["orchestrator"] = orch

    # STEP 5: hydrate GitHub App credentials
    print("-> Hydrating GitHub App credentials...")
    github_app_config, github_app_key = save_github_credentials()
    summary["github_app"] = {
        "config_loaded": github_app_config is not None,
        "key_loaded": github_app_key is not None,
    }

    # STEP 6: hydrate Firebase credentials
    print("-> Hydrating Firebase credentials...")
    fb_saved = save_firebase_credentials()
    summary["firebase"] = fb_saved

    # STEP 7: hydrate Hostinger credentials
    print("-> Hydrating Hostinger credentials...")
    host_saved = save_hostinger_credentials()
    summary["hostinger"] = host_saved

    # Build Hydration Summary
    print("\n[Hydration Summary]")
    print(f"Owner: {OWNER_NAME}")
    if isinstance(mem, dict) and "objectives" in mem:
        objs = mem.get("objectives")
        print(f"- Objectives: {len(objs) if objs else 0}")
    else:
        print(f"- Memory load: {('ok' if mem else 'none')}")
    print(f"- MCP health: {mcp.get('health')}")
    print(f"- Orchestrator health: {orch.get('health')}")

    # Executive answer: choose one high-leverage outcome
    print("\n[Executive Answer]")
    print(
        "- Start targeted crawls on PlatinumFunding_SeedData (high priority seeds) and run rapid NLP urgency scoring"
    )

    # Print 3 futures placeholder
    print("\n[3 Futures]")
    print(
        "FUTURE A (Best): Rapid ingestion -> high urgency leads -> outreach pipeline seeded (7d)"
    )
    print("FUTURE B (Base): Mixed signal; need tuning and dedupe (7-14d)")
    print("FUTURE C (Fail): Crawl noise, low precision; tune keywords and sources")

    # Decision table minimal
    print("\n[Decision Table]")
    print(
        "Decision: Run Platinum seed crawls | Pros: immediate data | Cons: noise | Cost: compute | Time-to-impact: hours | Confidence: 70"
    )

    # Actions to execute
    print("\n[Actions I will execute via MCP/Orchestrator]")
    print("- Enqueue crawl jobs for seeds (using /jobs/enqueue on MCP if available)")
    print(
        "- Start crawler worker (local) and monitor results into memory namespace platinum_crawls"
    )

    # Output the structured JSON summary into file
    out_path = os.path.join(os.getcwd(), "hydrate_summary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nHydration summary written to {out_path}")
    print("===== HYDRATOR COMPLETE =====\n")


if __name__ == "__main__":
    main()
