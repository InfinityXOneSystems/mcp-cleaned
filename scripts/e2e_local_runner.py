import asyncio
import json
import sys
from pathlib import Path

# ensure repo root is on sys.path for local script execution
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from extractors.ai_extractor import extract_signals
from mocks.mock_llm_adapter import MockLLMAdapter
from scoring.deal_score import score_signal
from storage.firestore_adapter import FirestoreAdapter

RAW_DIR = Path("crawler/output/raw")
FALLBACK_REPORT = Path("data/reports")


def latest_snapshot_path():
    if RAW_DIR.exists():
        files = sorted(
            RAW_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if files:
            return files[0]
    # fallback to reports folder
    if FALLBACK_REPORT.exists():
        files = sorted(
            FALLBACK_REPORT.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if files:
            return files[0]
    return None


async def run():
    path = latest_snapshot_path()
    if not path:
        print(
            "No snapshot found in crawler/output/raw or data/reports. Run a crawl first."
        )
        return
    print("Using snapshot:", path)
    data = json.loads(path.read_text(encoding="utf-8"))
    # try multiple fallback fields for textual content
    text = None
    for key in ("text", "html", "content", "body"):
        if data.get(key):
            text = data.get(key)
            break
    if text is None:
        # if the snapshot has nested payloads, stringify them
        text = json.dumps(data)
    keywords = [
        "need funding fast",
        "behind on payroll",
        "pre foreclosure",
        "tax delinquent",
    ]

    adapter = MockLLMAdapter()
    signals = await extract_signals(text, keywords, adapter)
    fs = FirestoreAdapter()

    results = []
    for s in signals:
        sig = s.dict()
        scored = score_signal(sig)
        record = {
            "industry": "Test",
            "source": data.get("url"),
            "signal": sig["keyword"],
            "urgency_score": sig["urgency"],
            "deal_score": scored["score"],
            "location": sig.get("entities", {}).get("address", "unknown"),
            "recommended_action": scored["recommended_action"],
        }
        print(json.dumps(record, indent=2))
        fs.write_memory(
            {
                "session_hash": f'e2e_{path.stem}_{sig["keyword"]}',
                "type": "signal",
                "content": record,
            }
        )
        results.append(record)

    print(f"Persisted {len(results)} signals (or wrote local fallback).")


if __name__ == "__main__":
    asyncio.run(run())
