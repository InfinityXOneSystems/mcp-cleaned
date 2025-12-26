# MCP HTTP Adapter Testing Guide

This document explains how to test and validate the MCP HTTP Adapter implementation.

## Quick Start

### 1. Verify Implementation
```bash
python verify_mcp_adapter.py .
```

Expected output: `✓ VERIFICATION SUCCESSFUL - Adapter ready for testing`

### 2. Run Unit Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run test suite
pytest test_mcp_http_adapter.py -v

# Run specific test class
pytest test_mcp_http_adapter.py::TestMCPAdapter -v

# Run with coverage
pytest test_mcp_http_adapter.py --cov=mcp_http_adapter
```

### 3. Test Running Service
```bash
# Start the gateway service
python omni_gateway.py

# In another terminal, test endpoints
curl http://localhost:8000/mcp/health
curl http://localhost:8000/mcp/tools
curl http://localhost:8000/mcp/schema
```

## Testing Breakdown

### Unit Tests (test_mcp_http_adapter.py)

#### TestMCPAdapter Class
- **test_health_endpoint**: Validates /mcp/health response structure
- **test_tools_list_endpoint**: Tests tool discovery endpoint
- **test_schema_endpoint**: Validates OpenAPI 3.0 schema generation
- **test_schema_download_json**: Tests schema download as JSON
- **test_schema_base_url_parameter**: Tests custom base URL configuration
- **test_stats_endpoint**: Validates adapter statistics
- **test_categories_endpoint**: Tests tool categorization
- **test_execute_dry_run_mode**: Tests dry-run without execution
- **test_execute_missing_required_args**: Tests error handling
- **test_execute_unknown_tool**: Tests unknown tool handling
- **test_execute_named_endpoint**: Tests tool-specific endpoints
- **test_read_only_header**: Tests read-only mode enforcement
- **test_response_includes_request_id**: Validates request tracing
- **test_response_includes_execution_time**: Tests timing information
- **test_openapi_paths_coverage**: Ensures all expected paths present
- **test_openapi_components_security**: Validates security schemes
- **test_tools_have_categories**: Ensures tool categorization
- **test_tool_parameters_typed**: Validates parameter type information
- **test_governance_levels_present**: Tests governance level presence
- **test_schema_x_stats_present**: Tests custom X-stats fields

#### TestMCPAdapterIntegration Class
- **test_adapter_mounted_in_gateway**: Verifies adapter integration
- **test_multiple_requests_independent**: Tests request isolation
- **test_schema_spec_validity**: Validates OpenAPI spec structure

#### TestMCPAdapterAsync Class
- **test_async_execution**: Tests async tool execution

## Manual Testing Examples

### Test Health Endpoint
```bash
curl -X GET http://localhost:8000/mcp/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "protocol_version": "2024-11",
  "mcp_server_available": true,
  "firestore_available": false,
  "timestamp": "2025-12-25T23:53:04.123456Z"
}
```

### Test Tool Discovery
```bash
curl -X GET http://localhost:8000/mcp/tools | jq '.tools | length'
```

### Test OpenAPI Schema
```bash
curl -X GET http://localhost:8000/mcp/schema | jq '.info'
```

### Test Tool Execution (Dry Run)
```bash
curl -X POST http://localhost:8000/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "docker_list_containers",
    "arguments": {},
    "dry_run": true
  }'
```

### Test Named Endpoint
```bash
curl -X POST http://localhost:8000/mcp/execute/docker_list_containers \
  -H "Content-Type: application/json" \
  -d '{"all": false}' \
  -G --data-urlencode 'dry_run=true'
```

### Test Authentication Header
```bash
curl -X POST http://localhost:8000/mcp/execute \
  -H "Content-Type: application/json" \
  -H "X-MCP-KEY: your-api-key" \
  -d '{
    "tool_name": "docker_list_containers",
    "arguments": {}
  }'
```

### Test Read-Only Mode
```bash
curl -X POST http://localhost:8000/mcp/execute \
  -H "Content-Type: application/json" \
  -H "X-MCP-ReadOnly: true" \
  -d '{
    "tool_name": "github_create_issue",
    "arguments": {
      "owner": "test",
      "repo": "test",
      "title": "Test Issue"
    }
  }'
