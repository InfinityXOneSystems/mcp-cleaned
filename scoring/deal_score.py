from typing import Dict, Any
from pydantic import BaseModel

class Weights(BaseModel):
    urgency: float = 0.35
    distress: float = 0.30
    liquidity: float = 0.20
    confidence: float = 0.15

def score_signal(signal: Dict[str, Any], weights: Weights = Weights()) -> Dict[str, Any]:
    """
    signal must contain urgency (0-1), emotional_stress (0-1), financial_distress (0-1), intent dict, confidence (0-1), liquidity_estimate (0-1)
    """
    urgency = signal.get("urgency", 0.0)
    distress = signal.get("financial_distress", signal.get("emotional_stress", 0.0))
    liquidity = signal.get("liquidity_estimate", 0.5)
    confidence = signal.get("confidence", 0.5)
    raw = (
        urgency * weights.urgency +
        distress * weights.distress +
        liquidity * weights.liquidity +
        confidence * weights.confidence
    )
    final = max(0, min(100, int(raw * 100)))
    contributions = {
        "urgency": urgency * weights.urgency * 100,
        "distress": distress * weights.distress * 100,
        "liquidity": liquidity * weights.liquidity * 100,
        "confidence": confidence * weights.confidence * 100,
    }
    recommended_action = "monitor"
    time_sensitivity = "72h"
    if final >= 85:
        recommended_action = "call_within_24h"
        time_sensitivity = "24h"
    elif final >= 60:
        recommended_action = "email_followup"
        time_sensitivity = "48h"
    return {"score": final, "contributions": contributions, "recommended_action": recommended_action, "time_sensitivity": time_sensitivity}
