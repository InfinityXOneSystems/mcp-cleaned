# Google Integration Setup Guide - Infinity XOS Omni-Directional Hub v3.0

## Overview

This guide provides complete setup instructions for integrating Google Workspace, Google Cloud, and Google AI/ML APIs into the Omni-Directional Hub. The system includes 41 Google-related tools organized across 13 categories with soft guardrails, rate limiting, and comprehensive error handling.

## System Architecture

### Google Tool Categories (41 tools)

1. **Google Workspace (7 tools)** - Calendar, Sheets, Drive, Gmail, Docs
2. **Google Cloud Run (4 tools)** - Service deployment and management
3. **Google Maps (3 tools)** - Search, directions, geocoding
4. **Google Search & Analytics (3 tools)** - Custom search, GA4 queries
5. **Google Cloud Storage (4 tools)** - Object storage operations
6. **Google BigQuery (3 tools)** - Data warehousing and queries
7. **Google Vertex AI (1 tool)** - ML predictions
8. **Google Workspace Admin (4 tools)** - User management
9. **Google Cloud Pub/Sub (2 tools)** - Messaging
10. **Google Cloud Firestore (3 tools)** - NoSQL database
11. **Google Security & Translation (3 tools)** - reCAPTCHA, Translation
12. **Google Vision AI (3 tools)** - OCR, label detection, text detection
13. **Google NLP (1 tool)** - Sentiment, entities, syntax
14. **Google Speech & Media (3 tools)** - Speech-to-text, TTS, video analysis

### Governance Framework

All Google tools implement soft guardrails with governance levels:

- **CRITICAL** (10 per hour): Cloud Run deploy/delete
- **HIGH** (100 per minute): Data writes, emails, user creation
- **MEDIUM** (Standard): Calendar events, API calls, predictions
- **LOW** (Minimal): Reads, searches, queries

## Prerequisites

### System Requirements
- Python 3.8+
- pip (package manager)
- Google Cloud account with billing enabled
- Access to Google Cloud Console
- Administrator access for Google Workspace domain (for admin tools)

### Required Python Packages

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Step 1: Create Google Cloud Project

1. **Visit Google Cloud Console:**
   ```
   https://console.cloud.google.com
   ```

2. **Create new project:**
   - Click "Select a Project" → "NEW PROJECT"
   - Project name: "infinity-xos-omni-hub"
   - Click "CREATE"

3. **Enable required APIs:**
   
   In Cloud Console, search for and enable these APIs:
   
   ```
   - Google Calendar API
   - Google Sheets API
   - Google Drive API
   - Gmail API
   - Google Docs API
   - Cloud Run API
   - Cloud Storage API
   - BigQuery API
   - Vertex AI API
   - Cloud Pub/Sub API
   - Cloud Firestore API
   - Cloud Maps API
   - Google Custom Search API
   - Google Analytics Admin API
   - Vision AI API
   - Natural Language API
   - Speech-to-Text API
   - Text-to-Speech API
   - Cloud Translation API
   ```

## Step 2: Create Service Account

For production use with Cloud APIs:

1. **Go to Service Accounts:**
   ```
   IAM & Admin → Service Accounts → Create Service Account
   ```

2. **Fill details:**
   - Service account name: `infinity-xos-omni`
   - Service account ID: `infinity-xos-omni@[PROJECT_ID].iam.gserviceaccount.com`
   - Click "CREATE AND CONTINUE"

3. **Grant roles:**
   - Basic Editor role (for testing)
   - For production, grant specific roles per service
   - Click "CONTINUE"

4. **Create key:**
   - Click "Manage Keys" → "Add Key" → "Create new key"
   - Key type: JSON
   - Click "CREATE"
   - Save the JSON file securely

## Step 3: Create OAuth 2.0 Credentials

For Google Workspace and user-facing APIs:

1. **Go to OAuth consent screen:**
   ```
   APIs & Services → OAuth consent screen
   ```

2. **Create consent screen:**
   - User type: Internal (or External if needed)
   - App name: "Infinity XOS Omni Hub"
   - Support email: [your-email]
   - Click "SAVE AND CONTINUE"

3. **Add scopes:**
   ```
   /auth/calendar
   /auth/spreadsheets
   /auth/drive
   /auth/gmail
   /auth/documents
   /auth/admin.directory.user
   /auth/analytics
   /auth/analytics.readonly
   ```
   Click "SAVE AND CONTINUE"

