"""
Smart Portfolio Allocation System
Allocates $5k across predictions based on confidence, risk, and diversification
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_trading import open_position, get_account_summary
from prediction_engine import list_pending
import sqlite3

DB_PATH = 'mcp_memory.db'

def get_current_prices():
    """Mock current prices - in production would fetch live data"""
    return {
        # Major Crypto
        'BTC': 98500.0,
        'ETH': 3600.0,
        'SOL': 195.0,
        'XRP': 2.35,
        'BNB': 695.0,
        
        # Meme Coins
        'DOGE': 0.32,
        'PEPE': 0.000018,
        'SHIB': 0.000023,
        'BONK': 0.000032,
        'WIF': 2.85,
        
        # Blue Chip Stocks
        'MSFT': 445.0,
        'AAPL': 252.0,
        'JNJ': 158.0,
        'KO': 63.5,
        'PG': 172.0,
        
        # Commodities (per unit)
        'GOLD': 2650.0,
        'WTI': 71.5,
        'SILVER': 30.2,
        'NATGAS': 3.45,
        'COPPER': 4.15,
        
        # Other Stocks
        'NVDA': 138.0,
        'TSLA': 385.0,
        'COIN': 285.0,
        'ARKK': 52.0,
        'ZM': 78.0,
        'PTON': 6.85,
        'RIVN': 12.5,
        'PLTR': 78.0,
        
        # Indices
        'DXY': 108.2,
        'VIX': 14.8,
        'SPY': 595.0,
    }


def get_all_pending_predictions():
    """Get all pending predictions with full details"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, asset, asset_type, predicted_direction, confidence, rationale, target_date
        FROM predictions
        WHERE status = 'pending'
        ORDER BY confidence DESC
    """)
    
    predictions = []
    for row in cur.fetchall():
        predictions.append({
            'id': row[0],
            'asset': row[1],
            'asset_type': row[2],
            'predicted_direction': row[3],
            'confidence': row[4],
            'rationale': row[5],
            'target_date': row[6]
        })
    
    conn.close()
    return predictions


def calculate_allocation(total_capital: float = 5000.0):
    """
    Calculate optimal position sizes based on:
    - Confidence level (higher confidence = larger position)
    - Asset type (diversification across asset classes)
    - Risk tier (conservative = smaller positions, aggressive = larger)
    - Kelly Criterion principles (position size proportional to edge)
    """
    predictions = get_all_pending_predictions()
    
    if not predictions:
        print("No pending predictions to allocate")
        return []
    
    # Categorize by asset type
    asset_types = {}
    for pred in predictions:
        asset_type = pred['asset_type']
        if asset_type not in asset_types:
            asset_types[asset_type] = []
        asset_types[asset_type].append(pred)
    
    # Base allocation per asset type (diversification)
    type_allocation = {
        'cryptocurrency': 0.35,  # 35% to crypto
        'stock': 0.30,           # 30% to stocks
        'commodity': 0.20,       # 20% to commodities
        'forex': 0.05,           # 5% to forex
        'index': 0.10,           # 10% to indices
    }
    
    allocations = []
    
    for asset_type, pct_allocation in type_allocation.items():
        if asset_type not in asset_types:
            continue
        
        type_predictions = asset_types[asset_type]
        type_capital = total_capital * pct_allocation
        
        # Within each type, allocate based on confidence
        total_confidence = sum(p['confidence'] for p in type_predictions)
        
        for pred in type_predictions:
            # Base allocation proportional to confidence
            confidence_weight = pred['confidence'] / total_confidence if total_confidence > 0 else 1.0 / len(type_predictions)
            base_amount = type_capital * confidence_weight
            
            # Risk adjustment
            # High confidence (>70%) = full allocation
            # Medium confidence (60-70%) = 80% allocation
            # Lower confidence (<60%) = 60% allocation
            if pred['confidence'] >= 70:
                risk_multiplier = 1.0
            elif pred['confidence'] >= 60:
                risk_multiplier = 0.8
            else:
                risk_multiplier = 0.6
            
            final_amount = base_amount * risk_multiplier
            
            # Minimum position size filter ($50)
            if final_amount < 50:
                final_amount = 50
            
            allocations.append({
                'prediction_id': pred['id'],
                'asset': pred['asset'],
                'asset_type': pred['asset_type'],
                'direction': pred['predicted_direction'],
                'confidence': pred['confidence'],
                'allocation_pct': (final_amount / total_capital) * 100,
                'allocation_usd': final_amount,
                'rationale': pred['rationale'][:80] + '...' if len(pred['rationale']) > 80 else pred['rationale']
            })
    
    # Sort by allocation size
    allocations.sort(key=lambda x: x['allocation_usd'], reverse=True)
    
    return allocations


def execute_allocation(account_id: int, allocations: list, execution_method: str = 'ai_auto'):
    """Execute the allocation plan by opening positions"""
    prices = get_current_prices()
    
    print(f"\n{'='*80}")
    print(f"🤖 EXECUTING ALLOCATION FOR ACCOUNT {account_id} ({execution_method.upper()})")
    print(f"{'='*80}\n")
    
    total_allocated = 0
    positions_opened = 0
    
    for alloc in allocations:
        asset = alloc['asset']
        
        if asset not in prices:
            print(f"⚠️  Skipping {asset} - price not available")
            continue
        
        price = prices[asset]
        position_size = alloc['allocation_usd']
        
        reason = f"{alloc['confidence']:.0f}% confidence - {alloc['rationale']}"
        
        position_id = open_position(
            account_id=account_id,
            asset=asset,
            asset_type=alloc['asset_type'],
            direction=alloc['direction'],
            entry_price=price,
            position_size=position_size,
            entry_reason=reason,
            execution_method=execution_method
        )
        
        if position_id:
            total_allocated += position_size
            positions_opened += 1
    
    print(f"\n✅ Allocation complete: {positions_opened} positions opened, ${total_allocated:,.2f} allocated\n")


def print_allocation_plan(allocations: list):
    """Print the allocation plan before execution"""
    print(f"\n{'='*80}")
    print(f"📋 PORTFOLIO ALLOCATION PLAN")
    print(f"{'='*80}\n")
    
    total = sum(a['allocation_usd'] for a in allocations)
    
    print(f"{'Asset':<8} {'Type':<15} {'Dir':<6} {'Conf':<6} {'Amount':<12} {'%':<8} {'Rationale'}")
    print(f"{'-'*80}")
    
    for a in allocations:
        print(f"{a['asset']:<8} {a['asset_type']:<15} {a['direction']:<6} "
              f"{a['confidence']:>4.0f}%  ${a['allocation_usd']:>9,.2f}  "
              f"{a['allocation_pct']:>6.2f}%  {a['rationale'][:35]}")
    
    print(f"{'-'*80}")
    print(f"{'TOTAL':<8} {'':<15} {'':<6} {'':<6} ${total:>9,.2f}  {(total/5000*100):>6.2f}%")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    # Calculate optimal allocation
    allocations = calculate_allocation(5000.0)
    
    if not allocations:
        print("No allocations generated")
        sys.exit(1)
    
    # Show the plan
    print_allocation_plan(allocations)
    
    # Get account IDs
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, account_name FROM paper_accounts ORDER BY id")
    accounts = cur.fetchall()
    conn.close()
    
    if not accounts:
        print("No accounts found. Run paper_trading.py first to create accounts.")
        sys.exit(1)
    
    print("Available accounts:")
    for acc_id, name in accounts:
        print(f"  {acc_id}: {name}")
    
    print("\nReady to execute allocation for AI Automated account (ID 1)")
    response = input("Execute now? (y/n): ")
    
    if response.lower() == 'y':
        execute_allocation(1, allocations, 'ai_auto')
        
        from paper_trading import print_account_summary
        print_account_summary(1)
    else:
        print("Allocation plan saved. Execute manually when ready.")
