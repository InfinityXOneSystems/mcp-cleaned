import sqlite3
import os
DB = os.environ.get('MCP_MEMORY_DB', './mcp_memory.db').replace('sqlite:///', '')

def run():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    print('Jobs:')
    for row in cur.execute('SELECT id,type,action,payload,status,result,created_at FROM jobs ORDER BY created_at DESC LIMIT 20'):
        print(row)
    print('\nMemory:')
    for row in cur.execute('SELECT id,namespace,key,value FROM memory ORDER BY id DESC LIMIT 20'):
        print(row[0], row[1], row[2])
    conn.close()

if __name__ == '__main__':
    run()
