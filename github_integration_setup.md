# GitHub Integration Setup Guide
**Date:** December 25, 2025  
**System:** Infinity XOS Multi-Account GitHub Integration

---

## 🎯 **Integration Overview**

This guide sets up complete GitHub integration with:
1. **Personal GitHub Account** - Your individual repositories
2. **Business GitHub Account (InfinityXOneSystems)** - Organization repositories  
3. **GitHub App Integration** - Native app for advanced workflows

---

## 📋 **Current Status**

### ✅ **What's Already Configured**

1. **Secret Manager Secrets:**
   - `InfinityXOneSystems-github-oauthtoken-c52d6b` - OAuth token for org access

2. **MCP Tools Available:**
   - `github_search_issues` - Search issues across repos
   - `github_get_file_content` - Get file contents from repos
   - `github_create_issue` - Create issues in repos

3. **Sync Infrastructure:**
   - `hydrate.py` - Pulls secrets from Secret Manager
   - `meta_service.py` - GitHub repo syncing endpoints
   - `workers/worker_github.py` - GitHub automation worker

### ⚠️ **What Needs Setup**

1. Personal GitHub token (classic or fine-grained)
2. Business/Organization token (already have OAuth token)
3. GitHub App configuration and private key
4. Service account permissions for Secret Manager

---

## 🔧 **Step 1: Fix Service Account Permissions**

Your service account needs permission to list/access secrets.

### In Google Cloud Console:

1. Go to **IAM & Admin** → **IAM**
2. Find your service account: `workspace-sa@...`
3. Click **Edit** and add role: **Secret Manager Admin** or **Secret Manager Accessor**

### Or via gcloud CLI:
```bash
gcloud projects add-iam-policy-binding 896380409704 \
  --member="serviceAccount:workspace-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"
```

---

## 🔑 **Step 2: Create GitHub Tokens**

### Personal Account Token

1. Go to https://github.com/settings/tokens
2. Click **Generate new token** → **Generate new token (classic)**
3. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Actions workflows)
   - ✅ `read:org` (Read org and team membership)
   - ✅ `user` (Read user profile data)
4. Generate and copy token: `ghp_XXXXXXXXXXXXXXXXXXXX`

### Business/Organization Token

You already have: `InfinityXOneSystems-github-oauthtoken-c52d6b`

If you need a new one:
1. Go to https://github.com/organizations/InfinityXOneSystems/settings/tokens
2. Create fine-grained token with:
   - ✅ All repositories access
   - ✅ Repository permissions: Read and write
   - ✅ Organization permissions: Read

---

## 📱 **Step 3: Create GitHub App**

### Why Use a GitHub App?

- **Better security** - Installation-specific tokens
- **Higher rate limits** - 5,000 requests/hour per installation
- **Granular permissions** - Fine-grained access control
- **Webhook integration** - Real-time event notifications

### Create Your App

1. Go to https://github.com/settings/apps/new
2. **App Name:** `InfinityXOS-Sync` (or your preferred name)
3. **Homepage URL:** Your app/website URL
4. **Webhook URL:** `https://orchestrator-896380409704.us-east1.run.app/webhooks/github`
5. **Webhook Secret:** Generate a random secret (save it!)

### Permissions Needed:

**Repository permissions:**
- ✅ Contents: Read & write
- ✅ Issues: Read & write
- ✅ Pull requests: Read & write
- ✅ Metadata: Read-only
- ✅ Workflows: Read & write

**Organization permissions:**
- ✅ Members: Read-only
- ✅ Projects: Read & write

### After Creation:

1. **Generate a private key** - Download the `.pem` file
2. **Copy the App ID** - You'll need this
3. **Install the app** on:
   - Your personal account
   - InfinityXOneSystems organization

---

## 🔐 **Step 4: Store Credentials in Secret Manager**

### Personal Token
```bash
echo -n "ghp_YOUR_PERSONAL_TOKEN" | gcloud secrets create github-personal-token \
  --project=896380409704 \
  --data-file=- \
  --replication-policy="automatic"
```

