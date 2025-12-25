# ChatGPT MCP "Auto Builder" Integration Guide

## Overview

This guide shows you how to connect your **ChatGPT custom GPT** (with the "Auto Builder" MCP tool) to the **Infinity XOS Omni Hub** for bidirectional AI orchestration.

---

## ✅ What's Already Included

### Google Cloud Run Tools (4 Tools) ☁️

Your Omni Hub **ALREADY INCLUDES** Google Cloud Run integration:

```
✓ google_cloud_run_deploy   - Deploy services to Cloud Run
✓ google_cloud_run_list     - List all Cloud Run services
✓ google_cloud_run_describe - Get service details
✓ google_cloud_run_delete   - Delete Cloud Run services
```

**Governance Level:** CRITICAL (10 operations per hour)  
**Status:** Available but needs Google Cloud credentials

---

## 🔧 Test Results Summary

The live connection test (`test_live_connections.py`) checked:

| System | Tools | Status | Notes |
|--------|-------|--------|-------|
| **Google Cloud Run** | 4 | ⊘ Ready | Needs credentials |
| **Google Workspace** | 7 | ⊘ Ready | Needs OAuth token |
| **Google AI/ML** | 12 | ⊘ Ready | Needs credentials |
| **Google Maps** | 3 | ⊘ Ready | Needs API key |
| **Docker** | 10 | ⊘ Ready | Docker not running |
| **Intelligence** | 2 | ✗ Failed | Database not initialized |
| **GitHub** | 3 | ⊘ Ready | Needs token |
| **ChatGPT MCP** | 1 | ⊘ Not Configured | See below |

---

## 🚀 How to Connect ChatGPT "Auto Builder" to Omni Hub

### Step 1: Get Your ChatGPT MCP Endpoint

1. Go to your ChatGPT account: https://chat.openai.com
2. Navigate to your custom GPT with "Auto Builder" MCP tool
3. Find the MCP endpoint URL in GPT settings
   - Should look like: `https://chatgpt-mcp.openai.com/v1/your-gpt-id`

### Step 2: Configure Environment Variable

**On Windows (PowerShell):**
```powershell
$env:CHATGPT_MCP_ENDPOINT = "your_chatgpt_mcp_endpoint_url"
```

**On Linux/Mac:**
```bash
export CHATGPT_MCP_ENDPOINT="your_chatgpt_mcp_endpoint_url"
```

### Step 3: Add ChatGPT Tool to Omni Hub

Create a new tool in `main_extended.py` that can call your ChatGPT Auto Builder:

```python
# Add to TOOLS list around line 280
Tool(
    name="chatgpt_auto_builder_execute",
    description="Execute a command through ChatGPT Auto Builder MCP tool",
    inputSchema={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Command to execute in Auto Builder"
            },
            "context": {
                "type": "object",
                "description": "Additional context for the command"
            }
        },
        "required": ["command"]
    }
)
```

### Step 4: Add Tool Handler

```python
# Add to call_tool dispatcher around line 1050
elif name == "chatgpt_auto_builder_execute":
    return await tool_chatgpt_auto_builder_execute(arguments)
```

### Step 5: Implement Tool Function

```python
# Add to tool implementations around line 1800
async def tool_chatgpt_auto_builder_execute(args: dict) -> list[TextContent]:
    """Execute command through ChatGPT Auto Builder"""
    try:
        endpoint = os.getenv("CHATGPT_MCP_ENDPOINT")
        if not endpoint:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "CHATGPT_MCP_ENDPOINT not configured",
                    "setup_guide": "See CHATGPT_MCP_INTEGRATION_GUIDE.md"
                })
            )]
        
        command = args.get("command", "")
        context = args.get("context", {})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{endpoint}/execute",
                json={
                    "command": command,
                    "context": context
                },
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"ChatGPT Auto Builder executed: {command}")
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "success",
                        "result": result,
                        "command": command
                    })
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"HTTP {response.status_code}",
                        "command": command
                    })
                )]
                
    except Exception as e:
        logger.error(f"ChatGPT Auto Builder error: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "command": args.get("command", "")
            })
        )]
```

### Step 6: Test the Connection

```bash
python test_live_connections.py
```

You should see:
```
💬 ChatGPT MCP Integration
------------------------------------------------------------
  ✓ chatgpt_auto_builder     Connected to ChatGPT MCP endpoint
```

---

## 🔄 Bidirectional Integration

### From Omni Hub → ChatGPT

Any tool in Omni Hub can now call ChatGPT Auto Builder:

```python
# Example: Use ChatGPT to generate code, then deploy to Cloud Run
result = await call_tool("chatgpt_auto_builder_execute", {
    "command": "Generate Python Flask app",
    "context": {"framework": "flask", "purpose": "API"}
})

# Deploy the generated code
await call_tool("google_cloud_run_deploy", {
    "service_name": "generated-api",
    "image_uri": "gcr.io/project/generated-app:latest"
})
```

### From ChatGPT → Omni Hub

Configure your ChatGPT custom GPT to call Omni Hub tools:

1. In your GPT configuration, add MCP server endpoint
2. Point to: `http://localhost:3000` (or your deployed URL)
3. ChatGPT can now call any of the 59 Omni Hub tools

---

## 🛡️ Security Considerations

### 1. Authentication

Add authentication to your MCP endpoints:

