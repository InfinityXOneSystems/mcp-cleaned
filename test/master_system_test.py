#!/usr/bin/env python3
import argparse
import os
from datetime import datetime
from test.framework.runner import run_all, write_master_record
from test.config import SUBSYSTEMS


def main():
    parser = argparse.ArgumentParser(description="Infinity XOS Master System Test")
    parser.add_argument("--mode", choices=["full", "single"], default="full")
    parser.add_argument("--target", help="Subsystem name for single mode", default=None)
    args = parser.parse_args()

    start = datetime.now().isoformat()
    if args.mode == "single" and args.target:
        subsystems = [args.target]
    else:
        subsystems = [f"{name}_test" for name in SUBSYSTEMS]

    results = run_all(subsystems)
    results["meta"] = {"start": start, "mode": args.mode, "subsystems": subsystems}

    out = write_master_record(results)
    print(f"Master system test record written: {out}")


if __name__ == "__main__":
    main()
