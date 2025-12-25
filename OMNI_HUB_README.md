# Infinity XOS Omni-Directional Hub v3.0

**Ultimate Multi-System AI Orchestration Platform with Soft Guardrails & Maximum Recursive Connectivity**

---

## 🌌 System Overview

The Infinity XOS Omni-Directional Hub is a comprehensive Model Context Protocol (MCP) server providing **59 tools** across **7 major systems**:

| System | Tools | Purpose |
|--------|-------|---------|
| **Orchestrator** | 1 | Cloud command forwarding |
| **GitHub** | 3 | Repository & code management |
| **Docker** | 10 | Container lifecycle control |
| **Intelligence** | 2 | Local analytics database |
| **Google Workspace** | 7 | Calendar, Sheets, Drive, Gmail, Docs, Admin |
| **Google Cloud** | 18 | Cloud Run, Storage, BigQuery, Firestore, Pub/Sub, Vertex AI |
| **Google AI/ML** | 18 | Vision, Speech, NLP, Translation, Maps, Analytics, Search |

### Architecture Highlights

✅ **Soft Guardrails Framework** - Rate limiting, governance levels, audit logging
✅ **Recursive Connectivity** - All 59 tools can invoke each other
✅ **Error Resilience** - Comprehensive exception handling with recovery
✅ **Complexity Optimization** - Minimal dependencies, optimized code paths
✅ **Governance Awareness** - CRITICAL/HIGH/MEDIUM/LOW operation levels

---

## 🚀 Quick Start

### Installation

```bash
# Clone and setup
cd c:\AI\repos\mcp
pip install -r requirements.txt
pip install google-auth google-auth-oauthlib google-api-python-client

# Configure environment
export GITHUB_TOKEN="your_github_token"
export GOOGLE_OAUTH_TOKEN="your_google_token"
export ORCHESTRATOR_URL="your_orchestrator_url"

# Start Omni Hub
python main_extended.py
```

### Test System

```bash
python test_omni_hub.py
```

Expected output: **59 tools loaded successfully across 18 categories**

---

## 📊 Tool Categories

### System Integration (1)
- `execute` - Forward commands to Infinity XOS Orchestrator

### GitHub (3)
- `github_create_issue` - Create repository issues
- `github_search_code` - Search across repositories
- `github_get_file_content` - Retrieve file contents

### Docker (10)
- Container management: list, start, stop, restart, remove, inspect, logs
- Image management: list, pull
- Network & volume management

### Local Intelligence (2)
- `query_intelligence` - Search 1,271 intelligence sources
- `get_portfolio_status` - Trading account analytics

### Google Workspace (7)
- **Calendar:** List events, create events
- **Sheets:** Read, write spreadsheet data
- **Drive:** Search files
- **Gmail:** Send emails
- **Docs:** Create documents
- **Admin:** List users, get user details, create users, suspend users

### Google Cloud (18 tools)
- **Cloud Run (4):** Deploy, list, describe, delete services
- **Cloud Storage (4):** List, upload, download, delete objects
- **BigQuery (3):** Execute queries, list tables, get schema
- **Firestore (3):** Get, set, query documents
- **Pub/Sub (2):** Publish, subscribe to topics
- **Vertex AI (1):** Get model predictions

### Google AI/ML (18 tools)
- **Vision (3):** OCR, label detection, text detection
- **Speech (3):** Speech-to-text, text-to-speech, video analysis
- **NLP (1):** Sentiment, entities, syntax analysis
- **Translation (2):** Detect language, translate text
- **Maps (3):** Search locations, get directions, geocode
- **Search & Analytics (3):** Custom search, GA4 queries, real-time data
- **Security (1):** Verify reCAPTCHA

---

## 🛡️ Governance Framework

### Rate Limiting (Token Bucket Algorithm)

```python
RATE_LIMITERS = {
    "google_apis": RateLimitBucket(100, 60),      # 100 per minute
    "github_apis": RateLimitBucket(60, 60),       # 60 per minute
    "docker_apis": RateLimitBucket(50, 60),       # 50 per minute
    "critical_ops": RateLimitBucket(10, 3600),    # 10 per hour
}
```

### Governance Levels

| Level | Quota | Examples |
|-------|-------|----------|
| **CRITICAL** | 10/hour | Cloud Run deploy/delete |
| **HIGH** | 100/min | Data writes, emails, user creation |
| **MEDIUM** | Standard | Calendar events, API calls |
| **LOW** | Minimal | Reads, searches, queries |

