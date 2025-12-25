# Paper Trading Experiment: AI vs Human vs Hybrid

## 🎯 Experiment Overview

Three separate $5,000 paper trading accounts compete to see which strategy performs best:

1. **AI Automated** (Account #1) - 100% autonomous trading
2. **Human Manual** (Account #2) - 100% human controlled  
3. **Hybrid Partnership** (Account #3) - AI suggests, human decides

## 💰 Current Status

**AI Automated**: 21 positions open, $2,773.89 allocated (55.5% deployed)

## 📊 How Each System Works

### 1. AI Automated (Hands-Off)
- **Portfolio allocation**: Smart diversification across asset classes
- **Position sizing**: Kelly Criterion based on confidence levels
- **Risk management**: Auto stop-loss at -8%, take profit at +12%
- **Execution**: Fully autonomous, no human intervention
- **Max positions**: 15 concurrent positions
- **Run**: `python scripts/ai_auto_trader.py --account-id 1 --loop`

**Strategy**:
- 35% cryptocurrency (high conviction plays)
- 30% stocks (mix of growth and defensive)
- 20% commodities (macro diversification)
- 10% indices (market benchmarks)
- 5% forex (directional bets)

**Risk Controls**:
- 2% max risk per trade
- Stop loss triggered at -8%
- Take profit at +12%
- Confidence threshold: 55%+ for entry

### 2. Human Manual (Hands-On)
- **Full control**: YOU make every decision
- **Access to predictions**: View all 32 AI predictions as "research"
- **Manual execution**: Choose assets, directions, position sizes
- **Your judgment**: Decide when to enter and exit
- **Run**: `python scripts/human_trader.py`

**Features**:
- View all pending predictions with confidence scores
- See current market prices
- Monitor open positions with live P&L
- Manual trade entry with customizable position size
- Manual position closing at your discretion

### 3. Hybrid Partnership (50/50 Collaboration)
- **AI recommends**: Scans for opportunities, suggests position sizes
- **You decide**: Approve, modify, or reject each suggestion
- **Risk alerts**: AI monitors positions, alerts you to problems
- **Collaborative**: Best of both worlds
- **Run**: `python scripts/hybrid_trader.py`

**Workflow**:
1. AI scans 32 predictions, filters to high-confidence (60%+)
2. AI calculates recommended position size using Kelly Criterion
3. AI presents top 5 opportunities with rationale
4. YOU choose: Approve / Modify / Reject
5. AI monitors open positions for stop-loss or take-profit
6. AI alerts you, YOU decide whether to close

## 🛠 Available Commands

### Quick Start
```bash
# Initialize all three accounts
python paper_trading.py

# Master dashboard (menu-driven)
python scripts/trading_dashboard.py
```

### AI Automated
```bash
# Single execution (opens new positions, manages existing)
python scripts/ai_auto_trader.py --account-id 1

# Continuous loop (every 5 minutes)
python scripts/ai_auto_trader.py --account-id 1 --loop --interval 300

# Dry run (simulation without actual trades)
python scripts/ai_auto_trader.py --account-id 1 --dry-run
```

### Human Manual
```bash
# Interactive trading interface
python scripts/human_trader.py

# Shows menu:
# 1. View predictions (all 32 opportunities)
# 2. View open positions (with live P&L)
# 3. Open new position (manual entry)
# 4. Close position (exit at current price)
```

### Hybrid Partnership
```bash
# Collaborative trading session
python scripts/hybrid_trader.py

# AI presents recommendations, you approve/modify/reject
```

### Performance Comparison
```bash
# See who's winning
python scripts/trading_dashboard.py
# Choose option 7 for comparison table
```

## 📈 Current AI Portfolio (Account #1)

**21 Positions Opened** - Diversified across:
- **Blue Chip Stocks** (71-75% confidence): MSFT, AAPL, JNJ, PG, KO, NVDA
- **Commodities** (62-66% confidence): GOLD, SILVER, WTI, COPPER, NATGAS
- **Major Crypto** (not yet allocated, coming in BTC/ETH/SOL predictions)
- **Indices** (63-71% confidence): SPY (long), VIX (short)
- **Forex** (70% confidence): DXY (short)
- **Growth/Risk** (48-65% confidence): COIN, PLTR, RIVN, TSLA
- **Shorts** (55-62% confidence): ARKK, ZM, PTON

**Cash Reserve**: $2,226.11 (44.5%) - Available for future opportunities

## 🎮 The Experiment

**Goal**: Discover which approach generates better returns:
1. Pure AI algorithms (speed, discipline, no emotion)
2. Pure human judgment (intuition, experience, flexibility)  
3. AI-Human partnership (data + wisdom)

**Timeline**: Predictions resolve between Dec 31, 2025 - Jan 23, 2025

**Tracking**: All trades logged with timestamps, reasoning, and execution method

**Result**: We'll know definitively which strategy wins after all predictions resolve!

## 🔬 What Makes This Unique

1. **Identical starting capital**: $5,000 each account
2. **Same data**: All three have access to same 32 predictions
3. **Same timeframe**: All trades executed in same market conditions
4. **Different execution**: Only the decision-making differs
5. **Verifiable results**: All tracked in SQLite, timestamped, immutable

## 🚀 Next Steps

1. **Let AI run**: Keep `ai_auto_trader.py --loop` running
2. **You trade**: Use `human_trader.py` whenever you want
3. **Try hybrid**: Run `hybrid_trader.py` for collaborative sessions
4. **Compare daily**: Check `trading_dashboard.py` option 7
5. **Resolve predictions**: As target dates arrive, track accuracy
6. **Final tally**: Jan 23, 2025 - see who won!

## 📊 Database Structure

All data stored in `mcp_memory.db`:
- `paper_accounts` - The three $5k accounts
- `paper_positions` - All open/closed positions
- `paper_trades` - Complete trade log
- `paper_snapshots` - Daily performance snapshots
- `predictions` - 32 asset predictions (already exists)

## 💡 Pro Tips

**For AI Account**:
- Let it run continuously to capture opportunities
- It will auto-manage risk (stop losses, take profits)
- Check performance weekly

**For Human Account**:
- Use predictions as "research reports"
- Trust your gut over AI confidence scores if you disagree
- Document your reasoning (helps you learn)

**For Hybrid Account**:
- Start with AI recommendations
- Modify position sizes based on your risk tolerance
- Override AI when you have conviction

---

**Current Status**: AI fully allocated, Human & Hybrid ready to trade!

**Demo Ready**: Show partner all three dashboards + live comparison table 🎯
