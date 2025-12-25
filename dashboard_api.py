"""
API endpoints for interactive trading dashboard
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime
from typing import List, Dict

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = 'mcp_memory.db'
CHAT_LOG: List[Dict] = []


def add_chat_message(role: str, text: str):
    CHAT_LOG.append({
        "role": role,
        "text": text,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    # keep log manageable
    if len(CHAT_LOG) > 200:
        del CHAT_LOG[:50]


# seed chat with a status line
add_chat_message("system", "System online. Ready for commands.")

# Serve dashboard HTML at root
@app.get("/")
async def root():
    with open("command_center_spa.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/dashboard.html")
async def dashboard():
    with open("command_center_spa.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/command-center")
async def command_center():
    with open("command_center_spa.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/command_center.html")
async def command_center_html():
    with open("command_center_spa.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/command_center")
async def command_center_alt():
    with open("command_center_spa.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# ===== CHAT ENDPOINTS =====

@app.get("/api/chat")
async def get_chat():
    return {"messages": CHAT_LOG}


@app.post("/api/chat")
async def post_chat(payload: dict):
    role = payload.get("role")
    text = payload.get("text")
    if role not in {"user", "assistant", "system"}:
        raise HTTPException(status_code=400, detail="Invalid role")
    if not text or not isinstance(text, str):
        raise HTTPException(status_code=400, detail="Text required")
    add_chat_message(role, text.strip())
    return {"status": "ok", "messages": CHAT_LOG}

# ===== BANK ACCOUNT ENDPOINTS =====

@app.get("/api/bank")
def get_bank_balance():
    """Get current bank balance"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT current_balance FROM paper_accounts WHERE id = 1
    """)
    row = cur.fetchone()
    conn.close()
    
    if row:
        return {
            'balance': row[0],
            'account_id': 1,
            'account_name': 'AI Automated'
        }
    return {'balance': 0, 'error': 'Account not found'}


@app.post("/api/bank/deposit")
def deposit(amount: float):
    """Deposit funds into bank account"""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE paper_accounts 
        SET current_balance = current_balance + ?, updated_at = ?
        WHERE id = 1
    """, (amount, datetime.now().isoformat()))
    
    conn.commit()
    
    cur.execute("SELECT current_balance FROM paper_accounts WHERE id = 1")
    new_balance = cur.fetchone()[0]
    conn.close()
    
    return {'balance': new_balance, 'deposited': amount}


