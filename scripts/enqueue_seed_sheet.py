import csv
import sqlite3
import os
import json
import sys

DB = os.environ.get('MCP_MEMORY_DB', './mcp_memory.db').replace('sqlite:///', '')

def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)

def enqueue_from_csv(path='scripts/seed_sheet_template.csv'):
    conn = get_conn()
    cur = conn.cursor()
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            url = r['url'].strip()
            if not url:
                continue
            payload = {
                'start_url': url,
                'max_pages': int(r.get('max_pages') or 50),
                'max_depth': int(r.get('max_depth') or 1),
                'concurrency': int(r.get('concurrency') or 3),
                'rate_limit': float(r.get('rate_limit') or 0.5),
                'namespace': r.get('namespace') or r.get('county','seeds').lower().replace(' ','_')
            }
            cur.execute('INSERT INTO jobs (type, action, payload, status) VALUES (?,?,?,?)', (
                'crawler', 'crawl/start', json.dumps(payload), 'pending'
            ))
            print('Enqueued', r.get('county'), r.get('source_name'), url)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'scripts/seed_sheet_template.csv'
    enqueue_from_csv(path)
