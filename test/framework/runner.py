import importlib
import pkgutil
from typing import Any, Dict, List

from ..config import BASE_RECORDS_PATH
from .reporting import write_json_record


def discover_subsystems(package_path: str) -> List[str]:
    modules = []
    for _, name, ispkg in pkgutil.iter_modules([package_path]):
        if not ispkg and name.endswith("_test"):
            modules.append(name)
    return modules


def run_subsystem(name: str) -> Dict[str, Any]:
    """Import subsystem module and run its run() function."""
    mod = importlib.import_module(f"test.subsystems.{name}")
    if hasattr(mod, "run"):
        return mod.run()
    return {"name": name, "status": "skipped", "reason": "run() not found"}


def run_all(subsystems: List[str]) -> Dict[str, Any]:
    results = {
        "summary": {"total": 0, "success": 0, "fail": 0, "skipped": 0},
        "details": [],
    }
    for name in subsystems:
        res = run_subsystem(name)
        # Write per-subsystem record mirrored under records/subsystems/<name>
        short = name.replace("_test", "")
        write_json_record(BASE_RECORDS_PATH, f"subsystems/{short}", short, res)

        results["details"].append(res)
        results["summary"]["total"] += 1
        status = res.get("status", "unknown").lower()
        if status == "success":
            results["summary"]["success"] += 1
        elif status == "fail":
            results["summary"]["fail"] += 1
        else:
            results["summary"]["skipped"] += 1
    return results


def write_master_record(payload: Dict[str, Any]) -> str:
    return write_json_record(BASE_RECORDS_PATH, "master", "system_master", payload)
