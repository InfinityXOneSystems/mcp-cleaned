"""
Hybrid Trading System - AI + Human Partnership
AI makes suggestions, human approves/rejects and can override
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from paper_trading import open_position, close_position, print_account_summary, get_account_summary
from prediction_engine import list_pending

DB_PATH = 'mcp_memory.db'

def get_market_prices():
    """Get current market prices"""
    import random
    base_prices = {
        'BTC': 98500.0, 'ETH': 3600.0, 'SOL': 195.0, 'XRP': 2.35, 'BNB': 695.0,
        'DOGE': 0.32, 'PEPE': 0.000018, 'SHIB': 0.000023, 'BONK': 0.000032, 'WIF': 2.85,
        'MSFT': 445.0, 'AAPL': 252.0, 'JNJ': 158.0, 'KO': 63.5, 'PG': 172.0,
        'GOLD': 2650.0, 'WTI': 71.5, 'SILVER': 30.2, 'NATGAS': 3.45, 'COPPER': 4.15,
        'NVDA': 138.0, 'TSLA': 385.0, 'COIN': 285.0, 'ARKK': 52.0, 'ZM': 78.0,
        'PTON': 6.85, 'RIVN': 12.5, 'PLTR': 78.0, 'DXY': 108.2, 'VIX': 14.8, 'SPY': 595.0,
    }
    
    prices = {}
    for asset, base_price in base_prices.items():
        variation = random.uniform(-0.02, 0.02)
        prices[asset] = base_price * (1 + variation)
    
    return prices


class HybridTrader:
    """AI-Human partnership trading system"""
    
    def __init__(self, account_id: int):
        self.account_id = account_id
        self.ai_confidence_threshold = 60  # AI only suggests 60%+ confidence trades
        self.ai_position_size_base = 0.04  # 4% base allocation
    
    def calculate_ai_position_size(self, confidence: float, account_value: float) -> float:
        """AI calculates recommended position size"""
        kelly_fraction = 0.5
        allocation_pct = (confidence / 100) * kelly_fraction * self.ai_position_size_base
        
        position_size = account_value * allocation_pct
        position_size = max(100, min(position_size, account_value * 0.08))  # $100 min, 8% max
        
        return position_size
    
    def ai_scan_opportunities(self):
        """AI scans for trading opportunities"""
        predictions = list_pending()
        prices = get_market_prices()
        
        # Filter: AI only suggests high-confidence trades
        opportunities = []
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Get assets we already have positions in
        cur.execute("""
            SELECT DISTINCT asset FROM paper_positions
            WHERE account_id = ? AND status = 'open'
        """, (self.account_id,))
        
        open_assets = set(row[0] for row in cur.fetchall())
        conn.close()
        
        for pred in predictions:
            if pred['confidence'] < self.ai_confidence_threshold:
                continue
            
            if pred['asset'] in open_assets:
                continue
            
            if pred['asset'] not in prices:
                continue
            
            opportunities.append(pred)
        
        # Sort by confidence
        opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        
        return opportunities
    
    def ai_check_risk_management(self):
        """AI checks existing positions for risk management"""
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, asset, direction, entry_price, quantity
            FROM paper_positions
            WHERE account_id = ? AND status = 'open'
        """, (self.account_id,))
        
        positions = cur.fetchall()
        conn.close()
        
        prices = get_market_prices()
        alerts = []
        
        for pos_id, asset, direction, entry_price, quantity in positions:
            if asset not in prices:
                continue
            
            current_price = prices[asset]
            
            if direction == 'long':
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = ((entry_price - current_price) / entry_price) * 100
            
            # AI risk thresholds
            if pnl_pct <= -7:
                alerts.append({
                    'position_id': pos_id,
                    'asset': asset,
                    'action': 'CLOSE',
                    'reason': f'Stop loss triggered: {pnl_pct:.2f}% loss',
                    'severity': 'HIGH',
                    'current_price': current_price,
                    'pnl_pct': pnl_pct
                })
            elif pnl_pct >= 10:
                alerts.append({
                    'position_id': pos_id,
                    'asset': asset,
                    'action': 'CONSIDER_CLOSE',
                    'reason': f'Take profit opportunity: {pnl_pct:.2f}% gain',
                    'severity': 'MEDIUM',
                    'current_price': current_price,
                    'pnl_pct': pnl_pct
                })
            elif pnl_pct <= -5:
                alerts.append({
                    'position_id': pos_id,
                    'asset': asset,
                    'action': 'MONITOR',
                    'reason': f'Position down {pnl_pct:.2f}%, approaching stop loss',
                    'severity': 'LOW',
                    'current_price': current_price,
                    'pnl_pct': pnl_pct
                })
        
        return alerts
    
    def present_ai_recommendations(self):
        """Present AI recommendations to human for approval"""
        summary = get_account_summary(self.account_id)
        prices = get_market_prices()
        
        print(f"\n{'='*90}")
        print("🤖💼 HYBRID TRADING SESSION - AI RECOMMENDATIONS")
        print(f"{'='*90}\n")
        
        # Risk management alerts
        alerts = self.ai_check_risk_management()
        
        if alerts:
            print("🚨 AI RISK MANAGEMENT ALERTS:")
            print(f"{'-'*90}")
            
            for alert in alerts:
                severity_icon = '🔴' if alert['severity'] == 'HIGH' else '🟡' if alert['severity'] == 'MEDIUM' else '🔵'
                print(f"{severity_icon} Position #{alert['position_id']} - {alert['asset']}")
                print(f"   Action: {alert['action']}")
                print(f"   Reason: {alert['reason']}")
                print(f"   Current Price: ${alert['current_price']:,.6f}")
                print()
            
            print(f"{'-'*90}\n")
            
            # Let human decide on alerts
            for alert in alerts:
                if alert['severity'] == 'LOW':
                    continue  # Don't ask for monitoring alerts
                
                print(f"\n🤖 AI recommends: {alert['action']} for {alert['asset']}")
                print(f"   {alert['reason']}")
                
                decision = input("   Your decision (close/keep/skip): ").strip().lower()
                
                if decision == 'close':
                    reason = input("   Reason for closing: ")
                    close_position(alert['position_id'], alert['current_price'], reason, 'hybrid')
                    print("   ✅ Position closed")
                elif decision == 'keep':
                    print("   ✅ Position kept open")
                else:
                    print("   ⏭️  Skipped")
        
        # New opportunities
        opportunities = self.ai_scan_opportunities()
        
        if opportunities:
            print(f"\n💡 AI FOUND {len(opportunities)} NEW OPPORTUNITIES:")
            print(f"{'-'*90}")
            
            for i, pred in enumerate(opportunities[:5], 1):  # Show top 5
                asset = pred['asset']
                price = prices[asset]
                recommended_size = self.calculate_ai_position_size(pred['confidence'], summary['total_value'])
                
                print(f"\n{i}. {asset} ({pred['asset_type'].upper()})")
                print(f"   Direction: {pred['predicted_direction'].upper()}")
                print(f"   AI Confidence: {pred['confidence']:.0f}%")
                print(f"   Current Price: ${price:,.6f}")
                print(f"   Recommended Size: ${recommended_size:,.2f} ({(recommended_size/summary['total_value']*100):.1f}% of portfolio)")
                print(f"   Rationale: {pred['rationale'][:80]}...")
                print(f"   Target Date: {pred['target_date']}")
            
            print(f"\n{'-'*90}\n")
            
            # Let human approve/modify/reject each opportunity
            for pred in opportunities[:5]:
                asset = pred['asset']
                price = prices[asset]
                recommended_size = self.calculate_ai_position_size(pred['confidence'], summary['current_cash'])
                
                if recommended_size > summary['current_cash']:
                    continue
                
                print(f"\n🤖 AI suggests: {pred['predicted_direction'].upper()} {asset} @ ${price:,.6f}")
                print(f"   Confidence: {pred['confidence']:.0f}% | Size: ${recommended_size:,.2f}")
                
                decision = input("   Your decision (approve/modify/reject): ").strip().lower()
                
                if decision == 'approve':
                    reason = f"Hybrid: AI {pred['confidence']:.0f}% conf, Human approved - {pred['rationale'][:80]}"
                    open_position(
                        account_id=self.account_id,
                        asset=asset,
                        asset_type=pred['asset_type'],
                        direction=pred['predicted_direction'],
                        entry_price=price,
                        position_size=recommended_size,
                        entry_reason=reason,
                        execution_method='hybrid'
                    )
                    summary['current_cash'] -= recommended_size
                    print("   ✅ Trade executed at AI recommendation")
                
                elif decision == 'modify':
                    custom_size = float(input(f"   Enter your position size (max ${summary['current_cash']:,.2f}): $"))
                    
                    if custom_size > summary['current_cash']:
                        print("   ❌ Insufficient cash")
                        continue
                    
                    custom_reason = input("   Your reasoning: ")
                    reason = f"Hybrid: AI {pred['confidence']:.0f}% conf, Human modified - {custom_reason}"
                    
                    open_position(
                        account_id=self.account_id,
                        asset=asset,
                        asset_type=pred['asset_type'],
                        direction=pred['predicted_direction'],
                        entry_price=price,
                        position_size=custom_size,
                        entry_reason=reason,
                        execution_method='hybrid'
                    )
                    summary['current_cash'] -= custom_size
                    print("   ✅ Trade executed with your modifications")
                
                else:
                    print("   ❌ Trade rejected")
        
        else:
            print("\n💡 AI found no new opportunities meeting confidence threshold\n")
        
        print(f"\n{'='*90}\n")


def hybrid_session(account_id: int):
    """Run a hybrid trading session"""
    print_account_summary(account_id)
    
    trader = HybridTrader(account_id)
    trader.present_ai_recommendations()
    
    print("\n✅ Hybrid trading session complete!")
    print_account_summary(account_id)


if __name__ == '__main__':
    # Hybrid account is ID 3
    hybrid_session(3)
