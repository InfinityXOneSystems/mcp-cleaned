import json
import os
import sqlite3
import time

import requests
from google.oauth2 import service_account

DB = os.environ.get("MCP_MEMORY_DB", "./mcp_memory.db").replace("sqlite:///", "")
POLL = float(os.environ.get("WORKER_POLL", "5"))


def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)


def run_job(row):
    job_id, jtype, action, payload, status, result = row[:6]
    payload = json.loads(payload or "{}")
    try:
        if action == "cloudrun/deploy":
            creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if not creds_path:
                raise RuntimeError("No GOOGLE_APPLICATION_CREDENTIALS")
            # For simplicity, call Cloud Run REST API using oauth2 client access token
            creds = service_account.Credentials.from_service_account_file(
                creds_path, scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            auth = creds.with_scopes(["https://www.googleapis.com/auth/cloud-platform"])
            auth.refresh(requests.Request())
            token = auth.token
            project = payload.get("project")
            region = payload.get("region", "us-central1")
            service_id = payload.get("service_id")
            service_body = payload.get("service")
            url = f"https://run.googleapis.com/v1/projects/{project}/locations/{region}/services?serviceId={service_id}"
            r = requests.post(
                url,
                json=service_body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            return {
                "status": "done" if r.status_code < 400 else "error",
                "http_status": r.status_code,
                "text": r.text,
            }
        else:
            return {"status": "unknown action"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    print("GCloud worker starting, DB=", DB)
    while True:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT id,type,action,payload,status,result FROM jobs WHERE status='pending' ORDER BY created_at ASC LIMIT 5"
            )
            rows = cur.fetchall()
            for r in rows:
                job_id = r[0]
                print("Processing job", job_id, r[2])
                res = run_job(r)
                cur.execute(
                    "UPDATE jobs SET status=?, result=? WHERE id=?",
                    (res.get("status", "done"), json.dumps(res), job_id),
                )
                conn.commit()
            conn.close()
        except Exception as e:
            print("Worker error", e)
        time.sleep(POLL)
