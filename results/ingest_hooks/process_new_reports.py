"""Ingest hook: run after sync to process new reports.
This script should be run in the context of the results repo and can call back to the MCP repo normalization tools.
"""
import sys
from pathlib import Path
import subprocess

def main():
    print('process_new_reports placeholder - implement per-deployment')

if __name__ == '__main__':
    main()
