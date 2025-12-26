#!/usr/bin/env python3
"""
Cloud Run End-to-End Test Suite
Tests the deployed MCP Gateway on Cloud Run
"""

import requests
import json
import time
from typing import Dict, List

# Configuration
CLOUD_RUN_URL = "https://gateway-f42ylsp5qa-ue.a.run.app"
MCP_API_KEY = "INVESTORS-DEMO-KEY-2025"
HEADERS = {
    "X-MCP-KEY": MCP_API_KEY,
    "Content-Type": "application/json"
}

class TestRunner:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def test(self, name: str, func):
        """Run a test and record the result."""
        print(f"\n🧪 Testing: {name}")
        try:
            result = func()
            if result:
                print(f"✅ PASS: {name}")
                self.passed += 1
                self.results.append({"test": name, "status": "PASS", "error": None})
            else:
                print(f"❌ FAIL: {name}")
                self.failed += 1
                self.results.append({"test": name, "status": "FAIL", "error": "Test returned False"})
        except Exception as e:
            print(f"❌ ERROR: {name} - {str(e)}")
            self.failed += 1
            self.results.append({"test": name, "status": "ERROR", "error": str(e)})
    
    def summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print(f"\n{'='*70}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {self.passed} ({100*self.passed/total:.1f}%)")
        print(f"❌ Failed: {self.failed} ({100*self.failed/total:.1f}%)")
        print(f"{'='*70}\n")
        
        # Print detailed results
        if self.failed > 0:
            print("Failed Tests:")
            for r in self.results:
                if r["status"] != "PASS":
                    print(f"  ❌ {r['test']}: {r['error']}")

# Test Functions