4. **Create OAuth 2.0 Client ID:**
   ```
   APIs & Services → Credentials → Create Credentials → OAuth client ID
   ```
   
   - Application type: "Desktop application"
   - Name: "Infinity XOS CLI"
   - Click "CREATE"

5. **Download credentials:**
   - Click the download icon
   - Save as `oauth_credentials.json`

## Step 4: Set Environment Variables

### Option A: Using .env file (Development)

Create `.env` in the project directory:

```bash
# Google Cloud Service Account (for Cloud APIs)
export GOOGLE_SERVICE_ACCOUNT_JSON="/path/to/service-account-key.json"

# Google OAuth2 (for Workspace APIs)
export GOOGLE_OAUTH_TOKEN="your_oauth_access_token_here"

# Google API Key (for Maps, Custom Search)
export GOOGLE_API_KEY="AIzaSyDx..."

# Other MCP credentials
export GITHUB_TOKEN="ghp_..."
export ORCHESTRATOR_URL="https://orchestrator.example.com"
```

### Option B: Using System Environment

**On Windows (PowerShell):**
```powershell
$env:GOOGLE_SERVICE_ACCOUNT_JSON="C:\path\to\service-account-key.json"
$env:GOOGLE_OAUTH_TOKEN="your_oauth_access_token"
$env:GOOGLE_API_KEY="AIzaSyDx..."
```

**On Linux/macOS:**
```bash
export GOOGLE_SERVICE_ACCOUNT_JSON="/path/to/service-account-key.json"
export GOOGLE_OAUTH_TOKEN="your_oauth_access_token"
export GOOGLE_API_KEY="AIzaSyDx..."
```

## Step 5: Obtain OAuth 2.0 Access Token

1. **Run OAuth flow:**
   ```python
   from google.auth.transport.requests import Request
   from google.oauth2.service_account import Credentials
   
   # For service account (automatic)
   credentials = Credentials.from_service_account_file(
       'service-account-key.json',
       scopes=[
           'https://www.googleapis.com/auth/calendar',
           'https://www.googleapis.com/auth/spreadsheets',
           'https://www.googleapis.com/auth/drive',
           'https://www.googleapis.com/auth/gmail.send',
           'https://www.googleapis.com/auth/documents',
       ]
   )
   
   # Get access token
   request = Request()
   credentials.refresh(request)
   access_token = credentials.token
   ```

2. **Set as environment variable:**
   ```bash
   export GOOGLE_OAUTH_TOKEN="$access_token"
   ```

## Step 6: Configure Google Maps & Custom Search

### Google Maps API

1. **Create API Key:**
   ```
   APIs & Services → Credentials → Create Credentials → API Key
   ```

2. **Restrict key:**
   - Restrict to only Maps APIs
   - Add HTTP referrer (if applicable)

3. **Set environment variable:**
   ```bash
   export GOOGLE_MAPS_API_KEY="your_api_key"
   ```

### Google Custom Search Engine

1. **Create custom search engine:**
   ```
   https://cse.google.com/cse
   ```

2. **Obtain search engine ID:**
   - Copy the Search Engine ID (cx)

3. **Get API key (see above)**

4. **Set environment variables:**
   ```bash
   export GOOGLE_CUSTOM_SEARCH_ID="cx=..."
   export GOOGLE_CUSTOM_SEARCH_API_KEY="your_api_key"
   ```

## Step 7: Configure Google Workspace Admin Access

For user management tools:

1. **Enable Domain-Wide Delegation:**
   ```
   Service Accounts → Select your service account
   → Security → Domain-wide delegation → Manage Domain Wide Delegation
   ```

2. **Add scopes:**
   ```
   https://www.googleapis.com/auth/admin.directory.user
   https://www.googleapis.com/auth/admin.directory.orgunit
   https://www.googleapis.com/auth/admin.directory.group
   ```

3. **Set authorized OAuth scopes in Google Workspace:**
   ```
   Admin console → Security → Access and data control → API controls → Manage Domain Wide Delegation
   ```

4. **Authorize client ID:**
   - Use your service account client ID
   - Add the above scopes

## Step 8: Test Google Integration

### Run the Omni Hub test:

```bash
cd c:\AI\repos\mcp
python test_omni_hub.py
```

Expected output shows all 59 tools loaded with governance levels.

### Test individual Google tools:

