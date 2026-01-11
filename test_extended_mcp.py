"""Test extended MCP server"""

import sys

sys.path.insert(0, ".")

print("Loading extended MCP server...")
from main_extended import server

print("\n✓ Extended MCP Server loaded successfully")
print(f"  Name: {server.name}")
print("\n  Available Tools:")
print("    1. execute - Forward to orchestrator")
print("    2. github_create_issue - Create GitHub issues")
print("    3. github_search_code - Search code across repos")
print("    4. github_get_file_content - Get file contents")
print("    5. query_intelligence - Query local intelligence DB")
print("    6. get_portfolio_status - Get trading portfolio")

print("\n  Usage:")
print("    Set GITHUB_TOKEN env var for GitHub tools")
print("    Run: python main_extended.py")
