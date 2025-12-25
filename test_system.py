"""
Comprehensive MCP System Test
Tests: Database, APIs, Endpoints, Data Flows
"""
import sys
import sqlite3
import httpx
import asyncio
import time
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_test(name, status, details=""):
    symbol = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
    print(f"{symbol} {name}")
    if details:
        print(f"  {Colors.BLUE}{details}{Colors.END}")

def log_section(name):
    print(f"\n{Colors.YELLOW}{'='*60}\n{name}\n{'='*60}{Colors.END}")

# ===== DATABASE TESTS =====
def test_database():
    log_section("DATABASE TESTS")
    try:
        conn = sqlite3.connect('mcp_memory.db')
        cur = conn.cursor()
        
        # Check tables exist
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        expected = ['memory', 'jobs', 'predictions', 'paper_accounts', 'paper_positions', 'paper_trades', 'paper_snapshots']
        
        missing = [t for t in expected if t not in tables]
        if missing:
            log_test("Database Schema", False, f"Missing tables: {missing}")
            return False
        log_test("Database Schema", True, f"All {len(expected)} tables exist")
        
        # Check memory records
        cur.execute("SELECT COUNT(*) FROM memory")
        memory_count = cur.fetchone()[0]
        log_test("Memory Records", memory_count > 0, f"{memory_count} records")
        
        # Check accounts
        cur.execute("SELECT COUNT(*) FROM paper_accounts")
        accounts_count = cur.fetchone()[0]
        log_test("Paper Accounts", accounts_count > 0, f"{accounts_count} accounts")
        
        # Check positions
        cur.execute("SELECT COUNT(*) FROM paper_positions")
        positions_count = cur.fetchone()[0]
        log_test("Paper Positions", positions_count >= 0, f"{positions_count} positions")
        
        conn.close()
        return True
    except Exception as e:
        log_test("Database Connection", False, str(e))
        return False

# ===== API TESTS =====
async def test_apis():
    log_section("API TESTS")
    
    # Test Dashboard API
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get('http://localhost:8001/api/portfolio')
            if r.status_code == 200:
                data = r.json()
                log_test("Dashboard API - Portfolio", True, f"Total value: ${data.get('total_value', 0):.2f}, Positions: {data.get('num_positions', 0)}")
            else:
                log_test("Dashboard API - Portfolio", False, f"Status {r.status_code}")
    except Exception as e:
        log_test("Dashboard API - Portfolio", False, f"Not running or error: {str(e)[:50]}")
    
    # Test Chat endpoint
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get('http://localhost:8001/api/chat')
            if r.status_code == 200:
                data = r.json()
                log_test("Dashboard API - Chat", True, f"{len(data.get('messages', []))} messages")
            else:
                log_test("Dashboard API - Chat", False, f"Status {r.status_code}")
    except Exception as e:
        log_test("Dashboard API - Chat", False, f"Not running: {str(e)[:50]}")
    
    # Test Intelligence API
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get('http://localhost:8002/api/intelligence/categories')
            if r.status_code == 200:
                data = r.json()
                total_sources = sum(sum(subcats.values()) for subcats in data.values())
                log_test("Intelligence API - Categories", True, f"{len(data)} categories, {total_sources} total sources")
            else:
                log_test("Intelligence API - Categories", False, f"Status {r.status_code}")
    except Exception as e:
        log_test("Intelligence API - Categories", False, f"Not running: {str(e)[:50]}")
    
    # Test Intelligence Sources
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get('http://localhost:8002/api/intelligence/sources')
            if r.status_code == 200:
                data = r.json()
                log_test("Intelligence API - Sources", True, f"{data.get('count', 0)} sources available")
            else:
                log_test("Intelligence API - Sources", False, f"Status {r.status_code}")
    except Exception as e:
        log_test("Intelligence API - Sources", False, f"Not running: {str(e)[:50]}")

