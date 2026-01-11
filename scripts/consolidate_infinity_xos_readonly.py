#!/usr/bin/env python3
"""Read-only consolidation of infinity-xos system_index into a staging folder.
Creates per-subsystem summaries without modifying the external repo.
"""
import datetime
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INFINITY_ROOT = os.path.abspath(r"c:\AI\repos\infinity-xos")
SYSTEM_INDEX = os.path.join(INFINITY_ROOT, "system_index", "docs_index.json")
STAGING_ROOT = os.path.join(ROOT, "staging")


def safe_name(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z._-]", "_", name)


def read_file_if_exists(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def main():
    if not os.path.exists(SYSTEM_INDEX):
        print("system_index docs_index.json not found at", SYSTEM_INDEX)
        return 1

    with open(SYSTEM_INDEX, "r", encoding="utf-8") as f:
        idx = json.load(f)

    now = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    staging_dir = os.path.join(STAGING_ROOT, f"infinity-xos-index-snapshot-{now}")
    os.makedirs(staging_dir, exist_ok=True)

    report = {
        "generated_at": now,
        "total_entries": 0,
        "summaries": [],
        "missing_readme": [],
    }

    entries = idx.get("entries", [])
    report["total_entries"] = len(entries)

    for e in entries:
        name = e.get("name") or e.get("path")
        path = e.get("path")
        snapshots = e.get("snapshots", [])
        safe = safe_name(name)
        outdir = os.path.join(staging_dir, safe)
        os.makedirs(outdir, exist_ok=True)

        summary_lines = []
        summary_lines.append(f"# {name}\n")
        summary_lines.append(f"Path: {path}\n")
        summary_lines.append(f"Snapshots: {len(snapshots)}\n")

        # Try to read README.md in the subsystem path
        candidate_readme = os.path.join(INFINITY_ROOT, path, "README.md")
        readme_text = read_file_if_exists(candidate_readme)
        if readme_text:
            snippet = "\n".join(readme_text.splitlines()[:40])
            summary_lines.append("## README.md snippet:\n")
            summary_lines.append(snippet)
        else:
            # Try snapshots relpath
            if snapshots:
                first = snapshots[0]
                rel = first.get("relpath") or first.get("file")
                if rel:
                    # relpaths in system_index often use backslashes
                    relpath = rel.replace("\\", os.sep).replace("/", os.sep)
                    candidate = os.path.join(INFINITY_ROOT, relpath)
                    txt = read_file_if_exists(candidate)
                    if txt:
                        snippet = "\n".join(txt.splitlines()[:40])
                        summary_lines.append(
                            f'## snapshot {first.get("file","file")} snippet:\n'
                        )
                        summary_lines.append(snippet)
                    else:
                        report["missing_readme"].append(name)
            else:
                report["missing_readme"].append(name)

        # list files under path (non-recursive)
        full_path = os.path.join(INFINITY_ROOT, path)
        files = []
        if os.path.exists(full_path) and os.path.isdir(full_path):
            try:
                files = os.listdir(full_path)
            except Exception:
                files = []

        summary_lines.append("\n## Files (top-level):")
        for fn in files[:200]:
            summary_lines.append(f"- {fn}")

        out_file = os.path.join(outdir, "SUMMARY.md")
        with open(out_file, "w", encoding="utf-8") as of:
            of.write("\n".join(summary_lines))

        report["summaries"].append(
            {
                "name": name,
                "path": path,
                "summary_file": os.path.relpath(out_file, ROOT),
            }
        )

    report_file = os.path.join(staging_dir, "consolidation-report.json")
    with open(report_file, "w", encoding="utf-8") as rf:
        json.dump(report, rf, indent=2)

    print("Consolidation complete. Staging dir:", staging_dir)
    print("Report file:", report_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
