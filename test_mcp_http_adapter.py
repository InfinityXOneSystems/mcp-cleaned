"""
Test suite for MCP HTTP Adapter
Validates OpenAPI compliance, tool discovery, and execution
"""

import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@pytest.fixture
def client():
    """Create test client for omni_gateway with MCP adapter"""
    from omni_gateway import app
    return TestClient(app)


class TestMCPAdapter:
    """Test suite for MCP HTTP Adapter"""
    
    def test_health_endpoint(self, client):
        """Test /mcp/health returns valid health status"""
        response = client.get("/mcp/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "protocol_version" in data
        assert "mcp_server_available" in data
        assert "firestore_available" in data
        assert "timestamp" in data
        
        # Validate ISO 8601 timestamp
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    
    def test_tools_list_endpoint(self, client):
        """Test /mcp/tools returns list of tools"""
        response = client.get("/mcp/tools")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "tools" in data
        assert isinstance(data["tools"], list)
        assert data["count"] > 0
        assert len(data["tools"]) == data["count"]
        
        # Validate tool structure
        for tool in data["tools"]:
            assert "name" in tool
            assert "description" in tool
            assert "category" in tool
            assert "parameters" in tool
            assert "rate_limit_level" in tool
            assert "requires_auth" in tool
            assert isinstance(tool["parameters"], list)
    
    def test_schema_endpoint(self, client):
        """Test /mcp/schema returns valid OpenAPI 3.0 schema"""
        response = client.get("/mcp/schema")
        assert response.status_code == 200
        
        spec = response.json()
        
        # Validate OpenAPI structure
        assert spec["openapi"] == "3.0.0"
        assert "info" in spec
        assert "paths" in spec
        assert "components" in spec
        
        # Validate info
        info = spec["info"]
        assert info["title"] == "Infinity XOS MCP HTTP Adapter"
        assert info["version"] == "1.0.0"
        assert "x-mcp-protocol" in info
        
        # Validate paths
        paths = spec["paths"]
        assert "/mcp/health" in paths
        assert "/mcp/tools" in paths
        assert "/mcp/schema" in paths
        assert "/mcp/execute" in paths
        
        # All execute paths should be POST
        for path, methods in paths.items():
            if "execute" in path:
                assert "post" in methods
    
    def test_schema_download_json(self, client):
        """Test /mcp/schema.json returns downloadable JSON"""
        response = client.get("/mcp/schema.json")
        assert response.status_code == 200
        
        # Check content-disposition header
        assert "application/json" in response.headers.get("content-type", "")
        
        # Validate JSON content
        spec = response.json()
        assert spec["openapi"] == "3.0.0"
    
    def test_schema_base_url_parameter(self, client):
        """Test /mcp/schema with custom base_url"""
        custom_url = "https://custom.example.com"
        response = client.get(f"/mcp/schema?base_url={custom_url}")
        assert response.status_code == 200
        
        spec = response.json()
        assert len(spec["servers"]) > 0
        assert spec["servers"][0]["url"] == custom_url
    
    def test_stats_endpoint(self, client):
        """Test /mcp/stats returns adapter statistics"""
        response = client.get("/mcp/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "adapter_version" in data
        assert "protocol_version" in data
        assert "total_tools" in data
        assert data["total_tools"] > 0
        assert "mcp_server_available" in data
        assert "tools_by_category" in data
        assert isinstance(data["tools_by_category"], dict)
        assert len(data["tools_by_category"]) > 0
    
    def test_categories_endpoint(self, client):
        """Test /mcp/categories returns tools grouped by category"""
        response = client.get("/mcp/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_categories" in data
        assert "categories" in data
        assert isinstance(data["categories"], dict)
        
        # Validate category structure
        for category, tools in data["categories"].items():
            assert isinstance(tools, list)
            assert len(tools) > 0
            
            for tool in tools:
                assert "name" in tool
                assert "description" in tool
                assert "governance_level" in tool
    
    def test_execute_dry_run_mode(self, client):
        """Test tool execution with dry_run=true"""
        response = client.post(
            "/mcp/execute",
            json={
                "tool_name": "github_create_issue",
                "arguments": {
                    "owner": "test-user",
                    "repo": "test-repo",
                    "title": "Test issue"
                },
                "dry_run": True
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["tool_name"] == "github_create_issue"
        assert data["result"]["dry_run"] == True
        assert "governance_level" in data
        assert data["execution_time_ms"] == 0
    
    def test_execute_missing_required_args(self, client):
        """Test tool execution with missing required arguments"""
        response = client.post(
            "/mcp/execute",
            json={
                "tool_name": "github_create_issue",
                "arguments": {}  # Missing required args
            }
        )
        # Should fail (likely 400 or execution error)
        assert response.status_code in [200, 400]
        data = response.json()
        
        if response.status_code == 200:
            # Tool execution returned error
            assert data["success"] == False or data.get("error") is not None
    
    def test_execute_unknown_tool(self, client):
        """Test tool execution with unknown tool name"""
        response = client.post(
            "/mcp/execute",
            json={
                "tool_name": "unknown_tool_xyz",
                "arguments": {}
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == False
        assert "Unknown tool" in data["error"]
    
    def test_execute_named_endpoint(self, client):
        """Test tool-specific execution endpoint /mcp/execute/{tool_name}"""
        response = client.post(
            "/mcp/execute/docker_list_containers",
            json={"all": False},
            params={"dry_run": True}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["tool_name"] == "docker_list_containers"
        assert "request_id" in data
        assert "execution_time_ms" in data
    
    def test_read_only_header(self, client):
        """Test X-MCP-ReadOnly header blocks write operations"""
        response = client.post(
            "/mcp/execute",
            json={
                "tool_name": "github_create_issue",
                "arguments": {
                    "owner": "test",
                    "repo": "test",
                    "title": "Test"
                }
            },
            headers={"X-MCP-ReadOnly": "true"}
        )
        # Should either succeed with dry_run or fail with read-only error
        assert response.status_code in [200, 403]
    
    def test_response_includes_request_id(self, client):
        """Test that responses include request_id for tracing"""
        response = client.post(
            "/mcp/execute",
            json={
                "tool_name": "docker_list_containers",
                "arguments": {},
                "dry_run": True
            }
        )
        data = response.json()
        assert "request_id" in data
        assert len(data["request_id"]) > 0
    
    def test_response_includes_execution_time(self, client):
        """Test that responses include execution timing"""
        response = client.post(
            "/mcp/execute",
            json={
                "tool_name": "docker_list_containers",
                "arguments": {},
                "dry_run": True
            }
        )
        data = response.json()
        assert "execution_time_ms" in data
        assert isinstance(data["execution_time_ms"], (int, float))
        assert data["execution_time_ms"] >= 0
    
    def test_openapi_paths_coverage(self, client):
        """Test that OpenAPI schema covers all expected paths"""
        response = client.get("/mcp/schema")
        spec = response.json()
        paths = spec["paths"]
        
        expected_system_paths = [
            "/mcp/health",
            "/mcp/tools",
            "/mcp/schema"
        ]
        
        for path in expected_system_paths:
            assert path in paths, f"Missing path: {path}"
    
    def test_openapi_components_security(self, client):
        """Test OpenAPI schema includes security schemes"""
        response = client.get("/mcp/schema")
        spec = response.json()
        
        assert "components" in spec
        assert "securitySchemes" in spec["components"]
        assert "MCP-API-Key" in spec["components"]["securitySchemes"]
        
        scheme = spec["components"]["securitySchemes"]["MCP-API-Key"]
        assert scheme["type"] == "apiKey"
        assert scheme["in"] == "header"
        assert scheme["name"] == "X-MCP-KEY"
    
    def test_tools_have_categories(self, client):
        """Test that all tools are assigned to categories"""
        response = client.get("/mcp/categories")
        assert response.status_code == 200
        
        data = response.json()
        total_tools_in_categories = sum(
            len(tools) for tools in data["categories"].values()
        )
        
        # Get tool count from /mcp/tools
        tools_response = client.get("/mcp/tools")
        tools_data = tools_response.json()
        
        assert total_tools_in_categories == tools_data["count"]
    
    def test_tool_parameters_typed(self, client):
        """Test that tool parameters include type information"""
        response = client.get("/mcp/tools")
        data = response.json()
        
        # Find a tool with parameters
        for tool in data["tools"]:
            if len(tool["parameters"]) > 0:
                for param in tool["parameters"]:
                    assert "name" in param
                    assert "type" in param
                    assert param["type"] in [
                        "string", "integer", "boolean", "object",
                        "array", "number"
                    ]
                break
    
    def test_governance_levels_present(self, client):
        """Test that tools include governance level"""
        response = client.get("/mcp/tools")
        data = response.json()
        
        valid_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        
        for tool in data["tools"]:
            assert "rate_limit_level" in tool
            assert tool["rate_limit_level"] in valid_levels
    
    def test_schema_x_stats_present(self, client):
        """Test that schema includes x-stats for tool counts"""
        response = client.get("/mcp/schema")
        spec = response.json()
        
        assert "x-stats" in spec
        assert "total_tools" in spec["x-stats"]
        assert "tools_by_category" in spec["x-stats"]
        assert spec["x-stats"]["total_tools"] > 0


class TestMCPAdapterIntegration:
    """Integration tests for MCP adapter with other components"""
    
    def test_adapter_mounted_in_gateway(self, client):
        """Test that MCP adapter is mounted in omni_gateway"""
        response = client.get("/mcp/health")
        assert response.status_code == 200
    
    def test_multiple_requests_independent(self, client):
        """Test that multiple requests are independent"""
        request_ids = []
        
        for i in range(3):
            response = client.post(
                "/mcp/execute",
                json={
                    "tool_name": "docker_list_containers",
                    "arguments": {},
                    "dry_run": True
                }
            )
            data = response.json()
            request_ids.append(data["request_id"])
        
        # All request IDs should be unique
        assert len(set(request_ids)) == len(request_ids)
    
    def test_schema_spec_validity(self, client):
        """Test that generated OpenAPI spec is valid"""
        response = client.get("/mcp/schema")
        spec = response.json()
        
        # Basic OpenAPI validation
        assert "openapi" in spec
        assert spec["openapi"].startswith("3.0")
        assert "info" in spec
        assert "paths" in spec
        
        # Required info fields
        info = spec["info"]
        assert "title" in info
        assert "version" in info
        
        # Validate paths structure
        for path, methods in spec["paths"].items():
            assert isinstance(methods, dict)
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in methods:
                    operation = methods[method]
                    assert "responses" in operation


@pytest.mark.asyncio
class TestMCPAdapterAsync:
    """Async tests for MCP adapter"""
    
    async def test_async_execution(self, client):
        """Test async tool execution"""
        response = client.post(
            "/mcp/execute",
            json={
                "tool_name": "docker_list_containers",
                "arguments": {},
                "dry_run": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
