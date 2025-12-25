import sqlite3

conn = sqlite3.connect('mcp_memory.db')
cur = conn.cursor()

# Get tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]
print('=== Database Tables ===')
print(tables)
print()

# Memory records
cur.execute("SELECT COUNT(*) FROM memory")
memory_count = cur.fetchone()[0]
print(f'Memory records: {memory_count}')

# Show sample memory records
cur.execute("SELECT id, key, value FROM memory LIMIT 5")
print('\n=== Sample Memory Records ===')
for row in cur.fetchall():
    print(f'ID: {row[0]} | Key: {row[1][:50]}... | Value length: {len(row[2]) if row[2] else 0} chars')

# Paper accounts
cur.execute("PRAGMA table_info(paper_accounts)")
print('\n=== Paper Accounts Schema ===')
for col in cur.fetchall():
    print(col)

cur.execute("SELECT * FROM paper_accounts LIMIT 3")
print('\n=== Paper Accounts Data ===')
accounts = cur.fetchall()
if accounts:
    for acc in accounts:
        print(acc)
else:
    print('No accounts found')

# Paper positions
cur.execute("SELECT COUNT(*) FROM paper_positions")
positions_count = cur.fetchone()[0]
print(f'\nPaper positions: {positions_count}')

cur.execute("SELECT id, asset, direction, entry_price, quantity, status FROM paper_positions LIMIT 10")
print('\n=== Sample Positions ===')
for row in cur.fetchall():
    print(f'ID: {row[0]} | {row[1]} {row[2]} @ ${row[3]:.2f} x {row[4]:.4f} | Status: {row[5]}')

conn.close()