# ===== SPA TESTS =====
async def test_spa():
    log_section("SPA TESTS")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get('http://localhost:8001/')
            if r.status_code == 200:
                content = r.text
                checks = [
                    ('Has Chart.js', 'chart.js' in content),
                    ('Has Trading Tab', 'Trading Dashboard' in content),
                    ('Has Intelligence Tab', 'Intelligence' in content),
                    ('Has Predictions Tab', 'Predictions' in content),
                    ('Has Chat', 'chatMessages' in content),
                    ('Has Portfolio Grid', 'performanceChart' in content)
                ]
                for check_name, passed in checks:
                    log_test(f"SPA - {check_name}", passed)
            else:
                log_test("SPA Loading", False, f"Status {r.status_code}")
    except Exception as e:
        log_test("SPA Loading", False, f"Dashboard API not running: {str(e)[:50]}")

# ===== DATA FLOW TESTS =====
async def test_data_flows():
    log_section("DATA FLOW TESTS")
    
    # Test chat post
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post('http://localhost:8001/api/chat', json={'role': 'user', 'text': 'Test message'})
            if r.status_code == 200:
                log_test("Chat Message Post", True, "Message sent successfully")
            else:
                log_test("Chat Message Post", False, f"Status {r.status_code}")
    except Exception as e:
        log_test("Chat Message Post", False, str(e)[:50])
    
    # Test intelligence preview
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Get first source
            r = await client.get('http://localhost:8002/api/intelligence/sources?category=&subcategory=')
            if r.status_code == 200:
                sources = r.json().get('sources', [])
                if sources:
                    source_id = sources[0]['id']
                    r2 = await client.get(f'http://localhost:8002/api/intelligence/preview/{source_id}')
                    if r2.status_code == 200:
                        preview = r2.json()
                        log_test("Intelligence Preview", True, f"Loaded preview for source {source_id}")
                    else:
                        log_test("Intelligence Preview", False, f"Status {r2.status_code}")
                else:
                    log_test("Intelligence Preview", False, "No sources available")
    except Exception as e:
        log_test("Intelligence Preview", False, str(e)[:50])

# ===== MCP SERVER TEST =====
def test_mcp_server():
    log_section("MCP SERVER TEST")
    
    import os
    # Check main.py exists
    if os.path.exists('main.py'):
        log_test("MCP Server File", True, "main.py exists")
        
        # Check mcp.json
        if os.path.exists('mcp.json'):
            log_test("MCP Config", True, "mcp.json exists")
            import json
            with open('mcp.json') as f:
                config = json.load(f)
                log_test("MCP Tools Defined", len(config.get('tools', [])) > 0, f"{len(config.get('tools', []))} tools")
        else:
            log_test("MCP Config", False, "mcp.json missing")
    else:
        log_test("MCP Server File", False, "main.py missing")

# ===== FILE STRUCTURE TEST =====
def test_file_structure():
    log_section("FILE STRUCTURE TEST")
    
    import os
    
    required_files = [
        'main.py', 'mcp.json', 'requirements.txt', 'README.md',
        'dashboard_api.py', 'intelligence_api.py',
        'command_center_spa.html', '.gitignore',
        'scripts/init_db.py', 'scripts/seed_accounts.py', 'scripts/analyze_intelligence.py'
    ]
    
    for file_path in required_files:
        exists = os.path.exists(file_path)
        log_test(f"File: {file_path}", exists)

# ===== RUN ALL TESTS =====
async def run_all_tests():
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"  MCP COMPREHENSIVE SYSTEM TEST")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{Colors.END}\n")
    
    test_database()
    await test_apis()
    await test_spa()
    await test_data_flows()
    test_mcp_server()
    test_file_structure()
    
    print(f"\n{Colors.GREEN}{'='*60}")
    print(f"  TEST SUITE COMPLETE")
    print(f"{'='*60}{Colors.END}\n")

if __name__ == '__main__':
    asyncio.run(run_all_tests())