### GitHub App Private Key
```bash
gcloud secrets create github-app-private-key \
  --project=896380409704 \
  --data-file=path/to/your-app-name.private-key.pem \
  --replication-policy="automatic"
```

### GitHub App Configuration
```bash
cat > github-app-config.json <<EOF
{
  "app_id": "YOUR_APP_ID",
  "installation_id_personal": "YOUR_PERSONAL_INSTALLATION_ID",
  "installation_id_infinityxone": "YOUR_ORG_INSTALLATION_ID",
  "webhook_secret": "YOUR_WEBHOOK_SECRET"
}
EOF

gcloud secrets create github-app-config \
  --project=896380409704 \
  --data-file=github-app-config.json \
  --replication-policy="automatic"
```

---

## 🔄 **Step 5: Update Local Sync Configuration**

### Create `.env.github` in Credential Manager

```bash
# File: C:\Users\JARVIS\AppData\Local\InfinityXOne\CredentialManager\.env.github

# Personal GitHub Account
GITHUB_PERSONAL_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXX
GITHUB_PERSONAL_USERNAME=YourUsername

# Business Account (InfinityXOneSystems)
GITHUB_BUSINESS_TOKEN=from_secret_manager
GITHUB_BUSINESS_ORG=InfinityXOneSystems

# GitHub App
GITHUB_APP_ID=123456
GITHUB_APP_INSTALLATION_ID_PERSONAL=78901234
GITHUB_APP_INSTALLATION_ID_BUSINESS=78901235
GITHUB_APP_PRIVATE_KEY_PATH=./github-app-private-key.pem
GITHUB_APP_WEBHOOK_SECRET=your_webhook_secret

# Project Configuration
GOOGLE_CLOUD_PROJECT=896380409704
```

---

## 🔄 **Step 6: Update Hydration Script**

Add to `hydrate.py` to pull GitHub credentials:

```python
def load_github_credentials():
    """Load all GitHub credentials from Secret Manager"""
    secrets_to_load = {
        'personal_token': 'projects/896380409704/secrets/github-personal-token',
        'business_token': 'projects/896380409704/secrets/InfinityXOneSystems-github-oauthtoken-c52d6b',
        'app_private_key': 'projects/896380409704/secrets/github-app-private-key',
        'app_config': 'projects/896380409704/secrets/github-app-config'
    }
    
    credentials = {}
    for key, secret_name in secrets_to_load.items():
        url = f"{MCP_AGENT_BASE}/gcp/get_secret"
        body = {'secret_name': secret_name}
        res = call(url, method='POST', json_body=body)
        if res and '__error' not in res:
            credentials[key] = res.get('data')
    
    return credentials

def save_github_env():
    """Save GitHub credentials to local .env.github"""
    creds = load_github_credentials()
    
    env_path = os.path.expanduser(
        'C:/Users/JARVIS/AppData/Local/InfinityXOne/CredentialManager/.env.github'
    )
    
    with open(env_path, 'w') as f:
        f.write(f"GITHUB_PERSONAL_TOKEN={creds.get('personal_token', '')}\n")
        f.write(f"GITHUB_BUSINESS_TOKEN={creds.get('business_token', '')}\n")
        
        # Parse app config
        app_config = json.loads(creds.get('app_config', '{}'))
        f.write(f"GITHUB_APP_ID={app_config.get('app_id', '')}\n")
        f.write(f"GITHUB_APP_INSTALLATION_ID_PERSONAL={app_config.get('installation_id_personal', '')}\n")
        f.write(f"GITHUB_APP_INSTALLATION_ID_BUSINESS={app_config.get('installation_id_infinityxone', '')}\n")
        f.write(f"GITHUB_APP_WEBHOOK_SECRET={app_config.get('webhook_secret', '')}\n")
    
    # Save private key separately
    key_path = os.path.join(os.path.dirname(env_path), 'github-app-private-key.pem')
    with open(key_path, 'w') as f:
        f.write(creds.get('app_private_key', ''))
    
    print(f"✅ GitHub credentials saved to {env_path}")
```

