import argparse
import json
import os
from datetime import datetime

QUEUE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "demo", "agent_queue.jsonl")
)


def ensure_queue_dir():
    d = os.path.dirname(QUEUE_PATH)
    os.makedirs(d, exist_ok=True)


def enqueue(entry: dict):
    ensure_queue_dir()
    line = json.dumps(entry, ensure_ascii=False)
    # atomic append
    with open(QUEUE_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return entry


def build_entry(message: str, agent: str, priority: str):
    ts = datetime.utcnow().isoformat() + "Z"
    return {
        "created_at": ts,
        "type": "delegate_request",
        "task": "skip_changes_delegate",
        "message": message,
        "target_agent": agent,
        "priority": priority,
        "status": "queued",
        "metadata": {
            "source": "cli.delegate_skip",
            "enqueued_at": ts,
        },
    }


def main():
    p = argparse.ArgumentParser(
        description="Queue a 'Skip Changes' delegate request for background agents."
    )
    p.add_argument(
        "--message",
        "-m",
        default="Skip Changes: Delegate to Background Agent",
        help="Human-readable task message",
    )
    p.add_argument(
        "--agent", "-a", default="agents.runner", help="Target agent name (optional)"
    )
    p.add_argument(
        "--priority",
        "-p",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        default="MEDIUM",
        help="Governance priority",
    )
    args = p.parse_args()

    entry = build_entry(args.message, args.agent, args.priority)
    queued = enqueue(entry)
    print(json.dumps({"queued": True, "path": QUEUE_PATH, "entry": queued}, indent=2))


if __name__ == "__main__":
    main()
