"""Helper to fetch secrets from Google Secret Manager and write to a local file.
Usage:
  from integrations.gcp_secret import fetch_secret_to_file
  fetch_secret_to_file('my-secret', project='my-gcp-project', out_path='.secrets/workspace-sa.json')
"""
from __future__ import annotations
import os
from typing import Optional

def fetch_secret_to_file(secret_name: str, project: Optional[str] = None, version: str = 'latest', out_path: Optional[str] = None) -> str:
    """Fetch a secret's payload from Google Secret Manager and write it to out_path.

    Returns the absolute path to the written file.
    Raises RuntimeError on errors.
    """
    try:
        from google.cloud import secretmanager
    except Exception as e:
        raise RuntimeError(f"google-cloud-secret-manager library is not installed: {e}")

    project = project or os.environ.get('GCP_PROJECT') or os.environ.get('FIRESTORE_PROJECT')
    if not project:
        raise RuntimeError('GCP project not provided via argument or GCP_PROJECT / FIRESTORE_PROJECT env var')

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project}/secrets/{secret_name}/versions/{version}"

    try:
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data
    except Exception as e:
        raise RuntimeError(f"failed to access secret {name}: {e}")

    out_dir = out_path or os.path.join(os.getcwd(), '.secrets', f'{secret_name}.json')
    out_dir = os.path.abspath(out_dir)
    os.makedirs(os.path.dirname(out_dir), exist_ok=True)

    try:
        # write binary payload
        with open(out_dir, 'wb') as fh:
            fh.write(payload)
    except Exception as e:
        raise RuntimeError(f"failed to write secret to {out_dir}: {e}")

    return out_dir


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('secret', help='Secret name in Secret Manager')
    parser.add_argument('--project', help='GCP project id (or set GCP_PROJECT env var)')
    parser.add_argument('--out', help='Output file path (defaults to .secrets/<secret>.json)')
    parser.add_argument('--version', default='latest')
    args = parser.parse_args()
    path = fetch_secret_to_file(args.secret, project=args.project, version=args.version, out_path=args.out)
    print(path)