```

## Validation Checklist

- [ ] Verification script passes with 0 failures
- [ ] All unit tests pass
- [ ] Service starts without errors
- [ ] /mcp/health returns 200 OK
- [ ] /mcp/tools returns list of tools
- [ ] /mcp/schema returns valid OpenAPI 3.0 spec
- [ ] Tool execution with dry_run works
- [ ] Tool execution with named endpoint works
- [ ] Authentication header is validated
- [ ] Read-only mode blocks write operations
- [ ] All 23 tool categories present
- [ ] All 58 tools accessible via HTTP
- [ ] Request tracing (request_id) works
- [ ] Execution timing is recorded
- [ ] Error responses are properly formatted

## Custom GPT Integration Testing

### 1. Download OpenAPI Schema
```bash
curl http://localhost:8000/mcp/schema > mcp-openapi.json
```

### 2. Validate Schema
```bash
# Use OpenAPI validator
npm install -g openapi-cli
openapi validate mcp-openapi.json
```

### 3. Import into Custom GPT
1. Open Custom GPT builder
2. Go to "Actions" tab
3. Click "Create new action"
4. Upload `mcp-openapi.json`
5. Configure authentication (X-MCP-KEY header)
6. Test tool invocation in GPT

### 4. Test Tool Invocation
Ask the Custom GPT:
- "List my Docker containers"
- "What MCP tools are available?"
- "Show me the adapter statistics"
- "Create a GitHub issue (in dry-run mode)"

## Troubleshooting

### Service Fails to Start
```bash
# Check Python version
python --version  # Should be 3.9+

# Check required dependencies
pip install fastapi pydantic starlette uvicorn

# Check for port conflicts
netstat -an | grep 8000
```

### OpenAPI Schema Invalid
```bash
# Re-download and validate
curl http://localhost:8000/mcp/schema.json | jq . > schema-validated.json

# Check for schema errors
python -c "import json; json.load(open('schema-validated.json'))"
```

### Tools Not Listed
```bash
# Check tool registry population
curl http://localhost:8000/mcp/tools | jq '.count'

# Should return a number > 0
```

### Authentication Fails
```bash
# Check API key configuration
echo $MCP_API_KEY

# Try with environment variable
export MCP_API_KEY="test-key"
curl -H "X-MCP-KEY: test-key" http://localhost:8000/mcp/health
```

### Read-Only Mode Not Working
```bash
# Test with write operation
curl -X POST http://localhost:8000/mcp/execute \
  -H "X-MCP-ReadOnly: true" \
  -d '{"tool_name": "github_create_issue", "arguments": {...}}'

# Should return 403 or error
```

## Performance Testing

### Load Testing
```bash
# Install wrk (load testing tool)
# brew install wrk (macOS)
# or download from https://github.com/wg/wrk

wrk -t12 -c400 -d30s http://localhost:8000/mcp/health
```

### Concurrent Requests
```bash
# Test with multiple concurrent requests
for i in {1..100}; do
  curl http://localhost:8000/mcp/tools &
done
wait
```

### Rate Limiting Test
```bash
# Send requests above rate limit
for i in {1..200}; do
  curl -X POST http://localhost:8000/mcp/execute \
    -d '{"tool_name": "docker_list_containers", "arguments": {}}' &
done
```

## Environment Variables for Testing

```bash
# Set API key
export MCP_API_KEY="test-key-123"

# Enable authentication
export MCP_ENABLE_AUTH="true"

# Enable read-only mode
export MCP_READ_ONLY="false"

# Set Firestore project
export GOOGLE_CLOUD_PROJECT="infinity-x-one-systems"

# Enable Custom GPT mode
export CUSTOM_GPT_MODE="true"
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Test MCP Adapter

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt pytest pytest-asyncio
      - run: python verify_mcp_adapter.py .
      - run: pytest test_mcp_http_adapter.py -v
```

## Success Criteria

✓ Adapter successfully wraps stdio MCP server with HTTP interface
✓ OpenAPI 3.0 schema is generated and valid
✓ All 58 tools are accessible via HTTP endpoints
✓ Authentication and authorization work correctly
✓ Read-only mode prevents write operations
✓ Dry-run mode works without side effects
✓ Error handling returns appropriate HTTP status codes
✓ Custom GPT integration is successful
✓ Performance meets requirements (< 1s response time)
✓ Cloud Run deployment is ready

## Next Steps

1. Start omni_gateway.py service
2. Run verification script
3. Execute unit test suite
4. Perform manual endpoint testing
5. Import schema into Custom GPT
6. Test tool invocation via Custom GPT
7. Deploy to Cloud Run for production testing

See [MCP_HTTP_ADAPTER_GUIDE.md](MCP_HTTP_ADAPTER_GUIDE.md) for detailed deployment instructions.
