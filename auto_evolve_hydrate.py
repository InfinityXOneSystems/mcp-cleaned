"""
auto_evolve_hydrate.py

Auto-adaptive rehydrate + evolve script for the MCP repo.

Features:
 - Scans repository for key documents and builds a doc index (file path, sha1, mtime)
 - Merges with systems index and manifest (rehydrate_manifest.json)
 - Persists manifest and doc index to Firestore (optional; requires ADC or GOOGLE_APPLICATION_CREDENTIALS)
 - Optional Google Calendar sync: create a calendar event for the next action (requires Calendar API access)
 - Interactive todo list stored in Firestore collection `mcp_todos` (add/list/complete tasks)
 - Dry-run mode and careful non-destructive defaults

Usage examples:
  python auto_evolve_hydrate.py --scan --show-manifest
  python auto_evolve_hydrate.py --scan --write-firestore --sync-calendar
  python auto_evolve_hydrate.py --interactive-todos

Notes:
 - The script avoids printing secret values. Credentials must be provided via ADC or
   environment variable `GOOGLE_APPLICATION_CREDENTIALS` for Firestore and Calendar operations.
 - Calendar sync uses a service account or OAuth client; domain delegation may be required
   to write to a specific user's calendar. The script will skip calendar sync if libs/credentials are missing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    from google.cloud import firestore

    GCLOUD = True
except Exception:
    GCLOUD = False

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    GCAL = True
except Exception:
    GCAL = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auto_evolve_hydrate")

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
MANIFEST_PATH = os.path.join(REPO_ROOT, "rehydrate_manifest.json")
FIRESTORE_PROJECT = os.environ.get("FIRESTORE_PROJECT") or "infinity-x-one-systems"
FIRESTORE_COLLECTION = os.environ.get("FIRESTORE_COLLECTION") or "mcp_memory"


def sha1_of_file(path: str) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def scan_docs(paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Scan repo for docs of interest and return index entries.
    If `paths` is provided, scan those files relative to repo root, otherwise scan a small set of known files.
    """
    if paths is None:
        candidates = [
            "AUTONOMOUS_PROMPTS.md",
            "cockpit.html",
            "omni_gateway.py",
            "rehydrate_master.py",
            "inspect_firestore.py",
            "cloudbuild.yaml",
            "Dockerfile",
            "README.md",
        ]
    else:
        candidates = paths

    index = []
    for rel in candidates:
        path = os.path.join(REPO_ROOT, rel)
        if os.path.exists(path):
            try:
                stat = os.stat(path)
                entry = {
                    "path": rel.replace("\\", "/"),
                    "size": stat.st_size,
                    "mtime": datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
                    "sha1": sha1_of_file(path),
                }
                index.append(entry)
            except Exception as e:
                logger.warning("Failed to index %s: %s", rel, e)
    return index


def load_local_manifest() -> Dict[str, Any]:
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("Failed to read local manifest")
    return {}


def merge_manifest_with_index(
    manifest: Dict[str, Any], index: List[Dict[str, Any]]
) -> Dict[str, Any]:
    manifest = manifest.copy()
    manifest["doc_index"] = {
        e["path"]: {"sha1": e["sha1"], "mtime": e["mtime"], "size": e["size"]}
        for e in index
    }
    manifest["last_scanned"] = datetime.utcnow().isoformat() + "Z"
    # bump manifest version if docs changed
    v = manifest.get("manifest_version", "1.0")
    try:
        major, minor = v.split(".")
        minor = int(minor) + 1
        manifest["manifest_version"] = f"{major}.{minor}"
    except Exception:
        manifest["manifest_version"] = v
    return manifest


def init_firestore_client() -> Optional["firestore.Client"]:
    if not GCLOUD:
        logger.warning("google-cloud not installed; Firestore operations disabled")
        return None
    try:
        client = firestore.Client(project=FIRESTORE_PROJECT)
        logger.info("Connected to Firestore project=%s", FIRESTORE_PROJECT)
        return client
    except Exception:
        logger.exception("Failed to init Firestore client")
        return None


def write_manifest_firestore(
    client: "firestore.Client",
    manifest: Dict[str, Any],
    doc_id: str = "rehydrate_master_manifest",
) -> bool:
    try:
        client.collection(FIRESTORE_COLLECTION).document(doc_id).set(manifest)
        logger.info("Wrote manifest to Firestore/%s/%s", FIRESTORE_COLLECTION, doc_id)
        return True
    except Exception:
        logger.exception("Failed to write manifest to Firestore")
        return False


def write_doc_index_firestore(
    client: "firestore.Client", index: List[Dict[str, Any]], doc_id: str = "doc_index"
) -> bool:
    try:
        payload = {
            e["path"]: {"sha1": e["sha1"], "mtime": e["mtime"], "size": e["size"]}
            for e in index
        }
        client.collection(FIRESTORE_COLLECTION).document(doc_id).set(
            {"index": payload, "scanned_at": datetime.utcnow().isoformat() + "Z"}
        )
        logger.info("Wrote doc index to Firestore/%s/%s", FIRESTORE_COLLECTION, doc_id)
        return True
    except Exception:
        logger.exception("Failed to write doc index to Firestore")
        return False


