import time
import json
import os
import sqlite3
import requests

DB = os.environ.get('MCP_MEMORY_DB', './mcp_memory.db').replace('sqlite:///', '')
POLL = float(os.environ.get('WORKER_POLL', '5'))

def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)


def run_job(row):
    job_id, jtype, action, payload, status, result = row[:6]
    payload = json.loads(payload or '{}')
    try:
        if action == 'repo/create':
            token = payload.get('token')
            name = payload.get('name')
            private = payload.get('private', True)
            if not token or not name:
                raise RuntimeError('Missing token or name')
            r = requests.post('https://api.github.com/user/repos', json={'name':name,'private':private}, headers={'Authorization': f'token {token}','Accept':'application/vnd.github+json'})
            return {'status':'done' if r.status_code<400 else 'error', 'http_status':r.status_code, 'text': r.text}
        else:
            return {'status':'unknown action'}
    except Exception as e:
        return {'status':'error', 'error': str(e)}


if __name__ == '__main__':
    print('GitHub worker starting, DB=',DB)
    while True:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id,type,action,payload,status,result FROM jobs WHERE status='pending' ORDER BY created_at ASC LIMIT 5")
            rows = cur.fetchall()
            for r in rows:
                job_id = r[0]
                print('Processing job', job_id, r[2])
                res = run_job(r)
                cur.execute("UPDATE jobs SET status=?, result=? WHERE id=?", (res.get('status','done'), json.dumps(res), job_id))
                conn.commit()
            conn.close()
        except Exception as e:
            print('Worker error', e)
        time.sleep(POLL)
