import re
from typing import Any, Dict

from .ai_extractor import LLMAdapter

PHONE_RE = re.compile(r"(\+?\d[\d\-\s]{7,}\d)")


def extract_entities_heuristic(text: str) -> Dict[str, Any]:
    phones = PHONE_RE.findall(text)
    # simple address heuristic (very basic)
    addresses = []
    for line in text.splitlines():
        if any(
            tok in line.lower()
            for tok in ("street", "st.", "ave", "road", "rd", "blvd", "lane")
        ):
            addresses.append(line.strip())
    return {"phones": phones, "addresses": addresses}


async def extract_entities(text: str, adapter: LLMAdapter = None) -> Dict[str, Any]:
    base = extract_entities_heuristic(text)
    if adapter:
        prompt = (
            "Extract normalized entities (names, addresses, phone, filing ids) as JSON."
        )
        res = await adapter.call_model(prompt=prompt, text=text)
        parsed = res.get("parsed", {})
        # merge heuristics with parsed, prefer parsed
        merged = {**base, **parsed}
        return merged
    return base