---

## 🔄 **Step 7: Sync to Git Repositories**

### Update `.env.example` in foundation repo:

```bash
# GitHub Integration
GITHUB_PERSONAL_TOKEN=your_personal_token_here
GITHUB_BUSINESS_TOKEN=from_secret_manager
GITHUB_APP_ID=your_app_id
GITHUB_APP_INSTALLATION_ID=your_installation_id
```

### Add to `.gitignore`:
```
# GitHub credentials
.env.github
github-app-private-key.pem
*.pem
```

---

## 🚀 **Step 8: Test the Integration**

### Test Personal Account Access:
```powershell
$env:GITHUB_TOKEN = (Get-Content "C:\Users\JARVIS\AppData\Local\InfinityXOne\CredentialManager\.env.github" | Select-String "GITHUB_PERSONAL_TOKEN" | ForEach-Object { $_.ToString().Split('=')[1] })

curl -H "Authorization: Bearer $env:GITHUB_TOKEN" https://api.github.com/user
```

### Test Business Account Access:
```powershell
$env:GITHUB_TOKEN = (Get-Content "C:\Users\JARVIS\AppData\Local\InfinityXOne\CredentialManager\.env.github" | Select-String "GITHUB_BUSINESS_TOKEN" | ForEach-Object { $_.ToString().Split('=')[1] })

curl -H "Authorization: Bearer $env:GITHUB_TOKEN" https://api.github.com/orgs/InfinityXOneSystems/repos
```

### Test GitHub App:
```powershell
python scripts/test_github_app.py
```

---

## 📊 **Step 9: Configure Tri-Directional Sync**

Your updated sync architecture:

```
Google Secret Manager (Cloud)
  ├─ github-personal-token
  ├─ InfinityXOneSystems-github-oauthtoken
  ├─ github-app-private-key
  └─ github-app-config
        ↓ hydrate.py
Local Credential Manager
  ├─ .env.github
  └─ github-app-private-key.pem
        ↓ git-sync-service.ts
Git Repositories
  ├─ mcp/.env.example (templates)
  └─ foundation/.env.example (templates)
```

---

## ✅ **Benefits of This Setup**

1. **Multi-Account Support:**
   - Personal repos for individual projects
   - Business repos for organization work
   - Seamless switching between accounts

2. **GitHub App Advantages:**
   - Higher API rate limits
   - Installation-specific access
   - Webhook notifications for automation
   - Better security with short-lived tokens

3. **Credential Security:**
   - All secrets in Google Secret Manager
   - Local copies synced automatically
   - Git repos only have examples, no real credentials
   - Service account authentication

4. **Automation Ready:**
   - MCP tools can use any account
   - Workers can automate tasks
   - Webhooks trigger real-time actions
   - Cross-repo synchronization

---

## 🔒 **Security Best Practices**

1. **Never commit real credentials to git**
2. **Use fine-grained tokens with minimum permissions**
3. **Rotate tokens every 90 days**
4. **Use GitHub App for production workflows**
5. **Monitor Secret Manager access logs**
6. **Enable 2FA on all GitHub accounts**

---

## 🆘 **Troubleshooting**

### Permission Denied on Secret Manager:
```bash
gcloud projects add-iam-policy-binding 896380409704 \
  --member="serviceAccount:YOUR-SA@896380409704.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"
```

### GitHub API Rate Limit:
- Switch to GitHub App (5000/hour vs 60/hour)
- Use authenticated requests
- Cache responses when possible

### Token Invalid:
- Check token hasn't expired
- Verify scopes include required permissions
- Regenerate if necessary

---

## 📝 **Next Steps**

1. ✅ Fix service account permissions
2. ✅ Create personal GitHub token
3. ✅ Create GitHub App
4. ✅ Store all credentials in Secret Manager
5. ✅ Update hydrate.py with GitHub functions
6. ✅ Test both personal and business account access
7. ✅ Configure webhooks for automation

**Questions?** Check the MCP documentation or meta_service.py endpoints!