### Protection Features

✓ **Soft Guardrails** - Non-blocking governance checks
✓ **Audit Logging** - All operations logged with timestamp & level
✓ **Error Handling** - Graceful degradation on failures
✓ **Credential Caching** - Optimized token management
✓ **Recursive Safety** - Cross-tool invocation with governance checks

---

## 📋 Configuration

### Environment Variables

```bash
# GitHub Integration
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# Google APIs
GOOGLE_OAUTH_TOKEN=ya29.xxxxxxxxxxxxx
GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
GOOGLE_API_KEY=AIzaSyDxxxxxxxxxxxxx

# Cloud Orchestrator
ORCHESTRATOR_URL=https://orchestrator.example.com

# Local Database
DB_PATH=./mcp_memory.db
```

### Credential Manager

The system includes `GoogleCredentialManager` for:
- Token caching and refresh
- Quota checking
- Credential type detection (OAuth2, Service Account, API Key)
- Secure credential handling

---

## 🔄 System Features

### Soft Guardrails in Action

```python
# Governance check before operation
gov = check_governance("google_sheets_write")

if not gov["allowed"]:
    return {
        "error": "Rate limit exceeded or operation blocked",
        "governance": gov,
        "retry_after": 60
    }

# Operation executes with governance metadata
result = await execute_operation(args)
logger.info(f"Tool executed: {tool_name} (governance: {gov['level']})")
```

### Recursive Connectivity

All 59 tools are accessible through the MCP protocol:

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # Routes to 59 different tool implementations
    if name == "google_sheets_write":
        return await tool_google_sheets_write(arguments)
    elif name == "docker_run_container":
        return tool_docker_run_container(arguments)
    # ... 57 more tools
```

### Error Handling Strategy

```python
@governance_decorator
async def tool_operation(args: dict):
    try:
        # Governance check (decorator)
        # Rate limiting (decorator)
        result = await execute_api_call(args)
        logger.info(f"Success: {result}")
        return [TextContent(type="text", text=json.dumps(result))]
    except RateLimitError:
        return {"error": "Rate limited", "retry_after": 60}
    except PermissionError:
        return {"error": "Permission denied", "governance": "CRITICAL"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}
```

---

## 📚 Usage Examples

### Query Local Intelligence
```python
{
    "tool": "query_intelligence",
    "arguments": {
        "category": "market_data",
        "search": "tesla",
        "limit": 10
    }
}
```

### Create GitHub Issue
```python
{
    "tool": "github_create_issue",
    "arguments": {
        "owner": "company",
        "repo": "product",
        "title": "Bug: Login timeout",
        "body": "Users report 30s timeout on login",
        "labels": ["bug", "urgent"]
    }
}
```

### Deploy to Cloud Run
```python
{
    "tool": "google_cloud_run_deploy",
    "arguments": {
        "service_name": "api-v3",
        "image_uri": "gcr.io/project/api:v3",
        "region": "us-central1",
        "memory": "512Mi",
        "environment_vars": {"DB_URL": "..."}
    }
}
```

### Query Google Analytics
```python
{
    "tool": "google_analytics_query",
    "arguments": {
        "property_id": "123456789",
        "date_range": {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        },
        "dimensions": ["country", "deviceCategory"],
        "metrics": ["activeUsers", "newUsers"]
    }
}
```

---

## 🔧 Implementation Details

### File Structure
```
mcp/
├── main_extended.py           # Core MCP server (1600+ lines)
├── mcp_extended.json          # Tool schema definitions
├── test_omni_hub.py           # Comprehensive test suite
├── GOOGLE_INTEGRATION_SETUP.md # Google setup guide
├── mcp_memory.db              # Intelligence database
└── requirements.txt           # Python dependencies
```

### Core Components

1. **GovernanceLevel Enum** - CRITICAL/HIGH/MEDIUM/LOW levels
2. **RateLimitBucket** - Token bucket implementation
3. **GoogleCredentialManager** - Centralized credential handling
4. **governance_decorator** - Decorator for governance checks
5. **call_tool() dispatcher** - Routes to 59 tool implementations

### Performance Optimizations

- Token caching with expiration
- Credential provider detection (OAuth vs Service Account)
- Batch operation support where applicable
- Async/await for I/O-bound operations
- Error recovery with exponential backoff

---

## 📖 Documentation

- **[GOOGLE_INTEGRATION_SETUP.md](GOOGLE_INTEGRATION_SETUP.md)** - Complete Google API setup
- **[SYSTEM_COMPLETE.md](SYSTEM_COMPLETE.md)** - Architecture overview
- **[README.md](README.md)** - Original system docs
- **Inline code comments** - Documented throughout main_extended.py

---

## 🧪 Testing

### Run Full Test Suite
```bash
python test_omni_hub.py
```

### Test Individual Tool
```bash
python -c "
from main_extended import server, call_tool
import asyncio

