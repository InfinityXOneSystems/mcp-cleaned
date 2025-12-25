import sqlite3
import os
import sys
import json
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.worker_crawler import process_job, get_conn

def run_once():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id,type,action,payload,status,result FROM jobs WHERE status='pending' AND action='crawl/start' ORDER BY created_at ASC LIMIT 1")
    row = cur.fetchone()
    if not row:
        print('No pending crawl jobs')
        return
    job_id = row[0]
    print('Processing job', job_id)
    res = asyncio.run(process_job(row))
    cur.execute("UPDATE jobs SET status=?, result=? WHERE id=?", (res.get('status','done'), json.dumps(res), job_id))
    conn.commit()
    conn.close()
    print('Job result', res)

if __name__ == '__main__':
    run_once()