```python
# Test Google Calendar
curl -X POST http://localhost:3000/tools/google_calendar_list_events \
  -H "Authorization: Bearer $GOOGLE_OAUTH_TOKEN" \
  -d '{
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  }'

# Test Google Sheets read
curl -X POST http://localhost:3000/tools/google_sheets_read \
  -H "Authorization: Bearer $GOOGLE_OAUTH_TOKEN" \
  -d '{
    "spreadsheet_id": "YOUR_SHEET_ID",
    "range": "Sheet1!A1:Z100"
  }'

# Test Cloud Run list
curl -X POST http://localhost:3000/tools/google_cloud_run_list \
  -H "Authorization: Bearer $GOOGLE_OAUTH_TOKEN" \
  -d '{
    "region": "us-central1"
  }'
```

## Step 9: Implement Production Credentials Management

For production deployments:

### Secure Credential Storage

```python
# Use Secret Manager (Google Cloud)
from google.cloud import secretmanager

def get_secret(project_id, secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Usage
service_account_json = get_secret("my-project", "google-service-account")
oauth_token = get_secret("my-project", "google-oauth-token")
```

### Token Refresh Strategy

```python
class GoogleCredentialManager:
    @staticmethod
    def get_fresh_token():
        """Get fresh OAuth token with automatic refresh"""
        # Check token expiration
        if not token or token_expired:
            # Refresh using service account credentials
            credentials = get_service_account_credentials()
            request = Request()
            credentials.refresh(request)
            return credentials.token
        return existing_token
```

## Step 10: Enable Audit Logging

Configure audit logging for governance compliance:

```bash
# Enable Cloud Audit Logs
gcloud logging write omni-hub-audit \
  "Google API call: $(date)" \
  --severity=INFO
```

## Troubleshooting

### Common Issues

1. **"GOOGLE_OAUTH_TOKEN not set"**
   - Verify environment variable is exported
   - Restart Python shell after setting env vars
   - Use `echo $GOOGLE_OAUTH_TOKEN` to verify

2. **"Credentials not found"**
   - Verify JSON path is absolute
   - Check file permissions (`chmod 600` on Unix)
   - Confirm project ID matches

3. **"Quota exceeded"**
   - Check governance rate limits in code
   - Review API quotas in Cloud Console
   - Implement backoff strategy

4. **"Permission denied"**
   - Verify service account has necessary roles
   - Check Domain-Wide Delegation is enabled
   - Confirm OAuth scopes are authorized

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('google.auth')
logger.setLevel(logging.DEBUG)
```

## Security Best Practices

1. **Protect credentials files:**
   ```bash
   chmod 600 service-account-key.json
   chmod 600 oauth_credentials.json
   ```

2. **Use Secret Manager:**
   - Store secrets in Google Cloud Secret Manager
   - Rotate tokens regularly (monthly)
   - Audit access logs

3. **Implement rate limiting:**
   - Soft guardrails are enforced in code
   - Monitor API usage in Cloud Console
   - Set alerts for quota usage

4. **Enable Cloud Audit Logs:**
   ```
   Logging → Audit Logs → Admin Activity, Data Access
   ```

## Monitoring & Observability

### Log Monitoring

```bash
gcloud logging read "resource.type=api" \
  --limit=50 \
  --format=json
```

### Metrics Dashboard

Create custom dashboard in Cloud Console:
1. Monitoring → Dashboards → Create Dashboard
2. Add charts for:
   - API call rate
   - Error rate
   - Latency
   - Quota usage

## Production Deployment Checklist

- [ ] Service account created and authorized
- [ ] OAuth 2.0 credentials configured
- [ ] API keys restricted and secured
- [ ] Domain-Wide Delegation enabled
- [ ] Environment variables configured
- [ ] Credentials secured in Secret Manager
- [ ] Audit logging enabled
- [ ] Monitoring dashboard created
- [ ] Rate limiting tested
- [ ] Error handling verified
- [ ] Documentation updated
- [ ] Team trained on guardrails

## Next Steps

1. **Implement additional Google APIs:**
   - Google Cloud Functions
   - Google Cloud Tasks
   - Google Cloud Scheduler
   - Google Cloud Bigtable

2. **Enhance governance:**
   - Multi-level approval workflows
   - Cost allocation tracking
   - Team quotas and limits

3. **Integrate with external systems:**
   - Slack notifications
   - PagerDuty alerts
   - Data lake synchronization

## Support & Resources

- **Google Cloud Documentation:** https://cloud.google.com/docs
- **Google API Documentation:** https://developers.google.com/
- **Omni Hub GitHub:** [Repository URL]
- **Issue Tracker:** [Issue URL]

---

**Last Updated:** December 25, 2025
**Version:** 3.0.0
**Status:** Production Ready
