#!/usr/bin/env python3
"""Ingest and normalize crawl reports from data/reports.

Writes normalized JSON files to `data/normalized/` and optionally writes
records to Firestore via `storage.firestore_adapter.FirestoreAdapter`.

Usage:
  python scripts/ingest_normalize.py --reports-dir data/reports --out-dir data/normalized --write-firestore
"""
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import sys
# ensure repo root on sys.path so `storage` and other packages import correctly
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from storage.firestore_adapter import FirestoreAdapter
try:
    from extractors.entity_extractor import extract_entities_heuristic
except Exception:
    def extract_entities_heuristic(text: str):
        return {"phones": [], "addresses": []}


def normalize_report_file(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        raise RuntimeError(f"failed to load {path}: {e}")

    # session id derived from filename
    session_hash = path.stem
    stat = path.stat()
    created_at = datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z"

    start_url = payload.get("start_url") or payload.get("seed") or ""
    parsed = urlparse(start_url) if start_url else None
    domain = parsed.netloc if parsed else None

    # Gather text to run heuristic entity extraction on
    text_pieces = []
    if isinstance(payload.get("results_summary"), list):
        for r in payload.get("results_summary", []):
            if isinstance(r, dict):
                text_pieces.append(r.get("text") or r.get("html") or "")
            else:
                text_pieces.append(str(r))

    # fallback: include entire raw as string if nothing else
    if not text_pieces and isinstance(payload, dict):
        # join values conservatively
        for k, v in payload.items():
            if isinstance(v, str) and len(v) < 2000:
                text_pieces.append(v)

    joined_text = "\n".join([t for t in text_pieces if t])
    entities = extract_entities_heuristic(joined_text)

    normalized = {
        "session_hash": session_hash,
        "type": "crawl_report_normalized",
        "source": "crawl_report",
        "start_url": start_url,
        "domain": domain,
        "created_at": created_at,
        "duration_sec": payload.get("duration_sec"),
        "max_pages": payload.get("max_pages"),
        "max_depth": payload.get("max_depth"),
        "found": payload.get("found"),
        "results_count": len(payload.get("results_summary") or []),
        "entities": entities,
        "raw": payload,
    }
    return normalized


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reports-dir", default="data/reports")
    p.add_argument("--out-dir", default="data/normalized")
    p.add_argument("--write-firestore", action="store_true", help="Write normalized records to FirestoreAdapter (or local fallback)")
    args = p.parse_args()

    reports_dir = Path(args.reports_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fs = FirestoreAdapter()

    files = sorted([p for p in reports_dir.glob("*.json")])
    if not files:
        print(f"No report JSON files found in {reports_dir}")
        return

    processed = 0
    for f in files:
        try:
            normalized = normalize_report_file(f)
        except Exception as e:
            print(f"Skipping {f.name}: load/normalize error: {e}")
            continue

        out_path = out_dir / f"{f.stem}.normalized.json"
        try:
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(normalized, fh, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed writing normalized file {out_path}: {e}")
            continue

        if args.write_firestore:
            try:
                fs.write_memory(normalized)
            except Exception as e:
                print(f"Firestore write failed for {f.name}: {e}")

        print(f"Normalized {f.name} -> {out_path.name}")
        processed += 1

    print(f"Processed {processed} reports.")


if __name__ == "__main__":
    main()
