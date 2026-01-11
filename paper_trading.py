"""
Paper Trading Engine - Three Account Experiment
Account 1: 100% AI Automated
Account 2: 100% Human Manual
Account 3: 50/50 Hybrid Partnership
"""

import sqlite3
from datetime import datetime
from typing import Literal

DB_PATH = "mcp_memory.db"


def init_trading_tables():
    """Create paper trading tables"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Accounts table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS paper_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT UNIQUE NOT NULL,
            account_type TEXT NOT NULL,
            starting_balance REAL NOT NULL,
            current_balance REAL NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """
    )

    # Positions table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS paper_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            asset TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            direction TEXT NOT NULL,
            entry_price REAL NOT NULL,
            position_size REAL NOT NULL,
            quantity REAL NOT NULL,
            opened_at TEXT NOT NULL,
            closed_at TEXT,
            exit_price REAL,
            pnl REAL,
            pnl_pct REAL,
            status TEXT DEFAULT 'open',
            entry_reason TEXT,
            exit_reason TEXT,
            FOREIGN KEY (account_id) REFERENCES paper_accounts(id)
        )
    """
    )

    # Trades log
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            position_id INTEGER,
            trade_type TEXT NOT NULL,
            asset TEXT NOT NULL,
            price REAL NOT NULL,
            quantity REAL NOT NULL,
            value REAL NOT NULL,
            executed_at TEXT NOT NULL,
            execution_method TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (account_id) REFERENCES paper_accounts(id),
            FOREIGN KEY (position_id) REFERENCES paper_positions(id)
        )
    """
    )

    # Performance snapshots
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS paper_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            snapshot_date TEXT NOT NULL,
            total_value REAL NOT NULL,
            cash_balance REAL NOT NULL,
            positions_value REAL NOT NULL,
            daily_pnl REAL,
            total_pnl REAL,
            total_pnl_pct REAL,
            num_positions INTEGER,
            win_rate REAL,
            FOREIGN KEY (account_id) REFERENCES paper_accounts(id)
        )
    """
    )

    conn.commit()
    conn.close()
    print("✓ Paper trading tables initialized")


def create_account(
    name: str,
    account_type: Literal["ai_automated", "human_manual", "hybrid_partnership"],
    starting_balance: float = 5000.0,
) -> int:
    """Create a new paper trading account"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    now = datetime.now().isoformat()

    try:
        cur.execute(
            """
            INSERT INTO paper_accounts (account_name, account_type, starting_balance, current_balance, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (name, account_type, starting_balance, starting_balance, now, now),
        )

        account_id = cur.lastrowid
        conn.commit()
        print(
            f"✓ Account created: {name} (ID: {account_id}) - ${starting_balance:,.2f}"
        )
        return account_id
    except sqlite3.IntegrityError:
        # Account exists, return existing ID
        cur.execute("SELECT id FROM paper_accounts WHERE account_name = ?", (name,))
        account_id = cur.fetchone()[0]
        print(f"✓ Account already exists: {name} (ID: {account_id})")
        return account_id
    finally:
        conn.close()


def open_position(
    account_id: int,
    asset: str,
    asset_type: str,
    direction: Literal["long", "short"],
    entry_price: float,
    position_size: float,
    entry_reason: str = "",
    execution_method: Literal["ai_auto", "human_manual", "hybrid"] = "ai_auto",
):
    """Open a new position"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get account balance
    cur.execute(
        "SELECT current_balance FROM paper_accounts WHERE id = ?", (account_id,)
    )
    balance = cur.fetchone()[0]

    if position_size > balance:
        print(f"✗ Insufficient balance: ${balance:,.2f} < ${position_size:,.2f}")
        conn.close()
        return None

    quantity = position_size / entry_price
    now = datetime.now().isoformat()

    # Create position
    cur.execute(
        """
        INSERT INTO paper_positions (account_id, asset, asset_type, direction, entry_price, position_size, quantity, opened_at, status, entry_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
    """,
        (
            account_id,
            asset,
            asset_type,
            direction,
            entry_price,
            position_size,
            quantity,
            now,
            entry_reason,
        ),
    )

    position_id = cur.lastrowid

    # Log trade
    cur.execute(
        """
        INSERT INTO paper_trades (account_id, position_id, trade_type, asset, price, quantity, value, executed_at, execution_method, notes)
        VALUES (?, ?, 'open', ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            account_id,
            position_id,
            asset,
            entry_price,
            quantity,
            position_size,
            now,
            execution_method,
            entry_reason,
        ),
    )

    # Update account balance
    new_balance = balance - position_size
    cur.execute(
        "UPDATE paper_accounts SET current_balance = ?, updated_at = ? WHERE id = ?",
        (new_balance, now, account_id),
    )

    conn.commit()
    conn.close()

    print(
        f"✓ Opened {direction.upper()} position: {asset} @ ${entry_price:.2f} × {quantity:.4f} = ${position_size:,.2f}"
    )
    return position_id


def close_position(
    position_id: int,
    exit_price: float,
    exit_reason: str = "",
    execution_method: Literal["ai_auto", "human_manual", "hybrid"] = "ai_auto",
):
    """Close an existing position"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get position details
    cur.execute(
        """
        SELECT account_id, asset, direction, entry_price, quantity, position_size
        FROM paper_positions
        WHERE id = ? AND status = 'open'
    """,
        (position_id,),
    )

    row = cur.fetchone()
    if not row:
        print(f"✗ Position {position_id} not found or already closed")
        conn.close()
        return

    account_id, asset, direction, entry_price, quantity, position_size = row

    # Calculate P&L
    exit_value = exit_price * quantity
    if direction == "long":
        pnl = exit_value - position_size
    else:  # short
        pnl = position_size - exit_value

    pnl_pct = (pnl / position_size) * 100
    now = datetime.now().isoformat()

    # Update position
    cur.execute(
        """
        UPDATE paper_positions
        SET exit_price = ?, closed_at = ?, pnl = ?, pnl_pct = ?, status = 'closed', exit_reason = ?
        WHERE id = ?
    """,
        (exit_price, now, pnl, pnl_pct, exit_reason, position_id),
    )

    # Log trade
    cur.execute(
        """
        INSERT INTO paper_trades (account_id, position_id, trade_type, asset, price, quantity, value, executed_at, execution_method, notes)
        VALUES (?, ?, 'close', ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            account_id,
            position_id,
            asset,
            exit_price,
            quantity,
            exit_value,
            now,
            execution_method,
            exit_reason,
        ),
    )

    # Return cash to account
    cur.execute(
        "SELECT current_balance FROM paper_accounts WHERE id = ?", (account_id,)
    )
    balance = cur.fetchone()[0]
    new_balance = balance + exit_value
    cur.execute(
        "UPDATE paper_accounts SET current_balance = ?, updated_at = ? WHERE id = ?",
        (new_balance, now, account_id),
    )

    conn.commit()
    conn.close()

    print(
        f"✓ Closed position: {asset} @ ${exit_price:.2f} | P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%)"
    )
    return pnl


def get_account_summary(account_id: int):
    """Get account performance summary"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Account info
    cur.execute(
        """
        SELECT account_name, account_type, starting_balance, current_balance, created_at
        FROM paper_accounts
        WHERE id = ?
    """,
        (account_id,),
    )

    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    name, acc_type, starting, current_cash, created = row

    # Open positions value
    cur.execute(
        """
        SELECT SUM(position_size) FROM paper_positions WHERE account_id = ? AND status = 'open'
    """,
        (account_id,),
    )
    positions_value = cur.fetchone()[0] or 0

    total_value = current_cash + positions_value
    total_pnl = total_value - starting
    total_pnl_pct = (total_pnl / starting) * 100

    # Closed positions stats
    cur.execute(
        """
        SELECT 
            COUNT(*) as total_trades,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
            AVG(pnl) as avg_pnl,
            SUM(pnl) as realized_pnl
        FROM paper_positions
        WHERE account_id = ? AND status = 'closed'
    """,
        (account_id,),
    )

    trades_row = cur.fetchone()
    total_trades, wins, avg_pnl, realized_pnl = trades_row
    win_rate = (wins / total_trades * 100) if total_trades else 0

    # Open positions
    cur.execute(
        """
        SELECT asset, direction, entry_price, quantity, position_size, opened_at
        FROM paper_positions
        WHERE account_id = ? AND status = 'open'
        ORDER BY opened_at DESC
    """,
        (account_id,),
    )

    open_positions = cur.fetchall()

    conn.close()

    return {
        "name": name,
        "type": acc_type,
        "starting_balance": starting,
        "current_cash": current_cash,
        "positions_value": positions_value,
        "total_value": total_value,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
        "realized_pnl": realized_pnl or 0,
        "total_trades": total_trades or 0,
        "wins": wins or 0,
        "win_rate": win_rate,
        "avg_pnl": avg_pnl or 0,
        "open_positions": open_positions,
        "created_at": created,
    }


def print_account_summary(account_id: int):
    """Print formatted account summary"""
    summary = get_account_summary(account_id)
    if not summary:
        print(f"Account {account_id} not found")
        return

    print(f"\n{'='*70}")
    print(f"📊 {summary['name'].upper()} ({summary['type']})")
    print(f"{'='*70}")
    print(f"Starting Balance:     ${summary['starting_balance']:>12,.2f}")
    print(f"Current Cash:         ${summary['current_cash']:>12,.2f}")
    print(f"Positions Value:      ${summary['positions_value']:>12,.2f}")
    print(f"Total Portfolio:      ${summary['total_value']:>12,.2f}")
    print(
        f"Total P&L:            ${summary['total_pnl']:>12,.2f} ({summary['total_pnl_pct']:+.2f}%)"
    )
    print(f"Realized P&L:         ${summary['realized_pnl']:>12,.2f}")
    print(f"-" * 70)
    print(f"Closed Trades:        {summary['total_trades']:>12}")
    print(f"Win Rate:             {summary['win_rate']:>11.1f}%")
    print(f"Avg P&L per Trade:    ${summary['avg_pnl']:>12,.2f}")
    print(f"-" * 70)
    print(f"Open Positions:       {len(summary['open_positions']):>12}")

    if summary["open_positions"]:
        print()
        for pos in summary["open_positions"]:
            asset, direction, entry, qty, size, opened = pos
            print(
                f"  {direction.upper():<6} {asset:<8} @ ${entry:>8.2f} × {qty:>10.4f} = ${size:>10,.2f}"
            )

    print(f"{'='*70}\n")


if __name__ == "__main__":
    init_trading_tables()

    # Create three accounts
    ai_account = create_account("AI Automated", "ai_automated", 5000.0)
    human_account = create_account("Human Manual", "human_manual", 5000.0)
    hybrid_account = create_account("Hybrid Partnership", "hybrid_partnership", 5000.0)

    print("\n✅ Three paper trading accounts initialized with $5,000 each\n")

    # Show initial state
    for acc_id in [ai_account, human_account, hybrid_account]:
        print_account_summary(acc_id)
