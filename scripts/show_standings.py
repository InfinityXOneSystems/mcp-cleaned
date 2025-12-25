"""
Quick Performance Snapshot
Show current standings of all three accounts
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_trading import get_account_summary
import sqlite3

DB_PATH = 'mcp_memory.db'

def show_standings():
    """Quick visual comparison"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, account_name FROM paper_accounts ORDER BY id")
    accounts = cur.fetchall()
    conn.close()
    
    if not accounts:
        print("No accounts found")
        return
    
    summaries = [get_account_summary(acc_id) for acc_id, _ in accounts]
    
    # Sort by total value
    summaries.sort(key=lambda x: x['total_value'], reverse=True)
    
    print("\n" + "="*80)
    print("🏆 PAPER TRADING LEADERBOARD")
    print("="*80 + "\n")
    
    for i, s in enumerate(summaries, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        
        print(f"{medal} {i}. {s['name'].upper()}")
        print(f"   Portfolio Value: ${s['total_value']:>12,.2f}")
        print(f"   P&L: ${s['total_pnl']:>+12,.2f} ({s['total_pnl_pct']:>+6.2f}%)")
        print(f"   Open Positions: {len(s['open_positions']):>12}")
        print(f"   Win Rate: {s['win_rate']:>11.1f}%")
        print()
    
    print("="*80 + "\n")

if __name__ == '__main__':
    show_standings()
