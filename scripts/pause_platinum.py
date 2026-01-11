import sqlite3

conn = sqlite3.connect("mcp_memory.db")
cur = conn.cursor()
cur.execute(
    "UPDATE jobs SET status='paused' WHERE payload LIKE '%platinum_crawls%' AND status='pending'"
)
print("rows updated", conn.total_changes)
conn.commit()
conn.close()