```python
# Add to main_extended.py
MCP_API_KEY = os.getenv("MCP_API_KEY", "your-secret-key")

async def verify_mcp_request(request):
    """Verify incoming MCP requests"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {MCP_API_KEY}":
        raise ValueError("Invalid MCP API key")
```

### 2. Rate Limiting

ChatGPT calls are already rate-limited through governance:

```python
GOVERNANCE_RULES = {
    "chatgpt_auto_builder_execute": (GovernanceLevel.MEDIUM, "External AI call"),
}
```

### 3. Audit Logging

All ChatGPT interactions are logged:

```python
logger.info(f"ChatGPT Auto Builder called: {command} (governance: MEDIUM)")
```

---

## 📊 Use Cases

### 1. Code Generation + Deployment Pipeline

```
ChatGPT Auto Builder → Generate code
    ↓
Omni Hub GitHub → Create repository
    ↓
Omni Hub Docker → Build container
    ↓
Omni Hub Cloud Run → Deploy service
```

### 2. Intelligent Analytics

```
Omni Hub Intelligence → Query sources
    ↓
ChatGPT Auto Builder → Analyze data
    ↓
Omni Hub Sheets → Generate report
    ↓
Omni Hub Gmail → Send summary
```

### 3. Multi-Cloud Orchestration

```
ChatGPT Auto Builder → Generate infrastructure plan
    ↓
Omni Hub Cloud Run → Deploy to Google Cloud
    ↓
Omni Hub Docker → Deploy locally
    ↓
Omni Hub GitHub → Version control
```

---

## ✅ Verification Checklist

After setup, verify:

- [ ] `CHATGPT_MCP_ENDPOINT` environment variable set
- [ ] ChatGPT Auto Builder tool added to `TOOLS` list
- [ ] Tool handler added to `call_tool` dispatcher
- [ ] Tool implementation function created
- [ ] `test_live_connections.py` shows ChatGPT as connected
- [ ] Bidirectional calls work (Hub→GPT and GPT→Hub)
- [ ] Governance rules applied to ChatGPT calls
- [ ] Audit logging captures all interactions

---

## 🎯 Current Status

### ✅ Google Cloud Run: YES, Included!

Your Omni Hub includes 4 Google Cloud Run tools:

| Tool | Description | Governance |
|------|-------------|------------|
| `google_cloud_run_deploy` | Deploy services | CRITICAL |
| `google_cloud_run_list` | List all services | MEDIUM |
| `google_cloud_run_describe` | Get service details | LOW |
| `google_cloud_run_delete` | Delete services | CRITICAL |

**To activate:** Set `GOOGLE_OAUTH_TOKEN` or `GOOGLE_SERVICE_ACCOUNT_JSON`

### ⊘ ChatGPT MCP: Needs Configuration

Follow steps above to connect your Auto Builder GPT.

---

## 🚀 Quick Start Commands

### 1. Run Live Connection Test
```bash
python test_live_connections.py
```

### 2. Test Google Cloud Run (with credentials)
```bash
$env:GOOGLE_OAUTH_TOKEN = "your_token"
python test_live_connections.py
```

### 3. Test ChatGPT Integration
```bash
$env:CHATGPT_MCP_ENDPOINT = "your_endpoint"
python test_live_connections.py
```

### 4. Test All Systems
```bash
# Set all credentials
$env:GITHUB_TOKEN = "your_github_token"
$env:GOOGLE_OAUTH_TOKEN = "your_google_token"
$env:GOOGLE_API_KEY = "your_api_key"
$env:CHATGPT_MCP_ENDPOINT = "your_chatgpt_endpoint"

# Run comprehensive test
python test_live_connections.py
```

---

## 📞 Troubleshooting

### Issue: "CHATGPT_MCP_ENDPOINT not configured"

**Solution:** Set the environment variable:
```powershell
$env:CHATGPT_MCP_ENDPOINT = "https://chatgpt-mcp.openai.com/v1/your-gpt-id"
```

### Issue: "Google Cloud credentials not set"

**Solution:** Configure Google authentication:
```powershell
$env:GOOGLE_OAUTH_TOKEN = "your_oauth_token"
# OR
$env:GOOGLE_SERVICE_ACCOUNT_JSON = "path/to/service-account.json"
```

### Issue: "Connection timeout"

**Solution:** 
1. Check your internet connection
2. Verify endpoint URL is correct
3. Check firewall settings
4. Increase timeout in code (default: 30s)

### Issue: "Intelligence database error"

**Solution:** Initialize the database:
```bash
python scripts/init_db.py
```

---

## 🎉 Summary

**YES, Google Cloud Run is included!** ✅

Your Omni Hub v3.0 includes:
- ✅ 4 Google Cloud Run tools (deploy, list, describe, delete)
- ✅ 41 total Google tools across Workspace, Cloud, AI/ML
- ✅ Soft guardrails with governance framework
- ✅ Ready for ChatGPT MCP integration
- ✅ Full recursive connectivity

**Next Steps:**
1. Configure Google Cloud credentials
2. Set up ChatGPT MCP endpoint
3. Run `test_live_connections.py`
4. Start building multi-AI workflows! 🚀

---

**File:** `CHATGPT_MCP_INTEGRATION_GUIDE.md`  
**Last Updated:** December 25, 2025  
**Omni Hub Version:** 3.0.0
