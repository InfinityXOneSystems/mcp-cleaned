"""
Human Trading Interface
Manual trading system where YOU make all the decisions
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

from paper_trading import (
    close_position,
    get_account_summary,
    open_position,
    print_account_summary,
)
from prediction_engine import list_pending

DB_PATH = "mcp_memory.db"


def get_market_prices():
    """Get current market prices"""
    import random

    base_prices = {
        "BTC": 98500.0,
        "ETH": 3600.0,
        "SOL": 195.0,
        "XRP": 2.35,
        "BNB": 695.0,
        "DOGE": 0.32,
        "PEPE": 0.000018,
        "SHIB": 0.000023,
        "BONK": 0.000032,
        "WIF": 2.85,
        "MSFT": 445.0,
        "AAPL": 252.0,
        "JNJ": 158.0,
        "KO": 63.5,
        "PG": 172.0,
        "GOLD": 2650.0,
        "WTI": 71.5,
        "SILVER": 30.2,
        "NATGAS": 3.45,
        "COPPER": 4.15,
        "NVDA": 138.0,
        "TSLA": 385.0,
        "COIN": 285.0,
        "ARKK": 52.0,
        "ZM": 78.0,
        "PTON": 6.85,
        "RIVN": 12.5,
        "PLTR": 78.0,
        "DXY": 108.2,
        "VIX": 14.8,
        "SPY": 595.0,
    }

    prices = {}
    for asset, base_price in base_prices.items():
        variation = random.uniform(-0.02, 0.02)
        prices[asset] = base_price * (1 + variation)

    return prices


def show_predictions():
    """Display all pending predictions with current prices"""
    predictions = list_pending()
    prices = get_market_prices()

    print(f"\n{'='*90}")
    print("📊 AVAILABLE TRADING OPPORTUNITIES (Based on Predictions)")
    print(f"{'='*90}\n")

    if not predictions:
        print("No pending predictions available")
        return

    # Group by asset type
    by_type = {}
    for pred in predictions:
        asset_type = pred["asset_type"]
        if asset_type not in by_type:
            by_type[asset_type] = []
        by_type[asset_type].append(pred)

    for asset_type, preds in by_type.items():
        print(f"\n{asset_type.upper()}:")
        print(
            f"{'ID':<5} {'Asset':<8} {'Dir':<6} {'Conf':<6} {'Price':<12} {'Target Date':<12} {'Rationale'}"
        )
        print(f"{'-'*90}")

        for pred in preds:
            asset = pred["asset"]
            price = prices.get(asset, 0)
            price_str = f"${price:,.2f}" if price > 1 else f"${price:.6f}"

            print(
                f"{pred['id']:<5} {asset:<8} {pred['predicted_direction']:<6} "
                f"{pred['confidence']:>4.0f}%  {price_str:<12} {pred['target_date']:<12} "
                f"{pred['rationale'][:45]}"
            )

    print(f"\n{'='*90}\n")


def show_open_positions(account_id: int):
    """Display current open positions"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, asset, direction, entry_price, quantity, position_size, opened_at
        FROM paper_positions
        WHERE account_id = ? AND status = 'open'
        ORDER BY opened_at DESC
    """,
        (account_id,),
    )

    positions = cur.fetchall()
    conn.close()

    if not positions:
        print("No open positions")
        return

    prices = get_market_prices()

    print(f"\n{'='*90}")
    print("💼 YOUR OPEN POSITIONS")
    print(f"{'='*90}\n")
    print(
        f"{'ID':<5} {'Asset':<8} {'Dir':<6} {'Entry':<12} {'Current':<12} {'Qty':<12} {'P&L %':<10}"
    )
    print(f"{'-'*90}")

    for (
        pos_id,
        asset,
        direction,
        entry_price,
        quantity,
        pos_size,
        opened_at,
    ) in positions:
        current_price = prices.get(asset, entry_price)

        if direction == "long":
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - current_price) / entry_price) * 100

        entry_str = f"${entry_price:,.2f}" if entry_price > 1 else f"${entry_price:.6f}"
        current_str = (
            f"${current_price:,.2f}" if current_price > 1 else f"${current_price:.6f}"
        )

        pnl_color = "🟢" if pnl_pct > 0 else "🔴" if pnl_pct < 0 else "⚪"

        print(
            f"{pos_id:<5} {asset:<8} {direction:<6} {entry_str:<12} {current_str:<12} "
            f"{quantity:<12.4f} {pnl_color} {pnl_pct:>+6.2f}%"
        )

    print(f"\n{'='*90}\n")


def manual_open_trade(account_id: int):
    """Manually open a new position"""
    show_predictions()

    print("\n🎯 OPEN NEW POSITION")
    print("=" * 50)

    asset = input("Enter asset symbol (e.g., BTC, MSFT): ").strip().upper()

    prices = get_market_prices()
    if asset not in prices:
        print(f"❌ Asset {asset} not found in price data")
        return

    current_price = prices[asset]
    print(f"Current price: ${current_price:,.6f}")

    direction = input("Direction (long/short): ").strip().lower()
    if direction not in ["long", "short"]:
        print("❌ Invalid direction. Must be 'long' or 'short'")
        return

    summary = get_account_summary(account_id)
    print(f"Available cash: ${summary['current_cash']:,.2f}")

    position_size = float(input("Position size (USD): $"))

    if position_size > summary["current_cash"]:
        print(f"❌ Insufficient cash. You have ${summary['current_cash']:,.2f}")
        return

    reason = input("Reason for trade: ")

    # Confirm
    print(f"\n📋 TRADE SUMMARY:")
    print(f"  Asset: {asset}")
    print(f"  Direction: {direction.upper()}")
    print(f"  Price: ${current_price:,.6f}")
    print(f"  Position Size: ${position_size:,.2f}")
    print(f"  Quantity: {position_size/current_price:.4f}")
    print(f"  Reason: {reason}")

    confirm = input("\nExecute this trade? (y/n): ")

    if confirm.lower() == "y":
        # Get asset type from predictions or default to 'stock'
        asset_type = "stock"
        predictions = list_pending()
        for pred in predictions:
            if pred["asset"] == asset:
                asset_type = pred["asset_type"]
                break

        open_position(
            account_id=account_id,
            asset=asset,
            asset_type=asset_type,
            direction=direction,
            entry_price=current_price,
            position_size=position_size,
            entry_reason=reason,
            execution_method="human_manual",
        )
        print("\n✅ Trade executed!")
    else:
        print("❌ Trade cancelled")


def manual_close_trade(account_id: int):
    """Manually close an existing position"""
    show_open_positions(account_id)

    position_id = int(input("\nEnter position ID to close: "))

    # Get position details
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT asset, direction, entry_price, quantity, position_size
        FROM paper_positions
        WHERE id = ? AND account_id = ? AND status = 'open'
    """,
        (position_id, account_id),
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        print("❌ Position not found or already closed")
        return

    asset, direction, entry_price, quantity, pos_size = row

    prices = get_market_prices()
    current_price = prices.get(asset, entry_price)

    # Calculate P&L
    exit_value = current_price * quantity
    if direction == "long":
        pnl = exit_value - pos_size
        pnl_pct = (pnl / pos_size) * 100
    else:
        pnl = pos_size - exit_value
        pnl_pct = (pnl / pos_size) * 100

    print(f"\n📋 CLOSING POSITION:")
    print(f"  Asset: {asset}")
    print(f"  Direction: {direction.upper()}")
    print(f"  Entry Price: ${entry_price:,.6f}")
    print(f"  Exit Price: ${current_price:,.6f}")
    print(f"  Quantity: {quantity:.4f}")
    print(f"  P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%)")

    reason = input("\nReason for closing: ")
    confirm = input("Confirm close? (y/n): ")

    if confirm.lower() == "y":
        close_position(position_id, current_price, reason, "human_manual")
        print("\n✅ Position closed!")
    else:
        print("❌ Close cancelled")


def main_menu(account_id: int):
    """Main trading interface menu"""
    while True:
        print_account_summary(account_id)

        print("\n" + "=" * 50)
        print("👤 HUMAN MANUAL TRADING INTERFACE")
        print("=" * 50)
        print("1. View Trading Opportunities (Predictions)")
        print("2. View Open Positions")
        print("3. Open New Position")
        print("4. Close Position")
        print("5. Refresh Account Summary")
        print("6. Exit")
        print("=" * 50)

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            show_predictions()
            input("\nPress Enter to continue...")
        elif choice == "2":
            show_open_positions(account_id)
            input("\nPress Enter to continue...")
        elif choice == "3":
            manual_open_trade(account_id)
            input("\nPress Enter to continue...")
        elif choice == "4":
            manual_close_trade(account_id)
            input("\nPress Enter to continue...")
        elif choice == "5":
            continue  # Loop will refresh
        elif choice == "6":
            print("\n👋 Exiting trading interface")
            break
        else:
            print("❌ Invalid option")
            input("Press Enter to continue...")


if __name__ == "__main__":
    # Human account is ID 2
    main_menu(2)
