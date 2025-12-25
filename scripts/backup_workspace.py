#!/usr/bin/env python3
"""Create a timestamped zip backup of the `mcp` workspace before large changes."""
import os
import zipfile
import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT_DIR = os.path.join(ROOT, 'backups')
os.makedirs(OUT_DIR, exist_ok=True)

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            arcname = os.path.relpath(fp, os.path.dirname(path))
            ziph.write(fp, arcname)

def main():
    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    out = os.path.join(OUT_DIR, f'mcp-backup-{ts}.zip')
    print('Creating backup:', out)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        zipdir(ROOT, z)
    print('Backup complete')

if __name__ == '__main__':
    main()