def ensure_calendar_service() -> Optional[Any]:
    if not GCAL:
        logger.warning("googleapiclient not available; calendar sync disabled")
        return None
    # If service account credentials are used, build via service_account.Credentials
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    try:
        if creds_path and os.path.exists(creds_path):
            sc = service_account.Credentials.from_service_account_file(
                creds_path, scopes=["https://www.googleapis.com/auth/calendar"]
            )
            service = build("calendar", "v3", credentials=sc)
            logger.info("Calendar service initialized using service account")
            return service
        else:
            logger.warning(
                "No service account credentials found; calendar sync skipped"
            )
            return None
    except Exception:
        logger.exception("Failed to initialize Calendar service")
        return None


def create_calendar_event(
    service: Any,
    summary: str,
    description: str,
    start_dt: datetime,
    duration_minutes: int = 60,
) -> Optional[str]:
    try:
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "America/New_York"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "America/New_York"},
        }
        created = service.events().insert(calendarId="primary", body=event).execute()
        logger.info("Created calendar event: %s", created.get("id"))
        return created.get("id")
    except Exception:
        logger.exception("Failed to create calendar event")
        return None


def interactive_todo_loop(client: Optional["firestore.Client"]):
    print('\nInteractive TODOs (type "help" for commands)')
    coll = None
    if client:
        coll = client.collection("mcp_todos")

    def list_todos():
        if coll:
            docs = coll.stream()
            for d in docs:
                data = d.to_dict()
                print(
                    f"- [{ 'x' if data.get('done') else ' ' }] {d.id}: {data.get('title')} (created: {data.get('created')})"
                )
        else:
            print("Firestore not available; no remote TODOs.")

    def add_todo(title: str):
        item = {
            "title": title,
            "done": False,
            "created": datetime.utcnow().isoformat() + "Z",
        }
        if coll:
            doc = coll.document()
            doc.set(item)
            print("Added TODO", doc.id)
        else:
            print("Firestore not available; TODO not saved.")

    def complete_todo(doc_id: str):
        if coll:
            doc = coll.document(doc_id)
            doc.set({"done": True}, merge=True)
            print("Marked done", doc_id)
        else:
            print("Firestore not available; cannot mark done.")

    while True:
        cmd = input("todo> ").strip()
        if not cmd:
            continue
        if cmd in ("quit", "exit"):
            break
        if cmd == "help":
            print("commands: list | add <title> | done <docid> | exit")
            continue
        if cmd == "list":
            list_todos()
            continue
        if cmd.startswith("add "):
            add_todo(cmd[len("add ") :].strip())
            continue
        if cmd.startswith("done "):
            complete_todo(cmd[len("done ") :].strip())
            continue
        print("unknown command; type help")


def main():
    p = argparse.ArgumentParser(description="Auto-evolve hydrate script for MCP")
    p.add_argument("--scan", action="store_true", help="Scan docs and build index")
    p.add_argument(
        "--write-firestore",
        action="store_true",
        help="Write manifest and doc index to Firestore",
    )
    p.add_argument(
        "--sync-calendar",
        action="store_true",
        help="Create a calendar event for the next action (if credentials present)",
    )
    p.add_argument(
        "--interactive-todos",
        action="store_true",
        help="Open interactive todo list (backed by Firestore when available)",
    )
    p.add_argument("--paths", nargs="*", help="Specific files to scan (repo-relative)")
    args = p.parse_args()

    manifest_local = load_local_manifest() if os.path.exists(MANIFEST_PATH) else {}

    if args.scan:
        index = scan_docs(args.paths)
        merged = merge_manifest_with_index(manifest_local or {}, index)
        # write local manifest
        try:
            with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2)
            logger.info("Wrote local merged manifest to %s", MANIFEST_PATH)
        except Exception:
            logger.exception("Failed to write local manifest")

        client = None
        if args.write_firestore:
            client = init_firestore_client()
            if client:
                write_manifest_firestore(client, merged)
                write_doc_index_firestore(client, index)

        if args.sync_calendar:
            service = ensure_calendar_service()
            if service:
                summary = f"MCP Rehydrate: {merged.get('manifest_version')}"
                desc = (
                    f"Rehydrate run at {merged.get('last_scanned')} - manifest updated"
                )
                start = datetime.utcnow() + timedelta(minutes=5)
                create_calendar_event(service, summary, desc, start)
            else:
                logger.warning(
                    "Calendar service not initialized; skipping calendar sync"
                )

        print(
            json.dumps(
                {
                    "scanned": len(index),
                    "manifest_version": merged.get("manifest_version"),
                },
                indent=2,
            )
        )

    if args.interactive_todos:
        client = init_firestore_client() if args.write_firestore or GCLOUD else None
        interactive_todo_loop(client)


if __name__ == "__main__":
    main()
