"""
Master Trading Dashboard
Initialize accounts, run all three trading systems, compare performance
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_trading import init_trading_tables, create_account, print_account_summary, get_account_summary
import sqlite3

DB_PATH = 'mcp_memory.db'

def initialize_all_accounts():
    """Initialize the three trading accounts"""
    print("\n" + "="*80)
    print("🚀 INITIALIZING PAPER TRADING EXPERIMENT")
    print("="*80 + "\n")
    
    init_trading_tables()
    
    # Create three accounts with $5,000 each
    ai_account = create_account("AI Automated", "ai_automated", 5000.0)
    human_account = create_account("Human Manual", "human_manual", 5000.0)
    hybrid_account = create_account("Hybrid Partnership", "hybrid_partnership", 5000.0)
    
    print("\n✅ All accounts initialized!\n")
    
    return ai_account, human_account, hybrid_account


def compare_performance():
    """Compare performance across all three accounts"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT id, account_name FROM paper_accounts ORDER BY id")
    accounts = cur.fetchall()
    conn.close()
    
    if not accounts:
        print("No accounts found. Run initialization first.")
        return
    
    print("\n" + "="*100)
    print("📊 THREE-WAY PERFORMANCE COMPARISON")
    print("="*100 + "\n")
    
    summaries = []
    for acc_id, name in accounts:
        summary = get_account_summary(acc_id)
        if summary:
            summaries.append(summary)
    
    # Print comparison table
    print(f"{'Metric':<25} {'AI Automated':<25} {'Human Manual':<25} {'Hybrid Partnership':<25}")
    print("-"*100)
    
    metrics = [
        ('Starting Balance', 'starting_balance', '${:,.2f}'),
        ('Current Value', 'total_value', '${:,.2f}'),
        ('Total P&L', 'total_pnl', '${:+,.2f}'),
        ('Total P&L %', 'total_pnl_pct', '{:+.2f}%'),
        ('Realized P&L', 'realized_pnl', '${:+,.2f}'),
        ('Cash Balance', 'current_cash', '${:,.2f}'),
        ('Open Positions', 'open_positions', '{}'),
        ('Closed Trades', 'total_trades', '{}'),
        ('Win Rate', 'win_rate', '{:.1f}%'),
        ('Avg P&L/Trade', 'avg_pnl', '${:+,.2f}'),
    ]
    
    for metric_name, key, fmt in metrics:
        values = []
        for summary in summaries:
            if key == 'open_positions':
                value = len(summary.get('open_positions', []))
            else:
                value = summary.get(key, 0)
            
            values.append(fmt.format(value))
        
        print(f"{metric_name:<25} {values[0]:<25} {values[1] if len(values) > 1 else 'N/A':<25} {values[2] if len(values) > 2 else 'N/A':<25}")
    
    print("="*100 + "\n")
    
    # Determine winner
    if len(summaries) >= 3:
        pnls = [(s['name'], s['total_pnl_pct']) for s in summaries]
        pnls.sort(key=lambda x: x[1], reverse=True)
        
        print(f"🏆 CURRENT LEADER: {pnls[0][0]} with {pnls[0][1]:+.2f}% return\n")


def show_detailed_summaries():
    """Show detailed summary for each account"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id FROM paper_accounts ORDER BY id")
    accounts = [row[0] for row in cur.fetchall()]
    conn.close()
    
    for acc_id in accounts:
        print_account_summary(acc_id)


def main_menu():
    """Main dashboard menu"""
    while True:
        print("\n" + "="*80)
        print("📊 PAPER TRADING MASTER DASHBOARD")
        print("="*80)
        print("1. Initialize All Accounts (First Time Setup)")
        print("2. Allocate Portfolio to AI Account")
        print("3. Run AI Auto-Trader (Single Run)")
        print("4. Run AI Auto-Trader (Continuous Loop)")
        print("5. Open Human Trading Interface")
        print("6. Run Hybrid Trading Session")
        print("7. Compare All Accounts Performance")
        print("8. Show Detailed Account Summaries")
        print("9. Exit")
        print("="*80)
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            initialize_all_accounts()
            show_detailed_summaries()
            
        elif choice == '2':
            print("\n🤖 Running portfolio allocation for AI account...")
            os.system("python scripts/allocate_portfolio.py")
            
        elif choice == '3':
            print("\n🤖 Running AI Auto-Trader (single execution)...")
            os.system("python scripts/ai_auto_trader.py --account-id 1")
            
        elif choice == '4':
            interval = input("Enter loop interval in seconds (default 300): ").strip()
            interval = interval if interval else "300"
            print(f"\n🤖 Starting AI Auto-Trader continuous loop (every {interval}s)...")
            print("Press Ctrl+C to stop\n")
            os.system(f"python scripts/ai_auto_trader.py --account-id 1 --loop --interval {interval}")
            
        elif choice == '5':
            print("\n👤 Opening Human Trading Interface...")
            os.system("python scripts/human_trader.py")
            
        elif choice == '6':
            print("\n🤝 Running Hybrid Trading Session...")
            os.system("python scripts/hybrid_trader.py")
            
        elif choice == '7':
            compare_performance()
            input("\nPress Enter to continue...")
            
        elif choice == '8':
            show_detailed_summaries()
            input("\nPress Enter to continue...")
            
        elif choice == '9':
            print("\n👋 Exiting dashboard. Happy trading!")
            break
            
        else:
            print("❌ Invalid option")
            input("Press Enter to continue...")


if __name__ == '__main__':
    main_menu()
