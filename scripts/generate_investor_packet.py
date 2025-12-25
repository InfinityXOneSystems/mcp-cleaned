#!/usr/bin/env python3
"""Generate an investor packet from the consolidation staging folder.
"""
import os
import json
import glob
import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STAGING_ROOT = os.path.join(ROOT, 'staging')
OUT_FILE = os.path.join(ROOT, 'INVESTOR_PACKET.md')


def find_latest_staging():
    candidates = glob.glob(os.path.join(STAGING_ROOT, 'infinity-xos-index-snapshot-*'))
    if not candidates:
        return None
    candidates.sort()
    return candidates[-1]


def read_report(staging_dir):
    rpt = os.path.join(staging_dir, 'consolidation-report.json')
    if not os.path.exists(rpt):
        return None
    with open(rpt, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_packet(staging_dir, report):
    now = datetime.datetime.utcnow().isoformat()
    lines = []
    lines.append('# Infinity XOS — Investor Packet')
    lines.append(f'Generated: {now} UTC')
    lines.append('\n## Executive Summary')
    lines.append('The `mcp` Omni Gateway is a self-sustaining, FAANG-grade orchestration hub that provides a single pane of control for predictions, crawling, and autonomous task execution. It is currently configured in `safe` doc-evolution mode to avoid any external writes.')

    # Scrape highlights placeholder
    lines.append('\n## Last Night — Scrape Highlights')
    lines.append('- Sources scraped: *PLACEHOLDER* (use the staging snapshots to populate)')
    lines.append('- Total pages indexed: *PLACEHOLDER*')
    lines.append('- Examples: *PLACEHOLDER*')

    # Predictions
    lines.append('\n## Predictions Summary')
    lines.append('- Prediction system: Unified predictor across Intelligence and Meta services')
    lines.append('- Recent predictions: *PLACEHOLDER*')
    lines.append('- Confidence model: calibrated to historical signals; see `scripts/` for calibration outputs')

    # Capabilities
    lines.append('\n## System Capabilities (Highlights)')
    lines.append('- Omni Gateway: Unified `predict`, `crawl`, `simulate`, `read`, `write`, `analyze` endpoints')
    lines.append('- Autonomous pipelines: agent-driven Auto-Builder, Vision Cortex integration (read-only)')
    lines.append('- Doc Evolution: safe/read-only/live modes with audit gating')
    lines.append('- Local memory: `mcp_memory.db` (SQLite) with optional external memory gateways')
    lines.append('- Admin Console: `http://localhost:8000/admin` for monitoring, toggles, and chat')

    # Staging summary table
    lines.append('\n## Consolidation Report')
    lines.append(f'Staging directory: `{staging_dir}`')
    lines.append(f'Total subsystems scanned: {report.get("total_entries", 0)}')
    lines.append(f'Subsystems missing README: {len(report.get("missing_readme", []))}')
    if report.get('missing_readme'):
        lines.append('\n### Missing README (examples)')
        for n in report['missing_readme'][:20]:
            lines.append(f'- {n}')

    lines.append('\n## How to run the demo (60s)')
    lines.append('1. Start gateway: `python api_gateway.py`')
    lines.append('2. Start dashboard: `python dashboard_api.py`')
    lines.append('3. Open Admin Console: `http://localhost:8000/admin`')

    lines.append('\n## Next Steps')
    lines.append('- Review consolidated snapshots, then allow human review to enable doc-evolution `read-only` mode.')
    lines.append('- Harden admin toggle with passphrase and audit logs before `live`.')
    lines.append('- Prepare PR or archive `infinity-xos` as needed.')

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print('Investor packet written to', OUT_FILE)


def main():
    staging_dir = find_latest_staging()
    if not staging_dir:
        print('No staging snapshots found under', STAGING_ROOT)
        return 1
    report = read_report(staging_dir)
    if not report:
        print('No report found in', staging_dir)
        return 1
    generate_packet(staging_dir, report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
