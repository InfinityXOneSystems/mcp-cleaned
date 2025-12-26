"""Parse JSON crawl reports and export a normalized XLSX summary.

Columns:
 - report_filename
 - timestamp
 - source_url
 - text_length
 - keywords_found (comma-separated)
 - urgency_avg
 - emotional_stress_avg
 - financial_distress_avg
 - confidence_avg
 - deal_score_avg
 - raw_json (truncated)

Usage:
  python scripts/reports_to_xlsx.py
"""
import json
from pathlib import Path
from statistics import mean
import sys

REPORT_DIR = Path('data/reports')
OUT_DIR = Path('data/normalized')
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_XLSX = OUT_DIR / 'reports_summary.xlsx'

def extract_metrics(obj):
    # obj is the parsed JSON of a crawl report
    # support various shapes: may contain 'signals' array or raw content
    signals = obj.get('signals') if isinstance(obj, dict) else None
    if not signals and isinstance(obj, dict):
        # try common keys
        if 'content' in obj and isinstance(obj['content'], dict):
            signals = obj['content'].get('signals')
    if not signals:
        return None
    # aggregate metrics
    urgencies = [s.get('urgency', 0.0) for s in signals]
    stresses = [s.get('emotional_stress', 0.0) for s in signals]
    distress = [s.get('financial_distress', 0.0) for s in signals]
    confidences = [s.get('confidence', 0.0) for s in signals]
    deals = [s.get('deal_score', 0.0) for s in signals if s.get('deal_score') is not None]
    keywords = [s.get('keyword') for s in signals if s.get('keyword')]
    return {
        'keywords_found': ','.join(keywords),
        'urgency_avg': mean(urgencies) if urgencies else 0.0,
        'emotional_stress_avg': mean(stresses) if stresses else 0.0,
        'financial_distress_avg': mean(distress) if distress else 0.0,
        'confidence_avg': mean(confidences) if confidences else 0.0,
        'deal_score_avg': mean(deals) if deals else None,
        'keywords_list': keywords
    }

def main():
    try:
        import openpyxl
        from openpyxl import Workbook
    except Exception:
        print('openpyxl not installed. Run: python -m pip install openpyxl')
        sys.exit(1)

    files = sorted(REPORT_DIR.glob('*.json'), key=lambda p: p.stat().st_mtime)
    wb = Workbook()
    ws = wb.active
    ws.title = 'reports'
    headers = ['report_filename','timestamp','source_url','text_length','keywords_found','urgency_avg','emotional_stress_avg','financial_distress_avg','confidence_avg','deal_score_avg','raw_json']
    ws.append(headers)

    for f in files:
        raw = f.read_text(encoding='utf-8')
        try:
            obj = json.loads(raw)
        except Exception:
            obj = {'raw': raw}
        metrics = extract_metrics(obj) or {}
        # try to get top-level info
        timestamp = obj.get('created_at') or obj.get('ts') or ''
        source = ''
        if isinstance(obj, dict):
            source = obj.get('url') or (obj.get('content') or {}).get('url') or ''
        text_len = 0
        if isinstance(obj, dict):
            text = obj.get('text') or obj.get('html') or (obj.get('content') or {}).get('text') or ''
            text_len = len(text) if text else 0
        row = [
            f.name,
            timestamp,
            source,
            text_len,
            metrics.get('keywords_found',''),
            round(metrics.get('urgency_avg',0.0),3),
            round(metrics.get('emotional_stress_avg',0.0),3),
            round(metrics.get('financial_distress_avg',0.0),3),
            round(metrics.get('confidence_avg',0.0),3),
            round(metrics['deal_score_avg'],3) if metrics.get('deal_score_avg') is not None else '',
            (json.dumps(obj)[:400])
        ]
        ws.append(row)

    wb.save(OUT_XLSX)
    print('Wrote', OUT_XLSX)

if __name__ == '__main__':
    main()
