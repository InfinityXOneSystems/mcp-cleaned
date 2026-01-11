import asyncio
from typing import Any, Dict


class MockLLMAdapter:
    """Simple mock adapter that returns deterministic parsed JSON for testing."""

    async def call_model(self, prompt: str, **kwargs) -> Dict[str, Any]:
        # use keyword hint if present
        kwargs.get("keyword") or "unknown"
        # simple deterministic scoring by presence of urgent words
        text = kwargs.get("text", "")
        urgency = (
            0.8
            if any(
                w in text.lower()
                for w in ["urgent", "emergency", "behind", "delinquent"]
            )
            else 0.2
        )
        emotional_stress = (
            0.7
            if any(w in text.lower() for w in ["stressed", "panic", "desperate"])
            else 0.1
        )
        confidence = 0.6
        parsed = {
            "urgency": urgency,
            "emotional_stress": emotional_stress,
            "financial_distress": 0.5,
            "intent": {"borrow": 0.6, "sell": 0.1},
            "entities": {},
            "confidence": confidence,
        }
        await asyncio.sleep(0.01)
        return {"parsed": parsed}
