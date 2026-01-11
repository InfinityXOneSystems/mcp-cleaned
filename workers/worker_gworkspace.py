import json
import os
import sqlite3
import time

from google.oauth2 import service_account
from googleapiclient.discovery import build

DB = os.environ.get("MCP_MEMORY_DB", "./mcp_memory.db").replace("sqlite:///", "")
POLL = float(os.environ.get("WORKER_POLL", "5"))


def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)


def run_job(row):
    job_id, jtype, action, payload, status, result = row[:6]
    payload = json.loads(payload or "{}")
    try:
        if action == "gmail/send":
            creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if not creds_path:
                raise RuntimeError("No GOOGLE_APPLICATION_CREDENTIALS")
            creds = service_account.Credentials.from_service_account_file(
                creds_path, scopes=["https://www.googleapis.com/auth/gmail.send"]
            )
            service = build("gmail", "v1", credentials=creds)
            message = payload.get("raw")
            # raw should be base64url encoded message
            service.users().messages().send(
                userId="me", body={"raw": message}
            ).execute()
            return {"status": "done"}
        else:
            return {"status": "unknown action"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    print("GWorkspace worker starting, DB=", DB)
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