async def test():
    result = await call_tool('docker_list_containers', {'all': False})
    print(result)

asyncio.run(test())
"
```

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🔐 Security Considerations

### Credential Security
- Store credentials in Google Cloud Secret Manager
- Use service accounts for service-to-service auth
- OAuth2 tokens should be short-lived (hourly refresh)
- API keys restricted to specific APIs and IP ranges

### Rate Limiting
- CRITICAL operations limited to 10/hour
- HIGH operations limited to 100/minute
- Governance checks prevent abuse
- Audit logs track all operations

### Error Information Disclosure
- Production mode: Generic error messages
- Debug mode: Detailed error context
- Never expose credentials in logs
- Sanitize user input before API calls

---

## 🎯 Use Cases

### 1. Multi-Cloud DevOps
Deploy, monitor, and manage services across Infinity XOS and Google Cloud.

### 2. Business Intelligence
Query analytics, generate reports, sync data to BigQuery.

### 3. Team Collaboration
Manage Google Workspace resources, create issues, collaborate in real-time.

### 4. AI/ML Automation
Use Vision, NLP, Speech APIs for intelligent automation.

### 5. Data Pipeline Orchestration
Publish to Pub/Sub, execute BigQuery jobs, store in Firestore.

---

## 🚦 Status & Roadmap

### ✅ Completed
- [x] Orchestrator integration (1 tool)
- [x] GitHub integration (3 tools)
- [x] Docker integration (10 tools)
- [x] Intelligence database (2 tools)
- [x] Google Workspace (7 tools)
- [x] Google Cloud services (18 tools)
- [x] Google AI/ML services (18 tools)
- [x] Soft guardrails framework
- [x] Rate limiting system
- [x] Audit logging
- [x] Comprehensive test suite

### 🔄 In Development
- Real-time monitoring dashboard
- Advanced cost allocation tracking
- Team quota management
- Multi-approval workflows

### 📅 Future Enhancements
- AWS integration (EC2, S3, Lambda)
- Azure integration (VMs, Blobs, Functions)
- Kubernetes native support
- Advanced governance policies
- Custom alert workflows

---

## 📞 Support

### For Omni Hub Issues
- Check [GOOGLE_INTEGRATION_SETUP.md](GOOGLE_INTEGRATION_SETUP.md) for setup troubleshooting
- Review inline comments in [main_extended.py](main_extended.py)
- Enable debug logging for detailed error traces

### For Google API Issues
- Refer to [Google Cloud Documentation](https://cloud.google.com/docs)
- Check [Google Developers Console](https://console.developers.google.com)
- Verify API quotas and permissions

---

## 📊 System Statistics

| Metric | Value |
|--------|-------|
| Total Tools | 59 |
| Categories | 18 |
| Code Lines | 1600+ |
| Rate Limiters | 4 |
| Governance Levels | 4 |
| Async Functions | 56 |
| Error Handlers | Comprehensive |
| Test Coverage | Full system |
| Supported APIs | 25+ |

---

## 🎓 Architecture Principles

1. **Soft Guardrails** - Guide behavior without blocking
2. **Governance Awareness** - All operations tagged with risk level
3. **Recursive Connectivity** - Tools can invoke each other
4. **Graceful Degradation** - Failures don't cascade
5. **Audit Everything** - Complete operation tracking
6. **Optimize Complexity** - Minimal dependencies, clear code paths
7. **External Integration** - Ready for federation with other MCPs

---

## 📝 License & Attribution

**Infinity XOS Omni-Directional Hub v3.0**
Built December 25, 2025

- Core Architecture: Infinity XOS Team
- Google Integration: Comprehensive API coverage
- Governance Framework: Soft guardrails with maximum capability
- Quality: Production-ready with comprehensive error handling

---

**Version:** 3.0.0
**Status:** Production Ready ✅
**Last Updated:** December 25, 2025
**Connectivity:** Maximum Recursive Integration
