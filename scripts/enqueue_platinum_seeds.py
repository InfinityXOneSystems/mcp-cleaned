import json
import os
import sqlite3

DB = os.environ.get("MCP_MEMORY_DB", "./mcp_memory.db").replace("sqlite:///", "")
print("Using DB:", DB)
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Ensure jobs table exists (schema similar to meta_service)
cur.execute(
    """CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    action TEXT,
    payload TEXT,
    status TEXT,
    result TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)"""
)
conn.commit()

seeds = [
    {"id": "1", "start_url": "https://www.gofundme.com/", "source": "GoFundMe"},
    {
        "id": "2",
        "start_url": "https://www.reddit.com/r/Assistance/",
        "source": "Reddit-Assistance",
    },
    {
        "id": "3",
        "start_url": "https://www.reddit.com/r/gofundme/",
        "source": "Reddit-GoFundMe",
    },
    {
        "id": "4",
        "start_url": "https://www.reddit.com/r/borrow/",
        "source": "Reddit-Borrow",
    },
    {
        "id": "5",
        "start_url": "https://news.google.com/search?q=job+loss+financial+hardship+loan",
        "source": "GoogleNews-FinancialStress",
    },
    {
        "id": "6",
        "start_url": "https://twitter.com/search?q=need%20money%20loan%20urgent",
        "source": "Twitter-X",
    },
    {
        "id": "7",
        "start_url": "https://www.fedsmallbusiness.org/reports/survey",
        "source": "FedSmallBusiness",
    },
    {
        "id": "8",
        "start_url": "https://www.equifax.com/business/product/small-business-indices/",
        "source": "Equifax",
    },
]

DEFAULT_PAYLOAD = {
    "max_pages": 200,
    "max_depth": 2,
    "concurrency": 10,
    "rate_limit": 1.0,
    "namespace": "platinum_crawls",
}

for s in seeds:
    payload = dict(DEFAULT_PAYLOAD)
    payload["start_url"] = s["start_url"]
    payload["source_id"] = s["id"]
    payload["source_name"] = s.get("source")
    pjson = json.dumps(payload)
    cur.execute(
        "INSERT INTO jobs (type, action, payload, status) VALUES (?, ?, ?, 'pending')",
        ("crawler", "crawl/start", pjson),
    )
    print("Enqueued", s["start_url"])

conn.commit()
conn.close()
print("Done enqueuing seeds.")
