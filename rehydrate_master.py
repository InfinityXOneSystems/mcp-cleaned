"""
rehydrate_master.py

Creates a comprehensive rehydrate manifest for the MCP system and provides
CLI entrypoints to write the manifest locally and to Firestore. Also contains
the master agentic orchestrator system prompt string to be used by orchestration
agents.

Usage:
  python rehydrate_master.py               # writes local file only
  python rehydrate_master.py --write-firestore
  python rehydrate_master.py --write-firestore --update-checklist

The script intentionally does not print secret contents. It reads
`GOOGLE_APPLICATION_CREDENTIALS` from the environment if present, or you can
set it in the shell before running. Firestore project defaults to
`infinity-x-one-systems` unless `FIRESTORE_PROJECT` is set in the environment.
"""
from __future__ import annotations
import os
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List
import logging
import socket

try:
    from google.cloud import firestore
    from google.api_core.exceptions import GoogleAPIError
    GCLOUD_AVAILABLE = True
except Exception:
    GCLOUD_AVAILABLE = False

import urllib.request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rehydrate_master")

# Defaults and configuration
FIRESTORE_PROJECT = os.environ.get('FIRESTORE_PROJECT') or os.environ.get('FIRESTORE_PROJECT_ID') or 'infinity-x-one-systems'
FIRESTORE_COLLECTION = os.environ.get('FIRESTORE_COLLECTION', 'mcp_memory')
LOCAL_MANIFEST_PATH = os.path.join(os.path.dirname(__file__), 'rehydrate_manifest.json')
DEFAULT_GATEWAY_URL = os.environ.get('GATEWAY_URL') or 'https://gateway-896380409704.us-east1.run.app'


def build_system_index() -> List[Dict[str, Any]]:
    """Return a system index gathered from repository conventions and known files."""
    repo_root = os.path.abspath(os.path.dirname(__file__))
    index = []
    index.append({
        'name': 'Omni Gateway',
        'file': 'omni_gateway.py',
        'description': 'FastAPI wrapper exposing MCP tools, cockpit UI, and Firestore-backed memory (PROTOCOL_110).',
        'entrypoint': 'uvicorn omni_gateway:app'
    })
    index.append({
        'name': 'Cockpit UI',
        'file': 'cockpit.html',
        'description': 'Browser UI for intelligence cockpit served by Omni Gateway.'
    })
    index.append({
        'name': 'Background Build Runner',
        'file': 'background_build_runner.py',
        'description': 'Submits Cloud Build jobs asynchronously for iterative builds.'
    })
    index.append({
        'name': 'Inspect Firestore',
        'file': 'inspect_firestore.py',
        'description': 'Utility to list collections and confirm Firestore persistence.'
    })
    index.append({
        'name': 'CI/CD',
        'file': 'cloudbuild.yaml',
        'description': 'Cloud Build pipeline building image and deploying to Cloud Run in us-east1.'
    })
    return index


