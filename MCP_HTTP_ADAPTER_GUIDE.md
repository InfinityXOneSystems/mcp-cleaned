# MCP HTTP Adapter - OpenAPI/Custom GPT Integration

## Overview

The MCP HTTP Adapter exposes the existing stdio-based MCP server (`main_extended.py`) via an HTTP/OpenAPI 3.0 interface compatible with:
- OpenAI Custom GPT MCP Auto-Builder
- Any OpenAPI-compliant client
- Cloud Run deployment

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Custom GPT / OpenAPI Client                                 │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Cloud Run / omni_gateway.py (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│ MCP HTTP Adapter (/mcp/*)                                   │
│ - Health check                                              │
│ - Tool discovery (list, schema)                             │
│ - Tool execution with governance                            │
│ - OpenAPI 3.0 generation                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ main_extended.py (MCP Tool Functions)                       │
├─────────────────────────────────────────────────────────────┤
│ - 58+ tools across 18 categories                            │
│ - Governance & rate limiting                                │
│ - Firestore memory integration                              │
└─────────────────────────────────────────────────────────────┘
```

## Endpoints

### System Endpoints

#### GET /mcp/health
Health check. Returns MCP server status and Firestore connectivity.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "protocol_version": "2024-11",
  "mcp_server_available": true,
  "firestore_available": true,
  "timestamp": "2025-12-25T14:30:00Z"
}
```

#### GET /mcp/tools
List all 58+ available tools with descriptions, parameters, and governance levels.

**Response:**
```json
{
  "count": 58,
  "tools": [
    {
      "name": "github_create_issue",
      "description": "Create a GitHub issue",
      "category": "GitHub",
      "parameters": [
        {
          "name": "owner",
          "description": "Repository owner",
          "type": "string",
          "required": true
        },
        ...
      ],
      "rate_limit_level": "MEDIUM",
      "requires_auth": true
    },
    ...
  ]
}
```

#### GET /mcp/schema
Get full OpenAPI 3.0 specification.

**Query Parameters:**
- `base_url` (optional): Base URL for the schema (default: http://localhost:8000)

**Response:** OpenAPI 3.0 JSON object with all tool definitions, parameters, and response schemas.

#### GET /mcp/schema.json
Download OpenAPI schema as JSON file.

#### GET /mcp/schema.yaml
Download OpenAPI schema as YAML file.

#### GET /mcp/stats
Get MCP adapter statistics.

**Response:**
```json
{
  "adapter_version": "1.0.0",
  "protocol_version": "2024-11",
  "total_tools": 58,
  "mcp_server_available": true,
  "tools_by_category": {
    "GitHub": 9,
    "Google Cloud": 15,
    "Docker": 10,
    ...
  },
  "timestamp": "2025-12-25T14:30:00Z"
}
```

#### GET /mcp/categories
List tools grouped by category.

### Tool Execution

#### POST /mcp/execute
Generic tool execution endpoint.

**Request:**
```json
{
  "tool_name": "github_create_issue",
  "arguments": {
    "owner": "user",
    "repo": "myrepo",
    "title": "Bug report",
    "body": "Issue description"
  },
  "dry_run": false,
  "request_id": "optional-request-id"
}
```

**Headers:**
- `X-MCP-KEY`: MCP API key (if enabled)
- `X-MCP-ReadOnly`: Set to `true` for read-only mode (blocks write operations)

**Response:**
```json
{
  "success": true,
  "request_id": "abc123def456",
  "tool_name": "github_create_issue",
  "result": {
    "pr_number": 123,
    "url": "https://github.com/user/myrepo/issues/123"
  },
  "execution_time_ms": 245.3,
  "governance_level": "MEDIUM"
}
```

#### POST /mcp/execute/{tool_name}
Tool-specific execution endpoint.

**Request (application/json):**
Tool arguments as JSON object (parameters vary by tool).

**Example:**
```bash
curl -X POST http://localhost:8000/mcp/execute/github_create_issue \
  -H "Content-Type: application/json" \
  -H "X-MCP-KEY: your-api-key" \
  -d '{
    "owner": "user",
    "repo": "myrepo",
    "title": "New feature",
    "body": "Feature request"
  }'
```

## Configuration

Set via environment variables:

### Security
- `MCP_API_KEY`: API key for authentication (default: "default-key-change-me")
- `MCP_ENABLE_AUTH`: Enable API key authentication (default: "true")
- `MCP_READ_ONLY`: Read-only mode for Custom GPT (default: "false")
- `MCP_REQUIRE_HTTPS`: Require HTTPS in production (default: "false")

### Rate Limiting
- `MCP_RATE_LIMIT_ENABLED`: Enable rate limiting (default: "true")
- `MCP_RATE_LIMIT_CRITICAL`: Critical ops per hour (default: 10)
- `MCP_RATE_LIMIT_HIGH`: High ops per minute (default: 100)
- `MCP_RATE_LIMIT_MEDIUM`: Medium ops per hour (default: 1000)

### Firestore (Memory)
- `FIRESTORE_PROJECT`: GCP project ID (default: "infinity-x-one-systems")
- `FIRESTORE_COLLECTION`: Firestore collection name (default: "mcp_memory")
- `MCP_USE_FIRESTORE`: Use Firestore backend (default: "true")

### Custom GPT
- `MCP_CUSTOM_GPT_MODE`: Enable Custom GPT compatibility (default: "true")

## Dry-Run Mode

Execute tools without actually making changes:

```bash
curl -X POST http://localhost:8000/mcp/execute \
  -H "X-MCP-KEY: your-api-key" \
  -d '{
    "tool_name": "github_create_issue",
    "arguments": {"owner": "user", "repo": "repo", "title": "test"},
    "dry_run": true
  }'
```

**Response (dry_run=true):**
```json
{
  "success": true,
  "result": {
    "dry_run": true,
    "tool": "github_create_issue",
    "category": "GitHub",
    "parameters_provided": ["owner", "repo", "title"],
    "governance_level": "MEDIUM"
  },
  "execution_time_ms": 0,
  "governance_level": "MEDIUM"
}
```

## Governance & Rate Limiting

Tools are governed by execution levels:

- **CRITICAL**: Cloud Run deploy/delete, user suspension (10/hour)
- **HIGH**: Data writes, emails, DNS changes (100/minute)
- **MEDIUM**: Standard API operations (1000/hour)
- **LOW**: Read-only operations (unlimited)

Violations return HTTP 429 (Too Many Requests).

## Read-Only Mode (Custom GPT)

For Custom GPT attachment, enable read-only mode:

```bash
curl -X POST http://localhost:8000/mcp/execute \
  -H "X-MCP-ReadOnly: true" \
  -d '{
    "tool_name": "github_create_issue",
    "arguments": {"owner": "user", "repo": "repo", "title": "test"}
  }'
```

Response:
```json
{
  "success": false,
  "error": "Write operations disabled in read-only mode: github_create_issue",
  "governance_level": "HIGH"
}
```

## Custom GPT Integration

### 1. Generate OpenAPI Schema
```bash
curl http://localhost:8000/mcp/schema?base_url=https://your-cloud-run-url \
  > mcp-openapi.json
```

### 2. Create Custom GPT Action
1. Go to [OpenAI Custom GPT Actions](https://platform.openai.com/gpts)
2. Create new GPT or edit existing
3. Enable "Actions"
4. Upload `mcp-openapi.json` or paste schema
5. Configure authentication:
   - Type: Bearer token
   - Token: Your MCP_API_KEY value
6. Set Read-Only headers for safety

### 3. Test Integration
```bash
# Custom GPT will call endpoints like:
POST https://your-cloud-run-url/mcp/execute/tool_name
Headers:
  Authorization: Bearer your-mcp-api-key
  X-MCP-ReadOnly: true
Body:
  {
    "tool_name": "tool_name",
    "arguments": {...}
  }
```

## OpenAPI Schema Structure

The schema includes:

```yaml
openapi: 3.0.0
info:
  title: Infinity XOS MCP HTTP Adapter
  version: 1.0.0
  x-mcp-protocol: "2024-11"

paths:
  /mcp/execute/{tool_name}:
    post:
      operationId: execute_tool_name
      tags: [Tool Category]
      parameters: [typed parameters from tool schema]
      requestBody: [tool arguments]
      responses: [execution results]

  /mcp/health:
  /mcp/tools:
  /mcp/schema:

components:
  securitySchemes:
    MCP-API-Key:
      type: apiKey
      in: header
      name: X-MCP-KEY
```

Each tool appears as a separate operation with:
- Full parameter validation
- Type information
- Required/optional field declaration
- Default values
- Enums

## Error Handling

Errors return appropriate HTTP status codes:

- **400**: Invalid request (missing required args, unknown tool)
- **401**: Unauthorized (invalid MCP key)
- **429**: Rate limited (governance policy exceeded)
- **500**: Server error (MCP server unavailable)

**Error Response:**
```json
{
  "success": false,
  "request_id": "req_abc123",
  "tool_name": "github_create_issue",
  "error": "Rate limit exceeded: github_create_issue",
  "execution_time_ms": 2.1,
  "governance_level": "MEDIUM"
}
```

## Deployment to Cloud Run

### Build and Push Image
```bash
gcloud builds submit --config cloudbuild.yaml
```

### Deploy with Environment Variables
```bash
gcloud run deploy gateway \
  --image us-east1-docker.pkg.dev/infinity-x-one-systems/mcp-east/gateway:latest \
  --region us-east1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars=\
MCP_API_KEY=your-secure-key,\
MCP_CUSTOM_GPT_MODE=true,\
MCP_READ_ONLY=false,\
FIRESTORE_PROJECT=infinity-x-one-systems,\
GOOGLE_APPLICATION_CREDENTIALS=/var/secrets/service-account.json
```

### Service Account (Workload Identity)
```bash
gcloud iam service-accounts add-iam-policy-binding \
  infinity-x-one-systems@appspot.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member serviceAccount:infinity-x-one-systems.iam.gserviceaccount.com
```

## Monitoring & Logs

View MCP adapter logs:

```bash
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=gateway AND \
  jsonPayload.logger=mcp_http_adapter" \
  --limit 50 --format json
```

Watch real-time execution:

```bash
gcloud logging read --follow \
  "resource.type=cloud_run_revision AND \
   resource.labels.service_name=gateway" \
  --format "value(jsonPayload.message)"
```

## Tool Categories (58+ Tools)

- **Orchestration**: 1
- **GitHub**: 20+
- **Docker**: 10
- **Intelligence**: 2
- **Google Workspace**: 7
- **Google Cloud**: 4
- **Google Maps**: 3
- **Google Analytics**: 3
- **Google Storage**: 4
- **BigQuery**: 3
- **Vertex AI**: 1
- **Workspace Admin**: 4
- **Cloud Pub/Sub**: 2
- **Cloud Firestore**: 3
- **Security**: 3
- **Vision AI**: 3
- **NLP**: 1
- **Speech**: 3
- **Hostinger**: 28+
- **Unified**: 3
- **VS Code**: 8
- **Crawlers**: 8

## Governance Rules

| Operation | Level | Rate Limit | Examples |
|-----------|-------|-----------|----------|
| Read-only queries | LOW | Unlimited | List repos, get file content |
| Standard API calls | MEDIUM | 1000/hour | Create calendar event, search maps |
| Data writes | HIGH | 100/minute | Write spreadsheet, send email |
| Infrastructure | CRITICAL | 10/hour | Deploy to Cloud Run, delete DNS |

## Troubleshooting

### MCP Server Unavailable
If `mcp_server_available: false`, check:
1. `main_extended.py` imports correctly
2. All dependencies installed (`requirements.txt`)
3. Governance module accessible

### Firestore Connection Issues
If `firestore_available: false`:
1. Verify `GOOGLE_APPLICATION_CREDENTIALS` set
2. Check service account permissions on `mcp_memory` collection
3. Ensure GCP project ID matches `FIRESTORE_PROJECT`

### Rate Limiting Too Restrictive
Adjust environment variables (examples for higher throughput):
```bash
MCP_RATE_LIMIT_CRITICAL=20
MCP_RATE_LIMIT_HIGH=500
MCP_RATE_LIMIT_MEDIUM=5000
```

### Tools Not Appearing in Schema
1. Verify tool in `main_extended.py` TOOLS list
2. Check `@server.call_tool()` handler includes tool
3. Run `/mcp/stats` to verify tool count

## References

- [OpenAPI 3.0 Specification](https://spec.openapis.org/oas/v3.0.3)
- [OpenAI Custom GPT Guide](https://platform.openai.com/docs/guides/gpts)
- [MCP Protocol](https://spec.anthropic.com/latest/model-context-protocol)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

---

**Last Updated:** December 25, 2025  
**Status:** Operational  
**Version:** 1.0.0
