"""Safety and governance checks for Vision Cortex."""
from __future__ import annotations

from typing import Dict, Any

GOVERNANCE_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def enforce_governance(level: str) -> str:
    if level not in GOVERNANCE_LEVELS:
        return "HIGH"  # default up if unclear
    return level


def annotate_risk(payload: Dict[str, Any], level: str) -> Dict[str, Any]:
    return {"payload": payload, "governance_level": enforce_governance(level)}