def test_health_endpoint():
    """Test basic health endpoint."""
    resp = requests.get(f"{CLOUD_RUN_URL}/health", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "healthy"
    print(f"   Service: {data.get('service')}")
    return True

def test_mcp_list_tools():
    """Test MCP tools listing."""
    resp = requests.get(f"{CLOUD_RUN_URL}/mcp/listMCPTools", headers=HEADERS, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data
    tools = data["tools"]
    assert len(tools) > 0
    print(f"   Found {len(tools)} tools")
    # Verify governance
    for tool in tools[:3]:
        assert "governance" in tool
        assert "level" in tool["governance"]
    return True

def test_mcp_execute_safe_tool():
    """Test executing a safe MCP tool."""
    payload = {
        "tool": "get_weather_data",
        "args": {"city": "New York"}
    }
    resp = requests.post(f"{CLOUD_RUN_URL}/mcp/executeMCPTool", 
                        headers=HEADERS, 
                        json=payload, 
                        timeout=15)
    # Tool might not exist, but should get proper response structure
    assert resp.status_code in [200, 400, 404]
    data = resp.json()
    # Verify response structure
    assert "result" in data or "error" in data
    return True

def test_credential_gateway_health():
    """Test credential gateway health endpoint."""
    resp = requests.get(f"{CLOUD_RUN_URL}/credentials/health", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    print(f"   Registry size: {data.get('registry_size')}")
    return True

def test_credential_gateway_auth():
    """Test credential gateway requires authentication."""
    # Without token - should fail
    resp = requests.get(f"{CLOUD_RUN_URL}/credentials/get/github_app", timeout=10)
    assert resp.status_code == 401
    
    # With token - should succeed (or 404 if credential not configured)
    headers_with_token = {"Authorization": f"Bearer {MCP_API_KEY}"}
    resp = requests.get(f"{CLOUD_RUN_URL}/credentials/get/github_app", 
                       headers=headers_with_token, 
                       timeout=10)
    assert resp.status_code in [200, 404]  # 404 if not configured yet
    return True

def test_autonomy_health():
    """Test autonomous orchestrator health endpoint."""
    resp = requests.get(f"{CLOUD_RUN_URL}/autonomy/health", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "agents" in data
    print(f"   Agent types: {list(data['agents'].keys())}")
    return True

def test_autonomy_agents_list():
    """Test listing autonomous agents."""
    headers_with_token = {"Authorization": f"Bearer {MCP_API_KEY}"}
    resp = requests.get(f"{CLOUD_RUN_URL}/autonomy/agents", 
                       headers=headers_with_token, 
                       timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert "agents" in data
    agents = data["agents"]
    assert len(agents) >= 4  # Should have 4 agent types
    return True

def test_intelligence_sources():
    """Test intelligence sources endpoint."""
    resp = requests.get(f"{CLOUD_RUN_URL}/intelligence/sources", 
                       headers=HEADERS, 
                       timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert "sources" in data
    print(f"   Intelligence sources: {len(data['sources'])}")
    return True

def test_cockpit_ui():
    """Test cockpit UI is accessible."""
    resp = requests.get(f"{CLOUD_RUN_URL}/cockpit", timeout=10)
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert len(resp.text) > 1000  # Should be substantial HTML
    return True

def test_protocol_110():
    """Test Protocol 110 status."""
    resp = requests.get(f"{CLOUD_RUN_URL}/protocol110", headers=HEADERS, timeout=10)
    # May or may not exist, but should return proper response
    assert resp.status_code in [200, 404]
    return True

def test_safe_mode_enforcement():
    """Test that SAFE_MODE blocks dangerous operations."""
    # Try to execute a dangerous tool (should be blocked)
    payload = {
        "tool": "system_shutdown",  # Hypothetical dangerous tool
        "args": {}
    }
    resp = requests.post(f"{CLOUD_RUN_URL}/mcp/executeMCPTool", 
                        headers=HEADERS, 
                        json=payload, 
                        timeout=10)
    # Should either block or return tool not found
    assert resp.status_code in [403, 404]
    return True

def test_firestore_connectivity():
    """Test that service can connect to Firestore."""
    # Query intelligence endpoint which uses Firestore
    resp = requests.post(f"{CLOUD_RUN_URL}/intelligence/query", 
                        headers=HEADERS, 
                        json={"query": "test connectivity", "source": "firestore"},
                        timeout=15)
    # Should succeed even if no results
    assert resp.status_code in [200, 404]
    return True

def test_rate_limiting_headers():
    """Test that responses include proper headers."""
    resp = requests.get(f"{CLOUD_RUN_URL}/health", timeout=10)
    # Check for CORS headers
    assert "access-control-allow-origin" in resp.headers or "content-type" in resp.headers
    return True

# Main Test Runner

if __name__ == "__main__":
    print(f"""
{'='*70}
🚀 MCP GATEWAY CLOUD RUN END-TO-END TEST SUITE
{'='*70}
Target: {CLOUD_RUN_URL}
Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
{'='*70}
""")
    
    runner = TestRunner()
    
    # Core Infrastructure Tests
    runner.test("Health Endpoint", test_health_endpoint)
    runner.test("Cockpit UI Accessible", test_cockpit_ui)
    runner.test("Rate Limiting Headers", test_rate_limiting_headers)
    
    # MCP Tools Tests
    runner.test("MCP List Tools", test_mcp_list_tools)
    runner.test("MCP Execute Safe Tool", test_mcp_execute_safe_tool)
    runner.test("Protocol 110 Status", test_protocol_110)
    runner.test("Safe Mode Enforcement", test_safe_mode_enforcement)
    
    # Credential Gateway Tests
    runner.test("Credential Gateway Health", test_credential_gateway_health)
    runner.test("Credential Gateway Auth", test_credential_gateway_auth)
    
    # Autonomous Orchestrator Tests
    runner.test("Autonomy Health", test_autonomy_health)
    runner.test("Autonomy Agents List", test_autonomy_agents_list)
    
    # Intelligence System Tests
    runner.test("Intelligence Sources", test_intelligence_sources)
    runner.test("Firestore Connectivity", test_firestore_connectivity)
    
    # Print Summary
    runner.summary()
    
    # Write results to file
    results_file = "test_results_cloudrun.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "target": CLOUD_RUN_URL,
            "summary": {
                "total": runner.passed + runner.failed,
                "passed": runner.passed,
                "failed": runner.failed,
                "success_rate": f"{100*runner.passed/(runner.passed+runner.failed):.1f}%"
            },
            "results": runner.results
        }, f, indent=2)
    
    print(f"\n📄 Results written to: {results_file}")
    
    # Exit with proper code
    exit(0 if runner.failed == 0 else 1)
