# Monitoring & Alerting Configuration

This directory contains automated monitoring and alerting for the Infinity XOS system.

## What's Being Monitored

### 1. **GitHub Actions Workflow** (`.github/workflows/monitor-everything.yml`)
Runs automatically on:
- **Hourly** - Full system health check
- **Weekly** (Monday 9 AM) - Detailed status report
- **On every push** - Deployment validation
- **Manual trigger** - Anytime via GitHub Actions UI

**Checks performed:**
- ✓ Cloud Run service status
- ✓ API endpoint health (health, dashboard, OpenAPI)
- ✓ Build history and status
- ✓ Database connectivity
- ✓ Repository state (commits, changes)

**Notifications:**
- GitHub Issues created on failures (tagged: `alert`, `monitoring`)
- Email notifications (configure in GitHub Secrets)
- Slack alerts (configure `SLACK_WEBHOOK_URL` in Secrets)

### 2. **Local Monitoring Script** (`monitor_system.py`)
Comprehensive Python health checker that can run anywhere:

```bash
# Run locally
python monitor_system.py

# In CI/CD
python -m monitor_system > health_report.json

# Output: JSON + formatted report
```

**Checks:**
- Cloud Run service details
- API response codes and latency
- Database tables and connectivity
- Git commit history
- Recent build status
- Alert aggregation

## Setup Instructions

### GitHub Actions Secrets
Add these to your repository secrets: https://github.com/InfinityXOneSystems/mcp/settings/secrets/actions

```
GCP_SA_KEY          # JSON service account key (for Cloud Run checks)
GCP_PROJECT_ID      # infinity-x-one-systems
GCP_REGION          # us-central1
SLACK_WEBHOOK_URL   # (optional) for Slack notifications
```

### Environment Variables (Local)
Create `.env.local`:
```
GATEWAY_URL=http://localhost:8000
GCP_PROJECT_ID=infinity-x-one-systems
GCP_REGION=us-central1
```

## Alert Severity Levels

- **HEALTHY** - No issues
- **DEGRADED** - 1-2 issues (e.g., one endpoint slow)
- **CRITICAL** - 3+ issues (e.g., Cloud Run down, API failing)

## Viewing Results

1. **GitHub Actions Dashboard**: https://github.com/InfinityXOneSystems/mcp/actions
2. **Created Issues**: https://github.com/InfinityXOneSystems/mcp/issues?labels=alert
3. **Email**: Notifications sent to your GitHub email
4. **Slack**: If webhook configured, real-time alerts
5. **Local**: Run `python monitor_system.py` anytime

## Customization

Edit `.github/workflows/monitor-everything.yml` to:
- Change schedule (cron format)
- Add/remove checks
- Modify alert thresholds
- Add custom notifications (PagerDuty, OpsGenie, etc.)

Edit `monitor_system.py` to:
- Add new health checks
- Change timeout values
- Add database-specific checks
- Integrate with external services

## Troubleshooting

**"Cloud Run service check failed"**
- Ensure GCP service account key is in GitHub Secrets
- Verify service account has `roles/run.viewer` permission

**"Cannot connect to dashboard endpoint"**
- Check if gateway is running: `curl http://localhost:8000/health`
- Verify GATEWAY_URL is correct in environment

**"Build check error"**
- Ensure gcloud CLI is installed on runner
- Check GCP credentials and permissions

---

**Deployed:** 2025-12-25
**Last Check:** Check GitHub Actions > Workflows > Monitor Everything
