#!/usr/bin/env python3
"""Bundle OpenAPI specs into a single archive for CustomGPT ingestion."""
import os
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'openapi-bundle.zip')
FILES = [
    os.path.join(ROOT, 'openapi', 'omni-gateway.yaml'),
    os.path.join(ROOT, 'openapi', 'orchestrator.yaml'),
]

def main():
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in FILES:
            if os.path.exists(f):
                z.write(f, os.path.join('openapi', os.path.basename(f)))
    print('Wrote', OUT)

if __name__ == '__main__':
    main()