def build_manifest() -> Dict[str, Any]:
    now = datetime.utcnow().isoformat() + 'Z'
    manifest = {
        'manifest_version': '1.0',
        'generated_at': now,
        'project_id': FIRESTORE_PROJECT,
        'region': 'us-east1',
        'artifact_registry': {
            'repo': 'mcp-east',
            'path_example': 'us-east1-docker.pkg.dev/infinity-x-one-systems/mcp-east/gateway:latest'
        },
        'systems_index': build_system_index(),
        'location_notes': 'Primary cloud region: us-east1. Local workspace path: ' + os.path.abspath(os.path.dirname(__file__)),
        'how_it_works': (
            'Omni Gateway (FastAPI) exposes MCP tools and stores runtime memory in Firestore. ' 
            'On startup the gateway attempts to rehydrate protocol state into Firestore under collection `mcp_memory`.'
        ),
        'vision': 'Provide always-on orchestration and an intelligence cockpit that can rehydrate critical runtime memory on boot and enable governed autonomous operations.',
        'roadmap': [
            {'phase': 'stabilize', 'tasks': ['credentials management', 'persistent memory validation', 'monitoring']},
            {'phase': 'scale', 'tasks': ['multi-region artifact registry', 'high-availability Cloud Run', 'automated failover']},
            {'phase': 'automate', 'tasks': ['agentic orchestrator', 'policy-based governance', 'self-healing workflows']}
        ],
        'memory_locations': {
            'firestore': f'project={FIRESTORE_PROJECT} collection={FIRESTORE_COLLECTION} document=protocol_110',
            'local_sqlite': 'mcp_memory.db (used by worker processes if configured)'
        },
        'ai_stack': [
            'MCP tool orchestration (mcp package)',
            'OpenAI/ChatGPT integrations via MCP',
            'Optional local models via transformers or ONNX depending on deployment'
        ],
        'tech_stack': [
            'Python 3.12',
            'FastAPI + Uvicorn',
            'google-cloud-firestore',
            'httpx / urllib',
            'Cloud Build, Artifact Registry, Cloud Run'
        ],
        'tool_stack': [
            'gcloud', 'docker', 'cloud-build-local', 'Artifact Registry', 'Secret Manager', 'Firestore'
        ],
        'attached_apps': [
            {'name': 'Frontend Service', 'url': DEFAULT_GATEWAY_URL},
            {'name': 'Cloud Run Gateway', 'url': 'https://gateway-896380409704.us-east1.run.app'},
            {'name': 'MCP Server', 'file': 'main_extended.py (optional on host)'}
        ],
        'env_samples': {
            'GOOGLE_APPLICATION_CREDENTIALS': 'C:\\Users\\JARVIS\\AppData\\Local\\InfinityXOne\\CredentialManager\\workspace-sa.json',
            'FIRESTORE_PROJECT': FIRESTORE_PROJECT,
            'FIRESTORE_COLLECTION': FIRESTORE_COLLECTION,
            'FRONTEND_SERVICE_URL': DEFAULT_GATEWAY_URL
        },
        'folder_paths': {
            'workspace_root': os.path.abspath(os.path.dirname(__file__)),
            'credential_manager': os.path.expandvars(r'%USERPROFILE%\\AppData\\Local\\InfinityXOne\\CredentialManager')
        },
        'code_type': 'python (FastAPI, workers, scripts)',
        'omni_gateway_description': 'See omni_gateway.py — exposes cockpit UI, MCP tool endpoints, and persistent memory rehydrate logic (PROTOCOL_110).',
        'manifest_notes': 'This manifest is intended for rehydrate + operational onboarding. Do not store private keys here.'
    }
    # Include the master invocation / orchestrator prompt (agentic system prompt)
    manifest['agentic_orchestrator_prompt'] = build_orchestrator_prompt()

    # Include boot agent prompt from file if available (user-provided BOOT_AGENT_PROMPT.txt)
    try:
        boot_prompt_path = os.path.join(os.path.dirname(__file__), 'BOOT_AGENT_PROMPT.txt')
        if os.path.exists(boot_prompt_path):
            with open(boot_prompt_path, 'r', encoding='utf-8') as bp:
                manifest['boot_agent_prompt'] = bp.read()
    except Exception:
        logger.exception('Failed to read BOOT_AGENT_PROMPT.txt (ignored)')
    return manifest


def build_orchestrator_prompt() -> str:
    """Return a long-form system prompt for a master agentic orchestrator.

    The prompt below is intentionally explicit about governance, safety,
    and allowed non-destructive defaults.
    """
    prompt = (
        "SYSTEM: You are the Infinity X One Master Orchestrator. Your primary goal is to bring the system to a safe, operational state and maintain it. "
        "You have access to a catalog of tools (MCP tools), the Omni Gateway HTTP API, and a persistent memory store (Firestore).\n\n"
        "Rules: \n"
        "- Always prefer non-destructive actions. If an action is non-destructive and safe, assume YES by default. If destructive, require explicit user confirmation.\n"
        "- All privileged actions must be logged and auditable. Do not print or exfiltrate secret values.\n"
        "- Respect governance checks provided by the MCP server; if a governance check blocks an action, escalate to the human operator.\n"
        "- Verify environment (credentials, Firestore writeability, service endpoints) before attempting persistence.\n\n"
        "Startup behavior: \n"
        "1) Ensure Application Default Credentials are present and valid.\n"
        "2) Rehydrate the `protocol_110` document under collection `mcp_memory`.\n"
        "3) Run health checks against the Cloud Run gateway and frontend.\n"
        "4) Update the launch checklist in Firestore with observed statuses.\n\n"
        "If any step fails, provide a short remediation plan and do not attempt destructive remediation without human approval.\n"
        "When finished, summarize changes and the updated checklist, and await further instructions."
    )
    return prompt


