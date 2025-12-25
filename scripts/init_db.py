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

# Sources table for intelligence system
cur.execute("""
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    title TEXT,
    description TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    last_checked TEXT
)
""")

# Portfolio table for trading system
cur.execute("""
CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,
    asset TEXT NOT NULL,
    quantity REAL NOT NULL,
    current_price REAL,
    market_value REAL,
    cost_basis REAL,
    unrealized_pnl REAL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES paper_accounts(id)
)
""")

# Seed demo data for testing
now = datetime.now().isoformat()

# Add demo intelligence sources
demo_sources = [
    ('https://www.sba.gov/funding-programs/loans', 'Business Loans', 'SBA', 'SBA Loan Programs', 'Official SBA loan programs and requirements', now),
    ('https://www.biggerpockets.com', 'Social Sentiment', 'BiggerPockets', 'Real Estate Community', 'Real estate investing community and forums', now),
    ('https://www.realtor.com', 'Real Estate', 'Property Records', 'Property Listings', 'National real estate listings and data', now),
    ('https://www.zillow.com', 'Real Estate', 'Property Records', 'Home Values', 'Home value estimates and market data', now),
    ('https://www.reddit.com/r/realestate', 'Social Sentiment', 'Reddit', 'Real Estate Discussion', 'Real estate discussion forum', now)
]

cur.executemany("""
    INSERT OR IGNORE INTO sources (url, category, subcategory, title, description, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
""", demo_sources)

# Add demo account if none exists
cur.execute("SELECT COUNT(*) FROM paper_accounts")
account_count = cur.fetchone()[0]

if account_count == 0:
    cur.execute("""
        INSERT INTO paper_accounts (account_name, account_type, starting_balance, current_balance, created_at, updated_at)
        VALUES ('Demo Trading Account', 'paper', 100000.0, 100000.0, ?, ?)
    """, (now, now))
    
    account_id = cur.lastrowid
    
    # Add demo portfolio positions
    demo_positions = [
        (account_id, 'AAPL', 10.0, 150.0, 1500.0, 1400.0, 100.0, now),
        (account_id, 'GOOGL', 5.0, 140.0, 700.0, 650.0, 50.0, now),
        (account_id, 'MSFT', 8.0, 380.0, 3040.0, 3000.0, 40.0, now)
    ]
    
    cur.executemany("""
        INSERT INTO portfolio (account_id, asset, quantity, current_price, market_value, cost_basis, unrealized_pnl, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, demo_positions)

conn.commit()
conn.close()

print(f"✓ Database initialized: {DB_PATH}")
print("  Tables: memory, paper_accounts, paper_positions, paper_trades, paper_snapshots, predictions, jobs, sources, portfolio")
print("\nNext steps:")
print("  1. Run: python scripts/analyze_intelligence.py  # Seed intelligence data")
print("  2. Run: python scripts/seed_accounts.py          # Create demo trading accounts")