@app.post("/api/bank/withdraw")
def withdraw(amount: float):
    """Withdraw funds from bank"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT current_balance FROM paper_accounts WHERE id = 1")
    current = cur.fetchone()[0]
    
    if amount > current:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Insufficient funds. Available: ${current:.2f}")
    
    cur.execute("""
        UPDATE paper_accounts 
        SET current_balance = current_balance - ?, updated_at = ?
        WHERE id = 1
    """, (amount, datetime.now().isoformat()))
    
    conn.commit()
    
    cur.execute("SELECT current_balance FROM paper_accounts WHERE id = 1")
    new_balance = cur.fetchone()[0]
    conn.close()
    
    return {'balance': new_balance, 'withdrawn': amount}


@app.post("/api/bank/set")
def set_balance(amount: float):
    """Directly set bank balance (admin function)"""
    if amount < 0:
        raise HTTPException(status_code=400, detail="Balance cannot be negative")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT current_balance FROM paper_accounts WHERE id = 1")
    old_balance = cur.fetchone()[0]
    
    cur.execute("""
        UPDATE paper_accounts 
        SET current_balance = ?, updated_at = ?
        WHERE id = 1
    """, (amount, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return {'old_balance': old_balance, 'new_balance': amount, 'changed_by': amount - old_balance}


# ===== PORTFOLIO ENDPOINTS =====

@app.get("/api/portfolio")
def get_portfolio():
    """Get current portfolio with P&L"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Account summary
    cur.execute("""
        SELECT current_balance, starting_balance FROM paper_accounts WHERE id = 1
    """)
    balance_row = cur.fetchone()
    cash, starting = balance_row if balance_row else (0, 0)
    
    # Open positions
    cur.execute("""
        SELECT id, asset, direction, entry_price, quantity, position_size, opened_at
        FROM paper_positions
        WHERE account_id = 1 AND status = 'open'
        ORDER BY position_size DESC
    """)
    
    positions = []
    total_positions_value = 0
    
    # Mock prices for demo
    prices = {
        'BTC': 98500.0, 'ETH': 3600.0, 'SOL': 195.0, 'XRP': 2.35, 'BNB': 695.0,
        'DOGE': 0.32, 'PEPE': 0.000018, 'SHIB': 0.000023, 'BONK': 0.000032, 'WIF': 2.85,
        'MSFT': 445.0, 'AAPL': 252.0, 'JNJ': 158.0, 'KO': 63.5, 'PG': 172.0,
        'GOLD': 2650.0, 'WTI': 71.5, 'SILVER': 30.2, 'NATGAS': 3.45, 'COPPER': 4.15,
        'NVDA': 138.0, 'TSLA': 385.0, 'COIN': 285.0, 'ARKK': 52.0, 'ZM': 78.0,
        'PTON': 6.85, 'RIVN': 12.5, 'PLTR': 78.0, 'DXY': 108.2, 'VIX': 14.8, 'SPY': 595.0,
    }
    
    import random
    for pos in cur.fetchall():
        pos_id, asset, direction, entry_price, quantity, pos_size, opened = pos
        
        # Simulate price movement
        current_price = prices.get(asset, entry_price)
        current_price *= (1 + random.uniform(-0.05, 0.05))
        
        if direction == 'long':
            current_value = current_price * quantity
            pnl = current_value - pos_size
            pnl_pct = (pnl / pos_size) * 100
        else:
            current_value = pos_size - (current_price * quantity)
            pnl = current_value - pos_size
            pnl_pct = (pnl / pos_size) * 100
        
        positions.append({
            'id': pos_id,
            'asset': asset,
            'direction': direction,
            'entry_price': entry_price,
            'current_price': current_price,
            'quantity': quantity,
            'entry_value': pos_size,
            'current_value': current_value,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'opened_at': opened
        })
        
        total_positions_value += current_value
    
    conn.close()
    
    return {
        'cash_balance': cash,
        'positions_value': total_positions_value,
        'total_value': cash + total_positions_value,
        'starting_balance': starting,
        'total_pnl': (cash + total_positions_value) - starting,
        'total_pnl_pct': ((cash + total_positions_value) - starting) / starting * 100 if starting > 0 else 0,
        'positions': positions,
        'num_positions': len(positions)
    }


@app.post("/api/portfolio/add-position")
def add_position(asset: str, direction: str, price: float, quantity: float):
    """Add a new position from bank balance"""
    if quantity <= 0 or price <= 0:
        raise HTTPException(status_code=400, detail="Price and quantity must be positive")
    
    if direction not in ['long', 'short']:
        raise HTTPException(status_code=400, detail="Direction must be 'long' or 'short'")
    
    position_size = price * quantity
    
    # Check available funds
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT current_balance FROM paper_accounts WHERE id = 1")
    available = cur.fetchone()[0]
    
    if position_size > available:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Insufficient funds: need ${position_size:.2f}, have ${available:.2f}")
    
    # Deduct from cash
    cur.execute("""
        UPDATE paper_accounts 
        SET current_balance = current_balance - ?, updated_at = ?
        WHERE id = 1
    """, (position_size, datetime.now().isoformat()))
    
    # Add position
    cur.execute("""
        INSERT INTO paper_positions (account_id, asset, asset_type, direction, entry_price, position_size, quantity, opened_at, status, entry_reason)
        VALUES (?, ?, 'manual', ?, ?, ?, ?, ?, 'open', 'Manual entry via dashboard')
    """, (1, asset, direction, price, position_size, quantity, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return {
        'success': True,
        'asset': asset,
        'direction': direction,
        'entry_price': price,
        'quantity': quantity,
        'position_size': position_size
    }


# ===== TRADING MODE ENDPOINTS =====

@app.post("/api/mode/auto")
def start_auto_mode():
    """Start AI auto-trading"""
    import subprocess
    import threading
    
    def run_trader():
        subprocess.Popen(['python', 'scripts/ai_auto_trader.py', '--account-id', '1', '--loop', '--interval', '60'])
    
    thread = threading.Thread(target=run_trader, daemon=True)
    thread.start()
    
    return {'status': 'auto-trader started', 'mode': 'FULL AUTO'}


@app.post("/api/mode/hybrid")
def start_hybrid_mode():
    """Start hybrid mode"""
    return {
        'status': 'ready',
        'mode': 'HYBRID',
        'message': 'Run: python scripts/hybrid_trader.py'
    }


@app.post("/api/mode/manual")
def start_manual_mode():
    """Start manual trading"""
    return {
        'status': 'ready',
        'mode': 'MANUAL',
        'message': 'Run: python scripts/human_trader.py'
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8001)