def write_local_manifest(manifest: Dict[str, Any], path: str = LOCAL_MANIFEST_PATH) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    logger.info('Wrote local manifest to %s', path)


def init_firestore_client() -> 'firestore.Client | None':
    if not GCLOUD_AVAILABLE:
        logger.warning('google-cloud package not available; Firestore operations disabled')
        return None
    try:
        client = firestore.Client(project=FIRESTORE_PROJECT)
        logger.info('Connected to Firestore project=%s', FIRESTORE_PROJECT)
        return client
    except GoogleAPIError as e:
        logger.error('Firestore API error: %s', e)
        return None
    except Exception as e:
        logger.error('Failed to initialize Firestore client: %s', e)
        return None


def write_manifest_to_firestore(manifest: Dict[str, Any], client: 'firestore.Client') -> bool:
    try:
        doc_ref = client.collection(FIRESTORE_COLLECTION).document('rehydrate_master_manifest')
        doc_ref.set(manifest)
        logger.info('Manifest written to Firestore/%s/rehydrate_master_manifest', FIRESTORE_COLLECTION)
        return True
    except Exception as e:
        logger.error('Failed to write manifest to Firestore: %s', e)
        return False


def check_gateway(url: str, timeout: int = 8) -> bool:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'rehydrate-check/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def update_protocol_checklist(client: 'firestore.Client', mark: Dict[str, str]) -> bool:
    try:
        doc_ref = client.collection(FIRESTORE_COLLECTION).document('protocol_110')
        doc = doc_ref.get()
        if not doc.exists:
            logger.warning('protocol_110 not found in Firestore; skipping checklist update')
            return False
        data = doc.to_dict() or {}
        checklist = data.get('checklist', [])
        for item in checklist:
            if item.get('id') in mark:
                item['status'] = mark[item['id']]
        doc_ref.set({'checklist': checklist}, merge=True)
        logger.info('protocol_110 checklist updated in Firestore')
        return True
    except Exception as e:
        logger.error('Failed to update protocol checklist: %s', e)
        return False


def main():
    parser = argparse.ArgumentParser(description='Rehydrate master manifest and optionally persist to Firestore')
    parser.add_argument('--write-firestore', action='store_true', help='Write manifest to Firestore')
    parser.add_argument('--update-checklist', action='store_true', help='Update protocol_110 checklist in Firestore based on checks')
    parser.add_argument('--gateway-url', default=DEFAULT_GATEWAY_URL, help='Gateway URL to check')
    args = parser.parse_args()

    manifest = build_manifest()
    write_local_manifest(manifest)

    client = None
    wrote = False
    if args.write_firestore:
        client = init_firestore_client()
        if client:
            wrote = write_manifest_to_firestore(manifest, client)

    # Run basic checks and optionally update protocol checklist
    checks = {
        'gateway_reachable': check_gateway(args.gateway_url),
        'firestore_write': bool(wrote)
    }

    logger.info('Checks: %s', checks)

    if args.update_checklist and client:
        # Map check results to checklist IDs
        mark = {}
        if checks['gateway_reachable']:
            mark['c3'] = 'completed'  # Cloud Run deployed
            mark['c4'] = 'completed'  # Health endpoints responding
        if checks['firestore_write']:
            mark['c6'] = 'completed'  # Firestore memory writable
        if mark:
            update_protocol_checklist(client, mark)

    # Summary output (no secrets)
    summary = {
        'local_manifest': LOCAL_MANIFEST_PATH,
        'wrote_to_firestore': wrote,
        'firestore_project': FIRESTORE_PROJECT,
        'gateway_checked': args.gateway_url,
        'gateway_up': checks['gateway_reachable']
    }
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
