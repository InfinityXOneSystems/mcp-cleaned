#!/usr/bin/env python3
"""Generate a FAANG-grade investor packet with professional SVG assets.

This script reads the latest consolidation staging snapshot created by
`consolidate_infinity_xos_readonly.py`, generates simple professional SVG
assets (cover, capabilities, timeline), and writes an enhanced
`INVESTOR_PACKET.md` at the repo root.
"""
import datetime
import glob
import json
import os
import textwrap

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STAGING_ROOT = os.path.join(ROOT, "staging")
OUT_FILE = os.path.join(ROOT, "INVESTOR_PACKET.md")
ASSETS_DIR = os.path.join(ROOT, "assets", "investor_packet")


def find_latest_staging():
    candidates = glob.glob(os.path.join(STAGING_ROOT, "infinity-xos-index-snapshot-*"))
    if not candidates:
        return None
    candidates.sort()
    return candidates[-1]


def read_report(staging_dir):
    rpt = os.path.join(staging_dir, "consolidation-report.json")
    if not os.path.exists(rpt):
        return None
    with open(rpt, "r", encoding="utf-8") as f:
        return json.load(f)


def gather_summaries(staging_dir):
    summaries = []
    for root, dirs, files in os.walk(staging_dir):
        if "SUMMARY.md" in files:
            rel = os.path.relpath(root, staging_dir)
            path = os.path.join(root, "SUMMARY.md")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception:
                text = ""
            summaries.append({"subsystem": rel.replace("\\", "/"), "summary": text})
    return summaries


def ensure_assets_dir():
    os.makedirs(ASSETS_DIR, exist_ok=True)


def write_svg_cover(title, subtitle, path):
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#0b2545"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#g)" />
  <g transform="translate(60,80)">
    <text x="0" y="0" font-family="Segoe UI, Roboto, Arial" font-size="44" fill="#ffffff">{title}</text>
    <text x="0" y="60" font-family="Segoe UI, Roboto, Arial" font-size="20" fill="#cbd5e1">{subtitle}</text>
  </g>
  <g transform="translate(60,520)">
    <text x="0" y="0" font-family="Segoe UI, Roboto, Arial" font-size="14" fill="#94a3b8">Generated: {datetime.datetime.utcnow().date().isoformat()} UTC</text>
  </g>
</svg>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


def write_svg_capabilities(path):
    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="200" viewBox="0 0 800 200">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <g font-family="Segoe UI, Roboto, Arial" font-size="14" fill="#0b2545">
    <rect x="20" y="20" width="220" height="140" rx="8" fill="#f1f5f9" stroke="#e2e8f0"/>
    <text x="40" y="50" font-weight="700">Omni Gateway</text>
    <text x="40" y="74">Unified predict / crawl / analyze</text>

    <rect x="280" y="20" width="220" height="140" rx="8" fill="#f8fafc" stroke="#e2e8f0"/>
    <text x="300" y="50" font-weight="700">Autonomous Pipelines</text>
    <text x="300" y="74">Agent-driven builders & monitors</text>

    <rect x="540" y="20" width="220" height="140" rx="8" fill="#f8fafc" stroke="#e2e8f0"/>
    <text x="560" y="50" font-weight="700">Doc Evolution</text>
    <text x="560" y="74">Safe / read-only / live modes</text>
  </g>
</svg>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


def write_svg_timeline(path):
    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="120" viewBox="0 0 1000 120">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <g stroke="#e2e8f0" stroke-width="2" fill="none">
    <line x1="40" y1="60" x2="960" y2="60" />
  </g>
  <g font-family="Segoe UI, Roboto, Arial" font-size="12" fill="#0b2545">
    <circle cx="140" cy="60" r="10" fill="#0b2545"/>
    <text x="120" y="90">MVP: Gateway + Scraper</text>
    <circle cx="420" cy="60" r="10" fill="#0b2545"/>
    <text x="400" y="90">Autonomy + Predictors</text>
    <circle cx="700" cy="60" r="10" fill="#0b2545"/>
    <text x="680" y="90">Doc Evolution Integration</text>
  </g>
