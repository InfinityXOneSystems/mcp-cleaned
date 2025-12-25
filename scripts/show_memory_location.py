import sqlite3

conn = sqlite3.connect('mcp_memory.db')
cur = conn.cursor()

print("\n📁 MEMORY STORAGE LOCATION")
print("=" * 60)
print(f"Database: C:\\AI\\repos\\mcp\\mcp_memory.db")
print()

# Tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print("📊 Tables:")
for t in tables:
    print(f"  • {t}")
print()

# Memory table stats
print("💾 MEMORY TABLE (crawled data):")
print("-" * 60)
cur.execute("SELECT COUNT(DISTINCT namespace) FROM memory")
total_ns = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM memory")
total_records = cur.fetchone()[0]
print(f"  Total namespaces: {total_ns}")
print(f"  Total records: {total_records:,}")
print()

# Top namespaces
cur.execute("""
    SELECT namespace, COUNT(*) as count 
    FROM memory 
    GROUP BY namespace 
    ORDER BY count DESC 
    LIMIT 15
""")
print("  Top 15 namespaces by record count:")
for row in cur.fetchall():
    print(f"    {row[0]:<30} {row[1]:>6,} records")
print()

# Jobs table
print("⚙️  JOBS TABLE (crawl tasks):")
print("-" * 60)
cur.execute("""
    SELECT status, COUNT(*) as count
    FROM jobs
    GROUP BY status
    ORDER BY count DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:<15} {row[1]:>4} jobs")
print()

# Predictions table
cur.execute("SELECT COUNT(*) FROM predictions")
pred_count = cur.fetchone()[0]
print("🔮 PREDICTIONS TABLE (asset predictions):")
print("-" * 60)
print(f"  Total predictions: {pred_count}")
if pred_count > 0:
    cur.execute("""
        SELECT status, COUNT(*) 
        FROM predictions 
        GROUP BY status
    """)
    for row in cur.fetchall():
        print(f"    {row[0]}: {row[1]}")

print()
print("=" * 60)
print("\n💡 Access this data:")
print("  • Web API: http://localhost:8000/memory/list (POST with namespace)")
print("  • Python: from prediction_engine import get_stats")
print("  • Direct SQL: sqlite3 mcp_memory.db")
print()

conn.close()
