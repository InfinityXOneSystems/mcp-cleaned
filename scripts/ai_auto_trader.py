"""
AI Auto-Trader - Fully Automated Trading System
Monitors predictions, executes trades, manages positions without human intervention
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import time

from paper_trading import close_position, get_account_summary, open_position
from prediction_engine import list_pending

DB_PATH = "mcp_memory.db"


class AITrader:
    """Autonomous trading system"""

    def __init__(self, account_id: int):
        self.account_id = account_id
        self.risk_tolerance = 0.02  # 2% max risk per trade
        self.max_positions = 15  # Max concurrent positions
        self.stop_loss_pct = -8.0  # Stop loss at -8%
        self.take_profit_pct = 12.0  # Take profit at +12%

    def get_market_prices(self):
        """Simulate getting real-time prices - in production would call API"""
        # For demo, use static prices with small random variation
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

        # Add small random variation to simulate market movement
        prices = {}
        for asset, base_price in base_prices.items():
            variation = random.uniform(-0.02, 0.02)  # ±2% variation
            prices[asset] = base_price * (1 + variation)

        return prices

    def calculate_position_size(self, confidence: float, account_value: float) -> float:
        """Calculate position size using Kelly Criterion modified for confidence"""
        # Base Kelly: f = (p * b - q) / b, where p = win prob, q = loss prob, b = win/loss ratio
        # Simplified: position_size = confidence_based_allocation

        # Conservative Kelly: use fraction of confidence as position size
        kelly_fraction = 0.5  # Use half Kelly for safety
        base_allocation = (confidence / 100) * kelly_fraction

        # Apply maximum risk limit
        max_allocation = self.risk_tolerance * 2  # Allow up to 4% per trade
        allocation_pct = min(base_allocation, max_allocation)

        position_size = account_value * allocation_pct

        # Minimum $50, maximum 10% of account
        position_size = max(50, min(position_size, account_value * 0.10))

        return position_size

    def should_enter_trade(self, prediction: dict, current_positions: int) -> bool:
        """Decide if we should enter a new trade"""
        # Don't exceed max positions
        if current_positions >= self.max_positions:
            return False

        # Only trade high/medium confidence predictions
        if prediction["confidence"] < 55:
            return False

        # Check if prediction is still valid (not too close to target date)
        # TODO: Add date validation

        return True

    def manage_risk(self, position: dict, current_price: float) -> str:
        """Check if position should be closed for risk management"""
        entry_price = position["entry_price"]
        direction = position["direction"]

        if direction == "long":
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # short
            pnl_pct = ((entry_price - current_price) / entry_price) * 100

        # Stop loss
        if pnl_pct <= self.stop_loss_pct:
            return (
                f"STOP_LOSS: Hit {self.stop_loss_pct}% stop loss (P&L: {pnl_pct:.2f}%)"
            )

        # Take profit
        if pnl_pct >= self.take_profit_pct:
            return (
                f"TAKE_PROFIT: Hit {self.take_profit_pct}% target (P&L: {pnl_pct:.2f}%)"
            )

        return None

    def execute_strategy(self, dry_run: bool = False):
        """Main trading loop - execute strategy"""
        print(f"\n{'='*80}")
        print(f"🤖 AI AUTO-TRADER - Account {self.account_id}")
        print(f"{'='*80}\n")

        # Get account summary
        summary = get_account_summary(self.account_id)
        if not summary:
            print(f"Account {self.account_id} not found")
            return

        print(f"Account: {summary['name']}")
        print(f"Total Value: ${summary['total_value']:,.2f}")
        print(f"Cash: ${summary['current_cash']:,.2f}")
        print(f"Open Positions: {len(summary['open_positions'])}")
        print(f"Win Rate: {summary['win_rate']:.1f}%\n")

        # Get current prices
        prices = self.get_market_prices()

        # Check existing positions for risk management
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, asset, direction, entry_price, quantity, position_size
            FROM paper_positions
            WHERE account_id = ? AND status = 'open'
        """,
            (self.account_id,),
        )

        open_positions = cur.fetchall()

        if open_positions:
            print("📊 MONITORING OPEN POSITIONS:")
            for (
                pos_id,
                asset,
                direction,
                entry_price,
                quantity,
                pos_size,
            ) in open_positions:
                if asset not in prices:
                    continue

                current_price = prices[asset]

                # Check risk management rules
                position_dict = {"entry_price": entry_price, "direction": direction}

                risk_action = self.manage_risk(position_dict, current_price)

                if risk_action:
                    print(f"  🔴 CLOSING {asset}: {risk_action}")
                    if not dry_run:
                        close_position(pos_id, current_price, risk_action, "ai_auto")
                else:
                    # Calculate current P&L
                    if direction == "long":
                        pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    else:
                        pnl_pct = ((entry_price - current_price) / entry_price) * 100

                    print(
                        f"  ✓ {asset}: Entry ${entry_price:.2f} | Current ${current_price:.2f} | P&L {pnl_pct:+.2f}%"
                    )

        # Look for new entry opportunities
        predictions = list_pending()
        current_position_count = len(open_positions)

        # Filter predictions we already have positions for
        cur.execute(
            """
            SELECT DISTINCT asset FROM paper_positions
            WHERE account_id = ? AND status = 'open'
        """,
            (self.account_id,),
        )

        open_assets = set(row[0] for row in cur.fetchall())
        conn.close()

        available_predictions = [
            p for p in predictions if p["asset"] not in open_assets
        ]

        if available_predictions and current_position_count < self.max_positions:
            print(f"\n🔍 SCANNING FOR NEW OPPORTUNITIES:")

            # Sort by confidence
            available_predictions.sort(key=lambda x: x["confidence"], reverse=True)

            for pred in available_predictions[:5]:  # Check top 5 opportunities
                if not self.should_enter_trade(pred, current_position_count):
                    continue

                asset = pred["asset"]
                if asset not in prices:
                    continue

                price = prices[asset]
                position_size = self.calculate_position_size(
                    pred["confidence"], summary["current_cash"]
                )

                if position_size > summary["current_cash"]:
                    print(
                        f"  ⚠️  {asset}: Insufficient cash (need ${position_size:.2f}, have ${summary['current_cash']:.2f})"
                    )
                    continue

                print(f"  🟢 OPPORTUNITY: {asset} @ ${price:.2f}")
                print(f"     Direction: {pred['predicted_direction'].upper()}")
                print(f"     Confidence: {pred['confidence']:.0f}%")
                print(
                    f"     Position Size: ${position_size:.2f} ({(position_size/summary['total_value']*100):.1f}% of portfolio)"
                )
                print(f"     Rationale: {pred['rationale'][:80]}...")

                if not dry_run:
                    reason = f"AI Auto: {pred['confidence']:.0f}% conf - {pred['rationale'][:100]}"
                    open_position(
                        account_id=self.account_id,
                        asset=asset,
                        asset_type=pred["asset_type"],
                        direction=pred["predicted_direction"],
                        entry_price=price,
                        position_size=position_size,
                        entry_reason=reason,
                        execution_method="ai_auto",
                    )
                    current_position_count += 1
                    summary["current_cash"] -= position_size

        print(f"\n{'='*80}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Auto-Trader")
    parser.add_argument("--account-id", type=int, default=1, help="Account ID to trade")
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulation mode - no actual trades"
    )
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Loop interval in seconds (default 300 = 5 min)",
    )

    args = parser.parse_args()

    trader = AITrader(args.account_id)

    if args.loop:
        print(f"🔄 Starting continuous trading loop (interval: {args.interval}s)")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                trader.execute_strategy(dry_run=args.dry_run)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\n⏹️  Trading loop stopped by user")
    else:
        trader.execute_strategy(dry_run=args.dry_run)
