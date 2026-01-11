"""Discover `data/reports` folders under a repos root, aggregate and auto-normalize into XLSX.

Usage:
  python scripts/reports_auto_normalizer_multi.py [repos_root]
Default repos_root: C:\AI\repos

Output written to this repo's data/normalized/reports_auto_normalized_multi.xlsx
"""

import json
import sys
from pathlib import Path

DEFAULT_ROOT = Path("C:/AI/repos")
THIS_OUT = Path("data/normalized")
THIS_OUT.mkdir(parents=True, exist_ok=True)
OUT_XLSX = THIS_OUT / "reports_auto_normalized_multi.xlsx"


def find_report_dirs(root: Path):
    for p in root.rglob("data/reports"):
        if p.is_dir():
            yield p


def load_reports_from_dir(dir_path: Path):
    reports = []
    for f in sorted(dir_path.glob("*.json")):
        try:
            obj = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            obj = {"raw": f.read_text(encoding="utf-8")}
        reports.append((str(dir_path.parent), f.name, obj))
    return reports


def flatten(d, parent_key="", sep="."):
    items = {}
    if isinstance(d, dict):
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(flatten(v, new_key, sep=sep))
            else:
                items[new_key] = v
    else:
        items[parent_key] = d
    return items


def discover_fields(report_objs):
    report_keys = set()
    signal_keys = set()
    for repo_path, name, obj in report_objs:
        if isinstance(obj, dict):
            flat = flatten(obj)
            report_keys.update(flat.keys())
            # try multiple common signal paths
            candidate_paths = [
                obj.get("signals"),
                (
                    (obj.get("content") or {}).get("signals")
                    if isinstance(obj.get("content"), dict)
                    else None
                ),
                obj.get("items"),
                obj.get("results"),
                obj.get("payload"),
            ]
            signals = None
            for c in candidate_paths:
                if isinstance(c, list):
                    signals = c
                    break
            if signals:
                for s in signals:
                    if isinstance(s, dict):
                        signal_keys.update(flatten(s).keys())
    return sorted(report_keys), sorted(signal_keys)


def main():
    try:
        from openpyxl import Workbook
    except Exception:
        print("openpyxl not installed. Run: python -m pip install openpyxl")
        sys.exit(1)

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ROOT
    all_reports = []
    for rpt_dir in find_report_dirs(root):
        loaded = load_reports_from_dir(rpt_dir)
        all_reports.extend([(r[0], r[1], r[2]) for r in loaded])

    if not all_reports:
        print("No reports found under", root)
        return

    report_keys, signal_keys = discover_fields(all_reports)

    wb = Workbook()
    ws_r = wb.active
    ws_r.title = "reports"
    headers_r = ["repo_path", "report_filename"] + report_keys
    ws_r.append(headers_r)

    def to_cell(v):
        if v is None:
            return ""
        if isinstance(v, (list, dict)):
            try:
                return json.dumps(v)
            except Exception:
                return str(v)
        return v

    for repo_path, name, obj in all_reports:
        flat = flatten(obj) if isinstance(obj, dict) else {"raw": str(obj)}
        row = [repo_path, name] + [to_cell(flat.get(k, "")) for k in report_keys]
        ws_r.append(row)

    ws_s = wb.create_sheet("signals")
    headers_s = ["repo_path", "report_filename"] + signal_keys
    ws_s.append(headers_s)
    total_signals = 0
    for repo_path, name, obj in all_reports:
        signals = None
        # try common locations
        if isinstance(obj, dict):
            candidates = [
                obj.get("signals"),
                (
                    (obj.get("content") or {}).get("signals")
                    if isinstance(obj.get("content"), dict)
                    else None
                ),
                obj.get("items"),
                obj.get("results"),
                obj.get("payload"),
            ]
            for c in candidates:
                if isinstance(c, list):
                    signals = c
                    break
        if signals:
            for s in signals:
                if isinstance(s, dict):
                    flat_s = flatten(s)
                    row = [repo_path, name] + [
                        to_cell(flat_s.get(k, "")) for k in signal_keys
                    ]
                    ws_s.append(row)
                    total_signals += 1

    wb.save(OUT_XLSX)
    print(
        f"Wrote {OUT_XLSX} with {len(all_reports)} reports from {root} and {total_signals} signals"
    )


if __name__ == "__main__":
    main()
