"""
Initialize empty MCP database with schema
"""
import sqlite3
from datetime import datetime

DB_PATH = 'mcp_memory.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Memory table for intelligence sources
cur.execute("""
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    value TEXT
)
""")

# Trading tables
cur.execute("""
CREATE TABLE IF NOT EXISTS paper_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    starting_balance REAL NOT NULL,
    current_balance REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS paper_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    asset TEXT NOT NULL,
    asset_type TEXT,
    direction TEXT NOT NULL,
    entry_price REAL NOT NULL,
    position_size REAL NOT NULL,
    quantity REAL NOT NULL,
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    status TEXT NOT NULL,
    entry_reason TEXT,
    exit_reason TEXT,
    exit_price REAL,
    pnl REAL,
    FOREIGN KEY (account_id) REFERENCES paper_accounts(id)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS paper_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    asset TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL,
    quantity REAL NOT NULL,
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    pnl REAL,
    pnl_pct REAL,
    reason TEXT,
    FOREIGN KEY (account_id) REFERENCES paper_accounts(id)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS paper_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    snapshot_time TEXT NOT NULL,
    total_value REAL NOT NULL,
    cash_balance REAL NOT NULL,
    positions_value REAL NOT NULL,
    num_positions INTEGER NOT NULL,
    FOREIGN KEY (account_id) REFERENCES paper_accounts(id)
)
""")

# Predictions table
cur.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset TEXT NOT NULL,
    prediction_type TEXT NOT NULL,
    confidence REAL,
    target_price REAL,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    outcome TEXT
)
""")

# Jobs/crawl queue
cur.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    payload TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    error TEXT
)
""")

conn.commit()
conn.close()

print(f"✓ Database initialized: {DB_PATH}")
print("  Tables: memory, paper_accounts, paper_positions, paper_trades, paper_snapshots, predictions, jobs")
print("\nNext steps:")
print("  1. Run: python scripts/analyze_intelligence.py  # Seed intelligence data")
print("  2. Run: python scripts/seed_accounts.py          # Create demo trading accounts")
