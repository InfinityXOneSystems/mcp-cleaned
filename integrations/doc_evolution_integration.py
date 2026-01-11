import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Common places to look; allow override via env var
EXTERNAL_PATHS = [
    os.environ.get("DOC_EV_PATH_OVERRIDE", ""),
    os.path.join(ROOT, "..", "infinity-xos"),
    os.path.join(ROOT, "infinity-xos"),
    r"C:\AI\repos\infinity-xos",
]


def find_doc_evolve_file() -> Optional[str]:
    """Locate a doc_evolve.py file in known external paths.

    Returns the filesystem path to the file or None.
    """
    tried = set()
    for base in EXTERNAL_PATHS:
        if not base:
            continue
        base = os.path.abspath(base)
        if base in tried:
            continue
        tried.add(base)
        if not os.path.exists(base):
            continue
        # quick check common subpath
        common = os.path.join(
            base,
            "services",
            "real-estate-intelligence",
            "vision-cortex",
            "doc_system",
            "doc_evolve.py",
        )
        if os.path.exists(common):
            return common
        # walk a few levels for a candidate
        for root, dirs, files in os.walk(base):
            if "doc_evolve.py" in files:
                return os.path.join(root, "doc_evolve.py")
            # limit depth to avoid long scans
            # compute depth relative to base
            if root.count(os.sep) - base.count(os.sep) > 6:
                # prune deeper dirs
                dirs[:] = []
    return None


DOC_EV_FILE = find_doc_evolve_file()
_doc_evolver = None

# Modes: 'safe' (default) => no writes to external repo; 'read-only' => can read but not create versions;
# 'live' => full behavior including creating versions in external repo. Use env var DOC_EV_MODE to override.
DOC_EV_MODE = os.environ.get("DOC_EV_MODE", "safe")


