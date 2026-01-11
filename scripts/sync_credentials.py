"""Preprocess credential files before syncing.

Usage:
  python -m scripts.sync_credentials --src "C:/Users/JARVIS/AppData/Local/InfinityXOne/CredentialManager" --out tmp_sanitized --allowlist allowlist.txt

This script will copy files to an output dir, optionally redact values matching regex patterns defined in allowlist.
"""

import argparse
import re
import shutil
from pathlib import Path


def load_allowlist(path: Path):
    patterns = []
    if not path.exists():
        return patterns
    for line in path.read_text(encoding="utf8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(re.compile(line))
    return patterns


def redact_text(text: str, patterns):
    for p in patterns:
        text = p.sub("REDACTED", text)
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--allowlist", required=False)
    args = parser.parse_args()

    src = Path(args.src)
    out = Path(args.out)
    allow = Path(args.allowlist) if args.allowlist else None
    patterns = load_allowlist(allow) if allow else []

    if not src.exists():
        print("Source not found:", src)
        return 1
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for p in src.rglob("*"):
        if p.is_file():
            rel = p.relative_to(src)
            dest = out / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            txt = p.read_text(encoding="utf8", errors="ignore")
            if patterns:
                txt = redact_text(txt, patterns)
            dest.write_text(txt, encoding="utf8")
            print("Processed", rel)
    print("Sanitized copy written to", out)


if __name__ == "__main__":
    raise SystemExit(main())
