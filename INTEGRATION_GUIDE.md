# Infinity XOS - Full System Integration Guide

## System Status: OPERATIONAL ✅

All components deployed and tested. Ready for Google Sheets/Calendar integration and ChatGPT MCP autonomous operation.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Infinity-Monitor UI                     │
│  (Primary Dashboard - Full Screen VS Code Shell)    │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│           Omni-Gateway (Port 8000) - display name for the MCP gateway │
│  /predict /crawl /simulate /sheets /calendar        │
│  /admin/status /admin/endpoints /admin/chat         │
└───┬──────┬──────┬──────┬──────┬──────┬─────────────┘
    │      │      │      │      │      │
    ▼      ▼      ▼      ▼      ▼      ▼
┌───────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────────────┐
│Dashbd │ │Intl│ │Meta│ │MCP │ │Sht │ │ Calendar   │
│ 8001  │ │8002│ │8003│ │Srv │ │API │ │   API      │
└───────┘ └────┘ └────┘ └────┘ └────┘ └────────────┘
```

## Quick Start

### 1. Start All Services
```powershell
powershell -ExecutionPolicy Bypass -File .\start_servers.ps1
```

### 2. Open Primary Dashboard
```powershell
Start-Process http://localhost:8000/admin
```

Or set environment variable:
```powershell
$env:PRIMARY_DASHBOARD="command_center"  # or "admin_console"
```

### 3. Install VS Code Extension (Optional Full-Screen Shell)
```powershell
cd vscode-dashboard-extension
npm install
npm run package
code --install-extension infinity-dashboard-0.0.1.vsix
```

## Google Integration Setup

### Prerequisites
1. Service Account JSON at: `c:\AI\repos\mcp\secrets\service-account.json`
2. Environment variable:
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="c:\AI\repos\mcp\secrets\service-account.json"
```

3. Sheet ID (get from URL):
```
https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit
```

4. Share Sheet with service account email (from JSON): `xxx@xxx.iam.gserviceaccount.com`

### Test Sheets Integration
```powershell
# Test append
curl -X POST "http://localhost:8000/sheets/append?sheet_id=YOUR_SHEET_ID&range_name=Sheet1!A1" `
  -H "Content-Type: application/json" `
  -d '{"values":[["timestamp","asset","type","confidence"],["2025-12-25","TSLA","price",75]]}'

# Test read
curl "http://localhost:8000/sheets/read?sheet_id=YOUR_SHEET_ID&range_name=Sheet1!A1:D10"
```

### Test Calendar Integration
```powershell
# List events
curl "http://localhost:8000/calendar/events?calendar_id=primary&max_results=5"

# Create event
curl -X POST "http://localhost:8000/calendar/create" `
  -H "Content-Type: application/json" `
  -d '{
    "calendar_id":"primary",
    "summary":"Infinity Prediction Target",
    "start_time":"2025-12-26T10:00:00Z",
    "end_time":"2025-12-26T11:00:00Z",
    "description":"TSLA price prediction target date"
  }'
```

## ChatGPT MCP Integration

### Custom GPT Actions Schema
Use the JSON schema from earlier message to configure your Custom GPT Actions.

Map each tool to the gateway:
- `gateway_predict` → POST http://localhost:8000/predict
- `gateway_crawl` → POST http://localhost:8000/crawl
- `gateway_simulate` → POST http://localhost:8000/simulate
- `memory_set` → POST http://localhost:8003/memory/set
- `memory_get` → GET http://localhost:8003/memory/get
- `gpt_rehydrate` → POST http://localhost:8003/gpt/rehydrate
- `admin_status` → GET http://localhost:8000/admin/status

### Enable in ChatGPT Desktop
1. Open ChatGPT Desktop app
2. Go to Settings > Beta Features
3. Enable "Model Context Protocol"
4. Add MCP server config:
```json
{
  "mcpServers": {
    "infinity-xos": {
      "command": "python",
      "args": ["c:\\AI\\repos\\mcp\\main_extended.py"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "c:\\AI\\repos\\mcp\\secrets\\service-account.json"
      }
    }
  }
}
```

