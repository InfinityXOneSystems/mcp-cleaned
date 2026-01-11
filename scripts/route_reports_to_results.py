"""Route crawl reports from multiple repos into a centralized results/ folder by category.

Categories (simple heuristics):
  - distressed_properties
  - business_loans
  - personal_loans
  - asset_predictions

Usage:
  python scripts/route_reports_to_results.py [repos_root]
Default repos_root: C:\AI\repos
Output: results/<category>/<repo_name>/<report_file.json> (created under this repo)
Also writes results/index.csv with columns: repo_path, report_filename, category, dest_path
"""

import csv
import json
import shutil
import sys
from pathlib import Path

DEFAULT_ROOT = Path("C:/AI/repos")
OUT_ROOT = Path("results")
OUT_ROOT.mkdir(exist_ok=True)

# primitive keyword maps
CATEGORY_KEYWORDS = {
    "distressed_properties": [
        "pre foreclosure",
        "foreclosure",
        "tax delinquent",
        "probate",
        "vacant house",
        "code violation",
        "delinquent tax",
    ],
    "business_loans": [
        "business loan",
        "cash flow",
        "payroll",
        "working capital",
        "invoice",
        "bridge loan",
        "merchant cash advance",
        "SBA",
        "invoice factoring",
        "accounts receivable",
    ],
    "personal_loans": [
        "personal loan",
        "paycheck advance",
        "personal finance",
        "installment loan",
        "ppf",
        "personal credit",
    ],
    "asset_predictions": [
        "asset prediction",
        "price drop",
        "vacancy",
        "market signal",
        "insurance claim",
        "price forecast",
        "asset value",
    ],
}


def classify_text(text: str):
    if not text:
        return "uncategorized"
    t = text.lower()
    scores = {k: 0 for k in CATEGORY_KEYWORDS.keys()}
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in t:
                scores[cat] += 1
    # pick highest score
    best = max(scores.items(), key=lambda kv: kv[1])
    if best[1] == 0:
        return "uncategorized"
    return best[0]


def find_report_dirs(root: Path):
    for p in root.rglob("data/reports"):
        if p.is_dir():
            yield p


def route_reports(root: Path):
    index_rows = []
    for rpt_dir in find_report_dirs(root):
        repo_name = rpt_dir.parents[1].name
        for f in rpt_dir.glob("*.json"):
            try:
                obj = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                obj = {"raw": f.read_text(encoding="utf-8")}
            # determine text to classify
            text = ""
            if isinstance(obj, dict):
                text = (
                    obj.get("text")
                    or obj.get("html")
                    or (obj.get("content") or {}).get("text")
                    or json.dumps(obj)
                )
            category = classify_text(text)
            dest_dir = OUT_ROOT / category / repo_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / f.name
            shutil.copy2(f, dest_path)
            index_rows.append(
                {
                    "repo_path": str(rpt_dir.parent),
                    "report_filename": f.name,
                    "category": category,
                    "dest_path": str(dest_path),
                }
            )
    # write index
    idx_path = OUT_ROOT / "index.csv"
    with idx_path.open("w", newline="", encoding="utf-8") as csvf:
        writer = csv.DictWriter(
            csvf, fieldnames=["repo_path", "report_filename", "category", "dest_path"]
        )
        writer.writeheader()
        for r in index_rows:
            writer.writerow(r)
    return idx_path, len(index_rows)


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ROOT
    idx_path, count = route_reports(root)
    print(f"Routed {count} reports. Index at {idx_path}")


if __name__ == "__main__":
    main()
