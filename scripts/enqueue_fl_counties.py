import json
import os
import sqlite3

DB = os.environ.get("MCP_MEMORY_DB", "./mcp_memory.db").replace("sqlite:///", "")

counties = [
    ("St Lucie County, FL", "https://www.stlucieco.gov/"),
    ("Martin County, FL", "https://www.martin.fl.us/"),
    ("Palm Beach County, FL", "https://discover.pbcgov.org/"),
    ("Okeechobee County, FL", "https://www.co.okeechobee.fl.us/"),
]


def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)


def enqueue():
    conn = get_conn()
    cur = conn.cursor()
    for name, url in counties:
        payload = {
            "start_url": url,
            "max_pages": 20,
            "max_depth": 1,
            "concurrency": 3,
            "rate_limit": 0.5,
            "namespace": f"fl_county_{name.split()[0].lower()}",
        }
        cur.execute(
            "INSERT INTO jobs (type, action, payload, status) VALUES (?,?,?,?)",
            ("crawler", "crawl/start", json.dumps(payload), "pending"),
        )
        print("Enqueued", name, url)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    enqueue()
