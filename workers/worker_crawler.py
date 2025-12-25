import asyncio
import json
import os
import sqlite3

from async_crawler import crawl_url
from safety import filter_allowed_domains, validate_url

DB = os.environ.get('MCP_MEMORY_DB', './mcp_memory.db').replace('sqlite:///', '')
POLL = float(os.environ.get('WORKER_POLL', '2'))


def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)


async def process_job(row):
    job_id, jtype, action, payload, status, result = row[:6]
    payload = json.loads(payload or '{}')
    start = payload.get('start_url')
    if not start:
        return {'status':'error','error':'missing start_url'}
    try:
        start_host = validate_url(start)
    except ValueError as exc:
        return {'status':'error','error': str(exc)}
    max_pages = int(payload.get('max_pages', 100))
    max_depth = int(payload.get('max_depth', 2))
    allowed = filter_allowed_domains(payload.get('allowed_domains'))
    if start_host not in allowed:
        allowed.append(start_host)
    concurrency = int(payload.get('concurrency', 10))
    rate_limit = float(payload.get('rate_limit', 1.0))
    # run crawler
    try:
        results = await crawl_url(start, max_pages=max_pages, max_depth=max_depth, allowed_domains=allowed, concurrency=concurrency, rate_limit=rate_limit)
    except Exception as e:
        return {'status':'error','error': str(e)}
    # store pages into memory table
    conn = get_conn()
    cur = conn.cursor()
    for r in results:
        ns = payload.get('namespace','crawls')
        key = r['url']
        cur.execute("INSERT INTO memory (namespace, key, value) VALUES (?,?,?)", (ns, key, json.dumps({'url': r['url'], 'html': r['html']})))
    conn.commit()
    conn.close()
    return {'status':'done','count': len(results)}


def run_loop():
    print('Crawler worker starting')
    while True:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id,type,action,payload,status,result FROM jobs WHERE status='pending' AND action='crawl/start' ORDER BY created_at ASC LIMIT 1")
            row = cur.fetchone()
            if row:
                job_id = row[0]
                print('Running crawl job', job_id)
                res = asyncio.run(process_job(row))
                cur.execute("UPDATE jobs SET status=?, result=? WHERE id=?", (res.get('status','done'), json.dumps(res), job_id))
                conn.commit()
            conn.close()
        except Exception as e:
            print('Crawler worker error', e)
        import time
        time.sleep(POLL)

if __name__ == '__main__':
    run_loop()