def _load_doc_evolver():
    """Import and instantiate the DocEvolveSystem if available."""
    global _doc_evolver
    if _doc_evolver is not None:
        return _doc_evolver

    if not DOC_EV_FILE:
        return None

    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("doc_evolve", DOC_EV_FILE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # Expect DocEvolveSystem to be present
        if hasattr(mod, "DocEvolveSystem"):
            DocEvolveSystem = getattr(mod, "DocEvolveSystem")
            # set versions directory next to the doc file so versions persist inside external repo
            versions_dir = os.path.join(os.path.dirname(DOC_EV_FILE), "docs_versions")
            # If running in safe mode, avoid creating or modifying the external versions directory
            if DOC_EV_MODE == "safe":
                logger.info(
                    "DOC_EV_MODE=safe: not instantiating DocEvolveSystem to avoid external writes"
                )
                return None
            _doc_evolver = DocEvolveSystem(versions_dir=versions_dir)
            logger.info(
                "Loaded DocEvolveSystem from %s (mode=%s)", DOC_EV_FILE, DOC_EV_MODE
            )
            return _doc_evolver
    except Exception:
        logger.exception("Failed to load DocEvolveSystem from %s", DOC_EV_FILE)

    return None


def ingest_document(source: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Ingest a document. If external system found, call it; else run local stub."""
    logger.info("Ingest doc: %s", source)
    evolver = _load_doc_evolver()
    # Read content
    try:
        with open(source, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        text = ""

    if evolver:
        try:
            # If running in read-only mode we will not create new versions
            doc_id = metadata.get("doc_id") if isinstance(metadata, dict) else None
            if not doc_id:
                doc_id = os.path.splitext(os.path.basename(source))[0]
            change_summary = (
                metadata.get("summary", "ingest")
                if isinstance(metadata, dict)
                else "ingest"
            )
            author = (
                metadata.get("author", "system")
                if isinstance(metadata, dict)
                else "system"
            )
            if DOC_EV_MODE == "read-only":
                # do not write; return what would have been done
                return {
                    "status": "read-only",
                    "doc_id": doc_id,
                    "would_create": True,
                    "change_summary": change_summary,
                }
            if DOC_EV_MODE == "live":
                version_id = evolver.create_version(
                    doc_id, text, change_summary=change_summary, author=author
                )
                return {"status": "ok", "doc_id": doc_id, "version_id": version_id}
            # if mode is unknown or safe, do not write
            logger.info("DOC_EV_MODE=%s: skipping create_version", DOC_EV_MODE)
            return {
                "status": "skipped",
                "reason": f"mode={DOC_EV_MODE}",
                "doc_id": doc_id,
            }
        except Exception:
            logger.exception("Evolver ingest failed")

    # Stubbed behavior: return small summary
    summary = text[:1000]
    return {
        "status": "stubbed",
        "summary": summary,
        "source": source,
        "metadata": metadata,
    }


def get_mode() -> str:
    """Return current DOC_EV_MODE (runtime value)."""
    return DOC_EV_MODE


def set_mode(mode: str) -> Dict[str, Any]:
    """Set DOC_EV_MODE at runtime. Allowed: safe, read-only, live."""
    global DOC_EV_MODE, _doc_evolver
    if mode not in ("safe", "read-only", "live"):
        return {"status": "error", "reason": "invalid mode"}
    DOC_EV_MODE = mode
    # Reset loaded evolver if mode changes to safe to avoid external writes
    if mode == "safe":
        _doc_evolver = None
    return {"status": "ok", "mode": DOC_EV_MODE}


def get_doc_ev_file() -> Optional[str]:
    return DOC_EV_FILE


def set_doc_ev_path_override(path: str) -> Dict[str, Any]:
    """Set DOC_EV_PATH_OVERRIDE and attempt to locate doc_evolve.py in the path."""
    global DOC_EV_FILE
    if not path or not os.path.exists(path):
        return {"status": "error", "reason": "path does not exist"}
    # write into env for future process launches (best-effort)
    os.environ["DOC_EV_PATH_OVERRIDE"] = path
    # re-run finder
    found = find_doc_evolve_file()
    DOC_EV_FILE = found
    return {"status": "ok", "found": found}


def transform_document(doc_id: str, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
    logger.info(
        "Transform doc: %s ops:%d", doc_id, len(operations) if operations else 0
    )
    evolver = _load_doc_evolver()
    if evolver:
        # Try to apply first operation as improvement type
        try:
            applied = 0
            last_content = None
            latest = evolver.get_latest_version(doc_id)
            if latest:
                last_content = latest.content
            else:
                last_content = ""

            for op in operations:
                if not isinstance(op, dict):
                    continue
                t = op.get("type") or op.get("improvement_type")
                if t:
                    ok, improved = evolver.apply_improvement(doc_id, last_content, t)
                    if ok:
                        # create a new version with improved content
                        vid = evolver.create_version(
                            doc_id,
                            improved,
                            change_summary=f"applied:{t}",
                            author=op.get("author", "system"),
                        )
                        applied += 1
                        last_content = improved
            return {"status": "ok", "doc_id": doc_id, "applied": applied}
        except Exception:
            logger.exception("Evolver transform failed")

    return {
        "status": "stubbed",
        "doc_id": doc_id,
        "applied": len(operations) if operations else 0,
    }


def evolve_document(doc_id: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("Evolve doc: %s strategy:%s", doc_id, strategy)
    evolver = _load_doc_evolver()
    if evolver:
        try:
            # strategy may ask for suggestions, improvements, or create a new version
            if strategy.get("suggest"):
                latest = evolver.get_latest_version(doc_id)
                if latest:
                    suggestions = evolver.suggest_improvements(latest.content)
                    return {"status": "ok", "suggestions": suggestions}
                else:
                    return {"status": "ok", "suggestions": []}

            if "improvement_type" in strategy:
                latest = evolver.get_latest_version(doc_id)
                content = latest.content if latest else ""
                ok, improved = evolver.apply_improvement(
                    doc_id, content, strategy["improvement_type"]
                )
                if ok:
                    vid = evolver.create_version(
                        doc_id,
                        improved,
                        change_summary=f"evolved:{strategy['improvement_type']}",
                    )
                    return {"status": "ok", "version_id": vid}
                return {"status": "error", "reason": "apply_failed"}

            return {
                "status": "ok",
                "message": "no-op or unknown strategy",
                "strategy": strategy,
            }
        except Exception:
            logger.exception("Evolver evolve failed")

    return {"status": "stubbed", "doc_id": doc_id, "strategy": strategy}


def sync_documents(target: str) -> Dict[str, Any]:
    logger.info("Sync documents to: %s", target)
    evolver = _load_doc_evolver()
    if evolver:
        try:
            # Provide a lightweight sync summary: number of docs and versions
            total_docs = len(evolver.versions)
            total_versions = sum(len(v) for v in evolver.versions.values())
            return {
                "status": "ok",
                "target": target,
                "total_docs": total_docs,
                "total_versions": total_versions,
            }
        except Exception:
            logger.exception("Evolver sync failed")

    return {"status": "stubbed", "target": target}
