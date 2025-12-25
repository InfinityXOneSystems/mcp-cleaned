"""
Seed demo trading accounts with starting balances
"""
import sqlite3
from datetime import datetime

DB_PATH = 'mcp_memory.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Check if accounts already exist
cur.execute("SELECT COUNT(*) FROM paper_accounts")
count = cur.fetchone()[0]

if count > 0:
    print(f"⚠ Database already has {count} account(s). Skipping seed.")
    conn.close()
    exit(0)

# Create 3 demo accounts
accounts = [
    ('AI Automated', 'ai_automated', 5000.0),
    ('Human Manual', 'human_manual', 5000.0),
    ('Hybrid Partnership', 'hybrid_partnership', 5000.0)
]

now = datetime.now().isoformat()

for name, acct_type, balance in accounts:
    cur.execute("""
        INSERT INTO paper_accounts (account_name, account_type, starting_balance, current_balance, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, acct_type, balance, balance, now, now))

conn.commit()
conn.close()

print("✓ Seeded 3 demo trading accounts:")
print("  1. AI Automated ($5,000)")
print("  2. Human Manual ($5,000)")
print("  3. Hybrid Partnership ($5,000)")
print("\nRun trading scripts to activate accounts:")
print("  python scripts/ai_auto_trader.py --account-id 1")
print("  python scripts/human_trader.py --account-id 2")
print("  python scripts/hybrid_trader.py --account-id 3")
