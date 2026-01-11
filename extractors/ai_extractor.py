from typing import Any, Dict, List

from pydantic import BaseModel


class LLMAdapter:
    """Adapter interface. Implement call_model(prompt, **kwargs)."""

    async def call_model(self, prompt: str, **kwargs) -> Dict:
        raise NotImplementedError()


class OpenAIAdapter(LLMAdapter):
    def __init__(self, client=None):
        self.client = client  # pass in externally; do not load keys here

    async def call_model(self, prompt: str, **kwargs):
        # placeholder; tests should mock this
        return {"text": "{}", "usage": {}}


class Signal(BaseModel):
    keyword: str
    context: str
    urgency: float
    emotional_stress: float
    financial_distress: float
    intent: Dict[str, float]
    entities: Dict[str, Any]
    confidence: float


async def extract_signals(
    text: str, keywords: List[str], adapter: LLMAdapter
) -> List[Signal]:
    """
    Uses adapter.call_model to classify urgency, emotion, intent, and extract entities.
    Keep prompt engineering in caller; adapter abstracts provider details.
    """
    # lightweight local heuristics-first pass
    hits = [k for k in keywords if k.lower() in text.lower()]
    results = []
    for k in hits:
        prompt = f"Extract signal for keyword '{k}' and surrounding context. Return JSON with urgency(0-1), emotional_stress(0-1), financial_distress(0-1), intent (borrow,sell), entities, confidence."
        res = await adapter.call_model(prompt=prompt, text=text, keyword=k)
        # adapter expected to return parsed dict; fallbacks if not
        data = res.get("parsed") if isinstance(res, dict) and res.get("parsed") else {}
        results.append(
            Signal(
                keyword=k,
                context=text[
                    max(0, text.lower().find(k.lower()) - 200) : text.lower().find(
                        k.lower()
                    )
                    + 200
                ],
                urgency=float(data.get("urgency", 0.0)),
                emotional_stress=float(data.get("emotional_stress", 0.0)),
                financial_distress=float(data.get("financial_distress", 0.0)),
                intent=data.get("intent", {"borrow": 0.0, "sell": 0.0}),
                entities=data.get("entities", {}),
                confidence=float(data.get("confidence", 0.5)),
            )
        )
    return results