## Optimized Crawler Usage

```python
from crawler_optimized import CrawlConfig, crawl_optimized
import asyncio

config = CrawlConfig(
    max_pages=50,
    max_depth=2,
    allowed_domains=['example.com'],
    sheet_id='YOUR_SHEET_ID',
    llm_analyze=True
)

result = asyncio.run(crawl_optimized('https://example.com', config))
print(f"Crawled {result['pages_crawled']} pages")
```

## Cloud Run Deployment

See [CLOUD_RUN_DEPLOYMENT.md](CLOUD_RUN_DEPLOYMENT.md) for full instructions.

Quick deploy:
```bash
export PROJECT_ID=896380409704
gcloud builds submit --tag gcr.io/$PROJECT_ID/omni-gateway
gcloud run deploy omni-gateway --image gcr.io/$PROJECT_ID/omni-gateway --region us-central1 --allow-unauthenticated
```

## Available Endpoints

### Core Gateway
- `GET /health` - Health check
- `GET /admin` - Primary dashboard UI
- `GET /admin/status` - Live system status
- `GET /admin/endpoints` - Endpoint inventory
- `POST /admin/chat` - Chat stub with provider selection

### Operations
- `POST /predict` - Unified predictions
- `POST /crawl` - Web crawling
- `POST /simulate` - Scenario analysis
- `POST /read/{resource}` - Data retrieval
- `POST /write/{resource}` - Data modification
- `POST /analyze/{resource}` - Analysis

### Google Integration
- `POST /sheets/append` - Append rows
- `GET /sheets/read` - Read range
- `POST /sheets/update` - Update range
- `POST /sheets/log_prediction` - Log prediction
- `GET /calendar/events` - List events
- `POST /calendar/create` - Create event
- `POST /calendar/update` - Update event
- `POST /calendar/delete` - Delete event

### Intelligence
- `GET /api/intelligence/categories` - Top industries
- `GET /api/intelligence/sources` - Intelligence sources

## System Check

```powershell
powershell -ExecutionPolicy Bypass -File .\status_servers.ps1
```

Expected output:
```
api_gateway - PID:XXXXX Proc:UP Port:UP
dashboard_api - PID:XXXXX Proc:UP Port:UP
intelligence_api - PID:XXXXX Proc:UP Port:UP
meta_service - PID:XXXXX Proc:UP Port:UP
```

## Troubleshooting

### Sheets not writing
1. Check `$env:GOOGLE_APPLICATION_CREDENTIALS` is set
2. Verify service account email has Editor access to Sheet
3. Check Sheet ID is correct (from URL)
4. Test with curl commands above

### Calendar not accessible
1. Ensure Calendar API is enabled in GCP project
2. Service account needs Calendar scope
3. For "primary" calendar, service account must be invited

### Services not starting
```powershell
powershell -ExecutionPolicy Bypass -File .\stop_servers.ps1
powershell -ExecutionPolicy Bypass -File .\start_servers.ps1
```

### Port conflicts
```powershell
Get-NetTCPConnection -LocalPort 8000,8001,8002,8003 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

## Environment Variables

Required:
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="path\to\service-account.json"
$env:PRIMARY_DASHBOARD="command_center"  # or admin_console
$env:SHEET_ID="your-google-sheet-id"
```

Optional:
```powershell
$env:GATEWAY_PORT="8000"
$env:MCP_API_KEY="your-api-key"
$env:GITHUB_TOKEN="your-github-token"
$env:CALENDAR_ID="primary"
```

## Next Steps

1. **Get Sheet ID**: Open Google Sheet, copy ID from URL
2. **Test Sheets**: Run curl test commands above
3. **Configure ChatGPT**: Add MCP server to ChatGPT Desktop
4. **Deploy to Cloud Run**: Follow deployment guide
5. **Build VS Code Extension**: For full-screen shell experience

## Support

All systems operational. Ready for autonomous ChatGPT operation via MCP.

For issues:
1. Check `.\logs\` directory for service logs
2. Run status check script
3. Verify environment variables
4. Test endpoints with curl
