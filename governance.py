"""Simple governance helpers for threshold checks and escalation flags"""

import os
from typing import Any, Dict

DEFAULT_CONFIDENCE_THRESH = float(os.environ.get("CONF_THRESHOLD", "0.6"))


def is_action_allowed(confidence: float, requires_high_trust: bool = False) -> bool:
    thresh = DEFAULT_CONFIDENCE_THRESH
    if requires_high_trust:
        thresh = max(thresh, 0.85)
    return confidence >= thresh


def need_escalation(confidence: float) -> bool:
    return confidence < (DEFAULT_CONFIDENCE_THRESH)


def permission_from_role(role: str) -> Dict[str, Any]:
    # naive role map; expand as needed
    if role == "admin":
        return {"can_execute": True, "can_approve": True}
    if role == "operator":
        return {"can_execute": False, "can_approve": True}
    return {"can_execute": False, "can_approve": False}
