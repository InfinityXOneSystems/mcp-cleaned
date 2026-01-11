"""Auto-normalize crawl reports into an Excel workbook with dynamic columns.

Generates two sheets:
 - reports: one row per report with discovered top-level fields
 - signals: one row per signal with discovered signal-level fields and a link to report filename

Usage:
  python scripts/reports_auto_normalizer.py
"""

import json
import sys
from pathlib import Path

REPORT_DIR = Path("data/reports")
OUT_DIR = Path("data/normalized")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_XLSX = OUT_DIR / "reports_auto_normalized.xlsx"


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
    for name, obj in report_objs:
        if isinstance(obj, dict):
            flat = flatten(obj)
            report_keys.update(flat.keys())
            signals = (
                obj.get("signals") or (obj.get("content") or {}).get("signals")
                if isinstance(obj.get("content"), dict)
                else obj.get("signals")
            )
            if signals and isinstance(signals, list):
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

    files = sorted(REPORT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    report_objs = []
    for f in files:
        try:
            obj = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            obj = {"raw": f.read_text(encoding="utf-8")}
        report_objs.append((f.name, obj))

    report_keys, signal_keys = discover_fields(report_objs)

    wb = Workbook()
    # Reports sheet
    ws_r = wb.active
    ws_r.title = "reports"
    headers_r = ["report_filename"] + report_keys
    ws_r.append(headers_r)
    for name, obj in report_objs:
        flat = flatten(obj) if isinstance(obj, dict) else {"raw": str(obj)}

        def to_cell(v):
            if v is None:
                return ""
            if isinstance(v, (list, dict)):
                try:
                    return json.dumps(v)
                except Exception:
                    return str(v)
            return v

        row = [name] + [to_cell(flat.get(k, "")) for k in report_keys]
        ws_r.append(row)

    # Signals sheet
    ws_s = wb.create_sheet("signals")
    headers_s = ["report_filename"] + signal_keys
    ws_s.append(headers_s)
    total_signals = 0
    for name, obj in report_objs:
        signals = None
        if isinstance(obj, dict):
            signals = obj.get("signals")
            if not signals and isinstance(obj.get("content"), dict):
                signals = obj["content"].get("signals")
        if signals and isinstance(signals, list):
            for s in signals:
                if isinstance(s, dict):
                    flat_s = flatten(s)
                    row = [name] + [to_cell(flat_s.get(k, "")) for k in signal_keys]
                    ws_s.append(row)
                    total_signals += 1

    wb.save(OUT_XLSX)
    print(
        f"Wrote {OUT_XLSX} with {len(report_objs)} reports and {total_signals} signals"
    )


if __name__ == "__main__":
    main()
