"""List and view crawl reports from data/reports in a safe way.

Usage:
  python scripts/list_reports.py           # lists recent reports
  python scripts/list_reports.py <filename>  # prints the given report prettified
"""

import json
import sys
from pathlib import Path

REPORT_DIR = Path("data/reports")


def list_reports(n=30):
    if not REPORT_DIR.exists():
        print("No reports directory:", REPORT_DIR)
        return
    files = sorted(
        REPORT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    for i, f in enumerate(files[:n], start=1):
        print(f"{i:02d}. {f.name}  ({f.stat().st_size} bytes)  {f.stat().st_mtime}")


def show_report(name):
    path = REPORT_DIR / name
    if not path.exists():
        print("Report not found:", path)
        return
    raw = path.read_text(encoding="utf-8")
    try:
        obj = json.loads(raw)
        print(json.dumps(obj, indent=2))
    except Exception:
        print(raw)


def main():
    if len(sys.argv) == 1:
        list_reports()
    else:
        show_report(sys.argv[1])


if __name__ == "__main__":
    main()