</svg>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


def generate_packet(staging_dir, report, summaries):
    ensure_assets_dir()
    cover_path = os.path.join(ASSETS_DIR, "cover.svg")
    caps_path = os.path.join(ASSETS_DIR, "capabilities.svg")
    timeline_path = os.path.join(ASSETS_DIR, "timeline.svg")
    write_svg_cover(
        "Infinity XOS — Strategic Investor Packet",
        "mcp: Omni Gateway & Autonomy Platform",
        cover_path,
    )
    write_svg_capabilities(caps_path)
    write_svg_timeline(timeline_path)

    now = datetime.datetime.utcnow().isoformat() + "Z"

    lines = []
    lines.append("# Infinity XOS — Strategic Investor Packet")
    lines.append(f"Generated: {now} (UTC)")
    lines.append("")
    lines.append("![Cover](assets/investor_packet/cover.svg)")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(
        textwrap.dedent(
            """
        The `mcp` Omni Gateway provides a secure, enterprise-grade orchestration platform that unifies crawling, prediction, and autonomous execution. It is designed for high-trust environments with layered safety gates: doc-evolution operates using a three-mode model (safe, read-only, live) with admin gating and audit trails.
    """
        )
    )

    lines.append("")
    # Key metrics
    total_subsystems = report.get("total_entries", 0)
    missing_readme = report.get("missing_readme", [])
    lines.append("## Key Metrics")
    lines.append(f"- Staging snapshot: `{os.path.basename(staging_dir)}`")
    lines.append(f"- Subsystems scanned: **{total_subsystems}**")
    lines.append(f"- Subsystems missing README: **{len(missing_readme)}**")
    lines.append("")
    lines.append("## Capabilities Overview")
    lines.append("![Capabilities](assets/investor_packet/capabilities.svg)")
    lines.append("")
    # Top highlights from summaries
    lines.append("## Top Highlights — Consolidated Snapshots")
    if summaries:
        for s in summaries[:8]:
            title = s["subsystem"]
            excerpt = s["summary"].strip().splitlines()
            excerpt = [l for l in excerpt if l.strip()]
            snippet = excerpt[0] if excerpt else "No summary available."
            lines.append(f"### {title}")
            lines.append(snippet)
            lines.append("")
    else:
        lines.append(
            "No subsystem summaries available in staging. Please run the read-only consolidation first."
        )

    lines.append("## Roadmap Snapshot")
    lines.append("![Timeline](assets/investor_packet/timeline.svg)")
    lines.append("")
    lines.append("## System Architecture (High Level)")
    lines.append(
        "The platform is composed of: Omni Gateway (API + routing), Intelligence services (predictors, aggregators), Autonomous Orchestrator (agent layer), and Doc Evolution (safe integration)."
    )
    lines.append("")
    lines.append("## Demo Instructions (60s)")
    lines.append("```pwsh")
    lines.append("python api_gateway.py")
    lines.append("python dashboard_api.py")
    lines.append("Start a browser and open: http://localhost:8000/admin")
    lines.append("```")
    lines.append("")
    lines.append("## Security & Governance")
    lines.append("- Doc-Evolution default mode: `safe` (no writes).")
    lines.append(
        "- Recommended: enable `read-only` for review, then `live` after audit + RBAC gating."
    )
    lines.append("")
    lines.append("## Appendix — Consolidation Report")
    lines.append(
        f'Consolidation report file: `{os.path.join(staging_dir, "consolidation-report.json")}`'
    )
    lines.append("")
    # Append small listing of missing readmes
    if missing_readme:
        lines.append("### Missing README (samples)")
        for m in missing_readme[:30]:
            lines.append(f"- {m}")
        lines.append("")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("Generated FAANG-grade investor packet at", OUT_FILE)


def main():
    staging_dir = find_latest_staging()
    if not staging_dir:
        print("No staging snapshots found under", STAGING_ROOT)
        return 2
    report = read_report(staging_dir)
    if not report:
        print("No consolidation report found in", staging_dir)
        return 3
    summaries = gather_summaries(staging_dir)
    generate_packet(staging_dir, report, summaries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
