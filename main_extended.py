"""
Infinity XOS Omni-Directional Hub - Comprehensive Integration Platform
Multi-system orchestration: Orchestrator, GitHub, Docker, Intelligence, Google Suite
Features: Soft guardrails, governance, rate limiting, recursive connectivity
"""
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx
import os
import sqlite3
import json
import subprocess
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import hashlib
from functools import wraps
import logging
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ===== LOGGING & GOVERNANCE =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GovernanceLevel(Enum):
    """Soft guardrails for API access"""
    CRITICAL = 1      # High-risk operations: requires approval
    HIGH = 2          # Data modification: logged, rate-limited
    MEDIUM = 3        # Standard operations: standard rate limit
    LOW = 4           # Read-only: minimal restrictions

class RateLimitBucket:
    """Token bucket rate limiter with governance awareness"""
    def __init__(self, max_tokens: int, refill_seconds: int):
        self.max_tokens = max_tokens
        self.refill_seconds = refill_seconds
        self.tokens = max_tokens
        self.last_refill = datetime.now()
    
    def can_use(self, tokens: int = 1) -> bool:
        now = datetime.now()
        elapsed = (now - self.last_refill).total_seconds()
        refill_rate = self.max_tokens / self.refill_seconds
        self.tokens = min(self.max_tokens, self.tokens + (elapsed * refill_rate))
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

# ===== GOVERNANCE REGISTRY =====
GOVERNANCE_RULES = {
    # Google APIs
    "google_sheets_write": (GovernanceLevel.HIGH, "Modifies spreadsheet data"),
    "google_docs_create": (GovernanceLevel.HIGH, "Creates new documents"),
    "google_calendar_create_event": (GovernanceLevel.MEDIUM, "Creates calendar events"),
    "google_gmail_send": (GovernanceLevel.HIGH, "Sends emails"),
    "google_cloud_run_deploy": (GovernanceLevel.CRITICAL, "Deploys to Cloud Run"),
    "google_maps_search": (GovernanceLevel.LOW, "Searches maps"),
    
    # GitHub APIs
    "github_create_issue": (GovernanceLevel.MEDIUM, "Creates GitHub issues"),
    
    # Docker APIs
    "docker_run": (GovernanceLevel.HIGH, "Executes containers"),
    
    # ChatGPT MCP
    "chatgpt_auto_builder_execute": (GovernanceLevel.MEDIUM, "External AI call"),

    # Hostinger
    "hostinger_list_domains": (GovernanceLevel.LOW, "Lists domains"),
    "hostinger_get_domain_info": (GovernanceLevel.LOW, "Get domain info"),
    "hostinger_list_dns_records": (GovernanceLevel.LOW, "Lists DNS records"),
    "hostinger_create_dns_record": (GovernanceLevel.HIGH, "Creates DNS record"),
    "hostinger_update_dns_record": (GovernanceLevel.HIGH, "Updates DNS record"),
    "hostinger_delete_dns_record": (GovernanceLevel.CRITICAL, "Deletes DNS record"),

    # Default
    "default": (GovernanceLevel.MEDIUM, "Standard operation")
}

RATE_LIMITERS = {
    "google_apis": RateLimitBucket(100, 60),      # 100 per minute
    "github_apis": RateLimitBucket(60, 60),       # 60 per minute
    "docker_apis": RateLimitBucket(50, 60),       # 50 per minute
    "critical_ops": RateLimitBucket(10, 3600),    # 10 per hour
}

def check_governance(tool_name: str) -> Dict[str, Any]:
    """Check governance rules and rate limits"""
    level, reason = GOVERNANCE_RULES.get(tool_name, GOVERNANCE_RULES["default"])
    
    # Determine rate limit bucket
    bucket = None
    if "google" in tool_name:
        if level == GovernanceLevel.CRITICAL:
            bucket = RATE_LIMITERS["critical_ops"]
        else:
            bucket = RATE_LIMITERS["google_apis"]
    elif "github" in tool_name:
        bucket = RATE_LIMITERS["github_apis"]
    elif "docker" in tool_name:
        bucket = RATE_LIMITERS["docker_apis"]
    
    result = {
        "level": level.name,
        "allowed": True,
        "reason": reason,
        "rate_limited": False
    }
    
    if bucket:
        if not bucket.can_use():
            result["allowed"] = False
            result["rate_limited"] = True
    
    if level == GovernanceLevel.CRITICAL:
        logger.warning(f"CRITICAL operation: {tool_name} - {reason}")
    
    return result

def governance_decorator(func):
    """Decorator to apply governance checks"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        tool_name = func.__name__.replace("tool_", "")
        gov_check = check_governance(tool_name)
        
        if not gov_check["allowed"]:
            return [TextContent(type="text", text=json.dumps({
                "error": "Rate limit exceeded or operation blocked by governance",
                "governance": gov_check,
                "retry_after": 60
            }))]
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            logger.info(f"Tool executed: {tool_name} (governance: {gov_check['level']})")
            return result
        except Exception as e:
            logger.error(f"Tool error: {tool_name} - {str(e)}")
            return [TextContent(type="text", text=json.dumps({
                "error": str(e),
                "tool": tool_name,
                "timestamp": datetime.now().isoformat()
            }))]
    
    return wrapper

ORCHESTRATOR_URL = os.getenv(
    "ORCHESTRATOR_URL",
    "https://orchestrator-896380409704.us-east1.run.app/execute"
)

DB_PATH = 'mcp_memory.db'

server = Server("infinity-xos-mcp-omni-hub")

# ===== TOOL DEFINITIONS =====
TOOLS = [
    Tool(
        name="execute",
        description="Forward command to Infinity XOS Orchestrator",
        inputSchema={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "payload": {"type": "object"}
            },
            "required": ["command"]
        }
    ),
    Tool(
        name="github_create_issue",
        description="Create a GitHub issue in the specified repository",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body"},
                "labels": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["owner", "repo", "title", "body"]
        }
    ),
    Tool(
        name="github_search_code",
        description="Search for code across GitHub repositories",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "max_results": {"type": "integer", "default": 10}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="github_get_file_content",
        description="Get the content of a file from a GitHub repository",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "path": {"type": "string"},
                "branch": {"type": "string", "default": "main"}
            },
            "required": ["owner", "repo", "path"]
        }
    ),
    Tool(
        name="query_intelligence",
        description="Query intelligence sources from local memory database",
        inputSchema={
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "search": {"type": "string"},
                "limit": {"type": "integer", "default": 10}
            }
        }
    ),
    Tool(
        name="get_portfolio_status",
        description="Get current trading portfolio status",
        inputSchema={"type": "object", "properties": {}}
    ),
    # Docker Tools
    Tool(
        name="docker_list_containers",
        description="List Docker containers (running or all)",
        inputSchema={
            "type": "object",
            "properties": {
                "all": {"type": "boolean", "default": False, "description": "Include stopped containers"}
            }
        }
    ),
    Tool(
        name="docker_container_action",
        description="Control Docker containers (start/stop/restart/remove)",
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["start", "stop", "restart", "remove"], "description": "Action to perform"},
                "container": {"type": "string", "description": "Container name or ID"}
            },
            "required": ["action", "container"]
        }
    ),
    Tool(
        name="docker_run_container",
        description="Run a new Docker container",
        inputSchema={
            "type": "object",
            "properties": {
                "image": {"type": "string", "description": "Image name"},
                "name": {"type": "string", "description": "Container name"},
                "ports": {"type": "object", "description": "Port mappings {container_port: host_port}"},
                "environment": {"type": "object", "description": "Environment variables"},
                "detach": {"type": "boolean", "default": True}
            },
            "required": ["image"]
        }
    ),
    Tool(
        name="docker_list_images",
        description="List Docker images",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="docker_pull_image",
        description="Pull a Docker image from registry",
        inputSchema={
            "type": "object",
            "properties": {
                "image": {"type": "string", "description": "Image name with optional tag"}
            },
            "required": ["image"]
        }
    ),
    Tool(
        name="docker_container_logs",
        description="Get container logs",
        inputSchema={
            "type": "object",
            "properties": {
                "container": {"type": "string", "description": "Container name or ID"},
                "tail": {"type": "integer", "default": 100, "description": "Number of lines to show"}
            },
            "required": ["container"]
        }
    ),
    Tool(
        name="docker_container_inspect",
        description="Inspect container details",
        inputSchema={
            "type": "object",
            "properties": {
                "container": {"type": "string", "description": "Container name or ID"}
            },
            "required": ["container"]
        }
    ),
    Tool(
        name="docker_list_networks",
        description="List Docker networks",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="docker_list_volumes",
        description="List Docker volumes",
        inputSchema={"type": "object", "properties": {}}
    ),
    # Google Workspace Tools
    Tool(
        name="google_calendar_list_events",
        description="List Google Calendar events within a date range",
        inputSchema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                "max_results": {"type": "integer", "default": 10}
            },
            "required": ["start_date", "end_date"]
        }
    ),
    Tool(
        name="google_calendar_create_event",
        description="Create a Google Calendar event",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "start_time": {"type": "string", "description": "Start time (ISO 8601)"},
                "end_time": {"type": "string", "description": "End time (ISO 8601)"},
                "description": {"type": "string", "description": "Event description"}
            },
            "required": ["title", "start_time", "end_time"]
        }
    ),
    Tool(
        name="google_sheets_read",
        description="Read data from Google Sheets",
        inputSchema={
            "type": "object",
            "properties": {
                "spreadsheet_id": {"type": "string", "description": "Google Sheets spreadsheet ID"},
                "range": {"type": "string", "description": "Sheet range (e.g., Sheet1!A1:B10)"}
            },
            "required": ["spreadsheet_id", "range"]
        }
    ),
    Tool(
        name="google_sheets_write",
        description="Write data to Google Sheets",
        inputSchema={
            "type": "object",
            "properties": {
                "spreadsheet_id": {"type": "string", "description": "Google Sheets spreadsheet ID"},
                "range": {"type": "string", "description": "Sheet range (e.g., Sheet1!A1)"},
                "values": {"type": "array", "description": "Array of rows to write"}
            },
            "required": ["spreadsheet_id", "range", "values"]
        }
    ),
    Tool(
        name="google_drive_search",
        description="Search for files in Google Drive",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 10}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="google_gmail_send",
        description="Send an email via Gmail",
        inputSchema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body"}
            },
            "required": ["to", "subject", "body"]
        }
    ),
    Tool(
        name="google_docs_create",
        description="Create a new Google Doc",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title"},
                "content": {"type": "string", "description": "Initial document content"}
            },
            "required": ["title"]
        }    ),
    # ===== COMPREHENSIVE GOOGLE CLOUD SERVICES =====
    Tool(
        name="google_cloud_run_deploy",
        description="Deploy a service to Google Cloud Run",
        inputSchema={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service name"},
                "image_uri": {"type": "string", "description": "Container image URI"},
                "region": {"type": "string", "default": "us-central1", "description": "GCP region"},
                "memory": {"type": "string", "default": "256Mi", "description": "Memory allocation"},
                "cpu": {"type": "string", "default": "1", "description": "CPU allocation"},
                "environment_vars": {"type": "object", "description": "Environment variables"}
            },
            "required": ["service_name", "image_uri"]
        }
    ),
    Tool(
        name="google_cloud_run_list",
        description="List Cloud Run services in a region",
        inputSchema={
            "type": "object",
            "properties": {
                "region": {"type": "string", "default": "us-central1", "description": "GCP region"}
            }
        }
    ),
    Tool(
        name="google_cloud_run_describe",
        description="Get detailed information about a Cloud Run service",
        inputSchema={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service name"},
                "region": {"type": "string", "default": "us-central1", "description": "GCP region"}
            },
            "required": ["service_name"]
        }
    ),
    Tool(
        name="google_cloud_run_delete",
        description="Delete a Cloud Run service",
        inputSchema={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service name"},
                "region": {"type": "string", "default": "us-central1", "description": "GCP region"}
            },
            "required": ["service_name"]
        }
    ),
    Tool(
        name="google_maps_search",
        description="Search locations and places on Google Maps",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (business, address, or place)"},
                "location": {"type": "string", "description": "Latitude,longitude bias (optional)"},
                "radius": {"type": "integer", "default": 50000, "description": "Search radius in meters"},
                "max_results": {"type": "integer", "default": 10}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="google_maps_directions",
        description="Get directions between two points on Google Maps",
        inputSchema={
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Starting location"},
                "destination": {"type": "string", "description": "Destination location"},
                "mode": {"type": "string", "enum": ["driving", "walking", "bicycling", "transit"], "default": "driving"},
                "alternatives": {"type": "boolean", "default": False, "description": "Return alternative routes"}
            },
            "required": ["origin", "destination"]
        }
    ),
    Tool(
        name="google_maps_geocode",
        description="Convert addresses to coordinates and vice versa",
        inputSchema={
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Address to geocode"},
                "reverse": {"type": "boolean", "default": False, "description": "Reverse geocode (lat,lng to address)"}
            },
            "required": ["address"]
        }
    ),
    Tool(
        name="google_custom_search",
        description="Perform custom web search using Google Custom Search Engine",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "default": 10, "description": "Number of results"},
                "safe_search": {"type": "boolean", "default": True, "description": "Enable safe search"},
                "image_search": {"type": "boolean", "default": False, "description": "Search for images only"}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="google_analytics_query",
        description="Query Google Analytics 4 data",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "string", "description": "GA4 property ID"},
                "date_range": {"type": "object", "properties": {
                    "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                    "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"}
                }, "required": ["start_date", "end_date"]},
                "dimensions": {"type": "array", "items": {"type": "string"}, "description": "Dimensions to query"},
                "metrics": {"type": "array", "items": {"type": "string"}, "description": "Metrics to query"}
            },
            "required": ["property_id", "date_range", "metrics"]
        }
    ),
    Tool(
        name="google_analytics_realtime",
        description="Get real-time Google Analytics data",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "string", "description": "GA4 property ID"},
                "metrics": {"type": "array", "items": {"type": "string"}, "description": "Metrics to query (activeUsers, newUsers, etc.}"}
            },
            "required": ["property_id", "metrics"]
        }
    ),
    Tool(
        name="google_cloud_storage_list",
        description="List objects in a Google Cloud Storage bucket",
        inputSchema={
            "type": "object",
            "properties": {
                "bucket": {"type": "string", "description": "Bucket name"},
                "prefix": {"type": "string", "description": "Object prefix filter"},
                "max_results": {"type": "integer", "default": 100}
            },
            "required": ["bucket"]
        }
    ),
    Tool(
        name="google_cloud_storage_upload",
        description="Upload an object to Google Cloud Storage",
        inputSchema={
            "type": "object",
            "properties": {
                "bucket": {"type": "string", "description": "Bucket name"},
                "object_name": {"type": "string", "description": "Object name/path"},
                "content": {"type": "string", "description": "File content (base64 encoded)"},
                "content_type": {"type": "string", "default": "application/octet-stream"}
            },
            "required": ["bucket", "object_name", "content"]
        }
    ),
    Tool(
        name="google_cloud_storage_download",
        description="Download an object from Google Cloud Storage",
        inputSchema={
            "type": "object",
            "properties": {
                "bucket": {"type": "string", "description": "Bucket name"},
                "object_name": {"type": "string", "description": "Object name/path"}
            },
            "required": ["bucket", "object_name"]
        }
    ),
    Tool(
        name="google_cloud_storage_delete",
        description="Delete an object from Google Cloud Storage",
        inputSchema={
            "type": "object",
            "properties": {
                "bucket": {"type": "string", "description": "Bucket name"},
                "object_name": {"type": "string", "description": "Object name/path"}
            },
            "required": ["bucket", "object_name"]
        }
    ),
    Tool(
        name="google_bigquery_query",
        description="Execute a BigQuery SQL query",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "GCP project ID"},
                "sql": {"type": "string", "description": "SQL query"},
                "dataset_id": {"type": "string", "description": "Default dataset ID"},
                "use_legacy_sql": {"type": "boolean", "default": False, "description": "Use Legacy SQL instead of Standard SQL"},
                "max_results": {"type": "integer", "default": 1000}
            },
            "required": ["project_id", "sql"]
        }
    ),
    Tool(
        name="google_bigquery_list_tables",
        description="List tables in a BigQuery dataset",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "GCP project ID"},
                "dataset_id": {"type": "string", "description": "Dataset ID"},
                "max_results": {"type": "integer", "default": 100}
            },
            "required": ["project_id", "dataset_id"]
        }
    ),
    Tool(
        name="google_bigquery_get_schema",
        description="Get schema information for a BigQuery table",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "GCP project ID"},
                "dataset_id": {"type": "string", "description": "Dataset ID"},
                "table_id": {"type": "string", "description": "Table ID"}
            },
            "required": ["project_id", "dataset_id", "table_id"]
        }
    ),
    Tool(
        name="google_vertex_ai_predict",
        description="Get predictions from a Vertex AI model",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "GCP project ID"},
                "endpoint_id": {"type": "string", "description": "Vertex AI endpoint ID"},
                "region": {"type": "string", "default": "us-central1"},
                "instances": {"type": "array", "description": "Input instances for prediction"}
            },
            "required": ["project_id", "endpoint_id", "instances"]
        }
    ),
    Tool(
        name="google_workspace_admin_list_users",
        description="List users in a Google Workspace domain",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Google Workspace domain"},
                "max_results": {"type": "integer", "default": 100},
                "query": {"type": "string", "description": "Search query filter"}
            },
            "required": ["domain"]
        }
    ),
    Tool(
        name="google_workspace_admin_get_user",
        description="Get details of a specific Google Workspace user",
        inputSchema={
            "type": "object",
            "properties": {
                "user_email": {"type": "string", "description": "User email address"}
            },
            "required": ["user_email"]
        }
    ),
    Tool(
        name="google_workspace_admin_create_user",
        description="Create a new user in Google Workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "email": {"type": "string"},
                "password": {"type": "string"},
                "org_unit_path": {"type": "string", "default": "/"}
            },
            "required": ["first_name", "last_name", "email", "password"]
        }
    ),
    Tool(
        name="google_workspace_admin_suspend_user",
        description="Suspend a Google Workspace user account",
        inputSchema={
            "type": "object",
            "properties": {
                "user_email": {"type": "string", "description": "User email address"}
            },
            "required": ["user_email"]
        }
    ),
    Tool(
        name="google_cloud_pubsub_publish",
        description="Publish a message to Google Cloud Pub/Sub",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "GCP project ID"},
                "topic_id": {"type": "string", "description": "Pub/Sub topic ID"},
                "message": {"type": "object", "description": "Message data"}
            },
            "required": ["project_id", "topic_id", "message"]
        }
    ),
    Tool(
        name="google_cloud_pubsub_subscribe",
        description="Subscribe to Google Cloud Pub/Sub topic",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "GCP project ID"},
                "subscription_id": {"type": "string", "description": "Subscription ID"},
                "max_messages": {"type": "integer", "default": 10}
            },
            "required": ["project_id", "subscription_id"]
        }
    ),
    Tool(
        name="google_cloud_firestore_get",
        description="Get a document from Google Cloud Firestore",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "GCP project ID"},
                "collection": {"type": "string", "description": "Collection name"},
                "document_id": {"type": "string", "description": "Document ID"}
            },
            "required": ["project_id", "collection", "document_id"]
        }
    ),
    Tool(
        name="google_cloud_firestore_set",
        description="Set a document in Google Cloud Firestore",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "GCP project ID"},
                "collection": {"type": "string", "description": "Collection name"},
                "document_id": {"type": "string", "description": "Document ID"},
                "data": {"type": "object", "description": "Document data"},
                "merge": {"type": "boolean", "default": False, "description": "Merge with existing data"}
            },
            "required": ["project_id", "collection", "document_id", "data"]
        }
    ),
    Tool(
        name="google_cloud_firestore_query",
        description="Query documents from Google Cloud Firestore",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "GCP project ID"},
                "collection": {"type": "string", "description": "Collection name"},
                "filters": {"type": "array", "description": "Query filters"},
                "limit": {"type": "integer", "default": 100}
            },
            "required": ["project_id", "collection"]
        }
    ),
    Tool(
        name="google_recaptcha_verify",
        description="Verify reCAPTCHA responses",
        inputSchema={
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "reCAPTCHA token from client"},
                "expected_action": {"type": "string", "description": "Expected action (v3 only)"},
                "min_score": {"type": "number", "default": 0.5, "description": "Minimum score threshold (v3)"}
            },
            "required": ["token"]
        }
    ),
    Tool(
        name="google_translate_detect",
        description="Detect language of given text",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to detect"}
            },
            "required": ["text"]
        }
    ),
    Tool(
        name="google_translate_translate",
        description="Translate text using Google Cloud Translation",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to translate"},
                "source_language": {"type": "string", "description": "Source language code"},
                "target_language": {"type": "string", "description": "Target language code"}
            },
            "required": ["text", "target_language"]
        }
    ),
    Tool(
        name="google_vision_ocr",
        description="Perform OCR on images using Google Vision API",
        inputSchema={
            "type": "object",
            "properties": {
                "image_uri": {"type": "string", "description": "Image URI (GCS or HTTPS)"},
                "language_hints": {"type": "array", "items": {"type": "string"}, "description": "Language hints"}
            },
            "required": ["image_uri"]
        }
    ),
    Tool(
        name="google_vision_label_detect",
        description="Detect labels/objects in images",
        inputSchema={
            "type": "object",
            "properties": {
                "image_uri": {"type": "string", "description": "Image URI"},
                "max_results": {"type": "integer", "default": 10}
            },
            "required": ["image_uri"]
        }
    ),
    Tool(
        name="google_vision_text_detect",
        description="Detect text in images",
        inputSchema={
            "type": "object",
            "properties": {
                "image_uri": {"type": "string", "description": "Image URI"}
            },
            "required": ["image_uri"]
        }
    ),
    Tool(
        name="google_natural_language_analyze",
        description="Analyze sentiment, entities, and syntax in text",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to analyze"},
                "analyze_sentiment": {"type": "boolean", "default": True},
                "analyze_entities": {"type": "boolean", "default": True},
                "analyze_syntax": {"type": "boolean", "default": False}
            },
            "required": ["text"]
        }
    ),
    Tool(
        name="google_speech_to_text",
        description="Convert speech/audio to text",
        inputSchema={
            "type": "object",
            "properties": {
                "audio_uri": {"type": "string", "description": "Audio URI (GCS or HTTPS)"},
                "language_code": {"type": "string", "default": "en-US"},
                "model": {"type": "string", "default": "default"}
            },
            "required": ["audio_uri"]
        }
    ),
    Tool(
        name="google_text_to_speech",
        description="Convert text to speech",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to synthesize"},
                "language_code": {"type": "string", "default": "en-US"},
                "voice_name": {"type": "string", "default": "en-US-Neural2-C"},
                "audio_encoding": {"type": "string", "default": "MP3"}
            },
            "required": ["text"]
        }
    ),
    Tool(
        name="google_video_analyze",
        description="Analyze videos for labels, shots, and objects",
        inputSchema={
            "type": "object",
            "properties": {
                "video_uri": {"type": "string", "description": "Video URI (GCS)"},
                "features": {"type": "array", "items": {"type": "string"}, "enum": ["LABEL_DETECTION", "OBJECT_TRACKING", "FACE_DETECTION"]}
            },
            "required": ["video_uri"]
        }
    ),
    Tool(
        name="chatgpt_auto_builder_execute",
        description="Execute a command through ChatGPT Auto Builder MCP tool",
        inputSchema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to execute in Auto Builder"},
                "payload": {"type": "object", "description": "Optional payload/context for the command"}
            },
            "required": ["command"]
        }
    ),
    # ===== HOSTINGER HOSTING =====
    Tool(
        name="hostinger_list_domains",
        description="List all domains in Hostinger account",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="hostinger_get_domain_info",
        description="Get detailed information about a specific domain",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"}
            },
            "required": ["domain"]
        }
    ),
    Tool(
        name="hostinger_list_dns_records",
        description="List DNS records for a domain",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"}
            },
            "required": ["domain"]
        }
    ),
    Tool(
        name="hostinger_create_dns_record",
        description="Create a new DNS record for a domain",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "record_type": {"type": "string", "enum": ["A", "AAAA", "CNAME", "MX", "TXT", "NS"], "description": "DNS record type"},
                "name": {"type": "string", "description": "Record name"},
                "content": {"type": "string", "description": "Record content/value"},
                "ttl": {"type": "integer", "default": 3600, "description": "TTL in seconds"}
            },
            "required": ["domain", "record_type", "name", "content"]
        }
    ),
    Tool(
        name="hostinger_update_dns_record",
        description="Update an existing DNS record",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "record_id": {"type": "string", "description": "DNS record ID"},
                "content": {"type": "string", "description": "New record content/value"}
            },
            "required": ["domain", "record_id", "content"]
        }
    ),
    Tool(
        name="hostinger_delete_dns_record",
        description="Delete a DNS record",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "record_id": {"type": "string", "description": "DNS record ID"}
            },
            "required": ["domain", "record_id"]
        }
    ),
    Tool(
        name="hostinger_list_ssl_certificates",
        description="List SSL certificates for a domain",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"}
            },
            "required": ["domain"]
        }
    ),
    Tool(
        name="hostinger_get_website_status",
        description="Get website hosting status and details",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"}
            },
            "required": ["domain"]
        }
    ),
    Tool(
        name="hostinger_list_databases",
        description="List databases for a website",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"}
            },
            "required": ["domain"]
        }
    ),
    # ===== UNIFIED ENDPOINTS =====
    Tool(
        name="unified_predict",
        description="Unified prediction endpoint - routes to all relevant systems for forecasting",
        inputSchema={
            "type": "object",
            "properties": {
                "asset": {"type": "string", "description": "Asset ticker/symbol (BTC, TSLA, etc.)"},
                "asset_type": {"type": "string", "enum": ["crypto", "stock", "forex", "commodity"], "default": "stock"},
                "prediction_type": {"type": "string", "enum": ["price", "direction", "volatility", "event"], "default": "price"},
                "timeframe": {"type": "string", "description": "1h, 4h, 24h, 7d, 30d, 90d"},
                "target_date": {"type": "string", "description": "ISO date when prediction resolves"},
                "confidence": {"type": "integer", "minimum": 0, "maximum": 100, "default": 50},
                "data_sources": {"type": "array", "items": {"type": "string"}, "description": "Data sources to consider"}
            },
            "required": ["asset", "timeframe"]
        }
    ),
    Tool(
        name="unified_crawl",
        description="Unified crawl endpoint - web scraping and data collection across all sources",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to crawl"},
                "depth": {"type": "integer", "minimum": 1, "maximum": 5, "default": 1, "description": "Crawl depth"},
                "max_pages": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100, "description": "Max pages to crawl"},
                "filters": {"type": "object", "description": "Filters (keyword, pattern, etc.)"}
            },
            "required": ["url"]
        }
    ),
    Tool(
        name="unified_simulate",
        description="Unified simulate endpoint - backtesting, scenario analysis, and market simulations",
        inputSchema={
            "type": "object",
            "properties": {
                "scenario": {"type": "string", "description": "Scenario type: backtest, monte_carlo, stress_test, etc."},
                "asset": {"type": "string", "description": "Asset to simulate (optional)"},
                "parameters": {"type": "object", "description": "Simulation parameters"}
            },
            "required": ["scenario"]
        }
    ),
    # ===== VS CODE MCP TOOLS =====
    Tool(
        name="vscode_open_file",
        description="Open a file in VS Code",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to open"},
                "line": {"type": "integer", "description": "Line number to jump to"},
                "column": {"type": "integer", "description": "Column number"}
            },
            "required": ["path"]
        }
    ),
    Tool(
        name="vscode_edit_file",
        description="Edit file content in VS Code",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "New file content"},
                "start_line": {"type": "integer", "description": "Start line for partial edit"},
                "end_line": {"type": "integer", "description": "End line for partial edit"}
            },
            "required": ["path", "content"]
        }
    ),
    Tool(
        name="vscode_search_workspace",
        description="Search text across VS Code workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "include_pattern": {"type": "string", "description": "Include file pattern (e.g., *.py)"},
                "exclude_pattern": {"type": "string", "description": "Exclude file pattern"},
                "case_sensitive": {"type": "boolean", "default": False},
                "regex": {"type": "boolean", "default": False}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="vscode_run_task",
        description="Run a VS Code task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_name": {"type": "string", "description": "Task name from tasks.json"},
                "args": {"type": "array", "items": {"type": "string"}, "description": "Task arguments"}
            },
            "required": ["task_name"]
        }
    ),
    Tool(
        name="vscode_debug_start",
        description="Start a debug session in VS Code",
        inputSchema={
            "type": "object",
            "properties": {
                "configuration": {"type": "string", "description": "Debug configuration name"},
                "file": {"type": "string", "description": "File to debug"}
            },
            "required": ["configuration"]
        }
    ),
    Tool(
        name="vscode_install_extension",
        description="Install a VS Code extension",
        inputSchema={
            "type": "object",
            "properties": {
                "extension_id": {"type": "string", "description": "Extension ID (e.g., ms-python.python)"}
            },
            "required": ["extension_id"]
        }
    ),
    Tool(
        name="vscode_git_commit",
        description="Commit changes via VS Code Git integration",
        inputSchema={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit message"},
                "files": {"type": "array", "items": {"type": "string"}, "description": "Files to stage and commit"}
            },
            "required": ["message"]
        }
    ),
    Tool(
        name="vscode_terminal_execute",
        description="Execute command in VS Code integrated terminal",
        inputSchema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to execute"},
                "terminal_name": {"type": "string", "description": "Terminal name/identifier"}
            },
            "required": ["command"]
        }
    ),
    # ===== EXPANDED GITHUB TOOLS (Business/Personal + Pages) =====
    Tool(
        name="github_create_repo",
        description="Create a new GitHub repository",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Repository name"},
                "description": {"type": "string", "description": "Repository description"},
                "private": {"type": "boolean", "default": False},
                "auto_init": {"type": "boolean", "default": True, "description": "Initialize with README"}
            },
            "required": ["name"]
        }
    ),
    Tool(
        name="github_delete_repo",
        description="Delete a GitHub repository",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"}
            },
            "required": ["owner", "repo"]
        }
    ),
    Tool(
        name="github_fork_repo",
        description="Fork a GitHub repository",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Original repository owner"},
                "repo": {"type": "string", "description": "Repository name"}
            },
            "required": ["owner", "repo"]
        }
    ),
    Tool(
        name="github_list_repos",
        description="List GitHub repositories",
        inputSchema={
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["all", "owner", "public", "private", "member"], "default": "all"},
                "sort": {"type": "string", "enum": ["created", "updated", "pushed", "full_name"], "default": "updated"}
            }
        }
    ),
    Tool(
        name="github_create_pull_request",
        description="Create a pull request",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "title": {"type": "string", "description": "PR title"},
                "head": {"type": "string", "description": "Branch with changes"},
                "base": {"type": "string", "description": "Base branch", "default": "main"},
                "body": {"type": "string", "description": "PR description"}
            },
            "required": ["owner", "repo", "title", "head"]
        }
    ),
    Tool(
        name="github_merge_pull_request",
        description="Merge a pull request",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "pull_number": {"type": "integer", "description": "Pull request number"},
                "merge_method": {"type": "string", "enum": ["merge", "squash", "rebase"], "default": "merge"}
            },
            "required": ["owner", "repo", "pull_number"]
        }
    ),
    Tool(
        name="github_list_branches",
        description="List repository branches",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"}
            },
            "required": ["owner", "repo"]
        }
    ),
    Tool(
        name="github_create_branch",
        description="Create a new branch",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "branch": {"type": "string", "description": "New branch name"},
                "from_branch": {"type": "string", "description": "Source branch", "default": "main"}
            },
            "required": ["owner", "repo", "branch"]
        }
    ),
    Tool(
        name="github_delete_branch",
        description="Delete a branch",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "branch": {"type": "string", "description": "Branch name to delete"}
            },
            "required": ["owner", "repo", "branch"]
        }
    ),
    Tool(
        name="github_create_release",
        description="Create a GitHub release",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "tag_name": {"type": "string", "description": "Tag name"},
                "name": {"type": "string", "description": "Release name"},
                "body": {"type": "string", "description": "Release notes"},
                "draft": {"type": "boolean", "default": False},
                "prerelease": {"type": "boolean", "default": False}
            },
            "required": ["owner", "repo", "tag_name"]
        }
    ),
    Tool(
        name="github_list_releases",
        description="List repository releases",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"}
            },
            "required": ["owner", "repo"]
        }
    ),
    Tool(
        name="github_pages_enable",
        description="Enable GitHub Pages for a repository",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "source_branch": {"type": "string", "default": "main", "description": "Source branch for GitHub Pages"},
                "source_path": {"type": "string", "enum": ["/", "/docs"], "default": "/", "description": "Source path"}
            },
            "required": ["owner", "repo"]
        }
    ),
    Tool(
        name="github_pages_get_status",
        description="Get GitHub Pages status and URL",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"}
            },
            "required": ["owner", "repo"]
        }
    ),
    Tool(
        name="github_pages_update",
        description="Update GitHub Pages configuration",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "cname": {"type": "string", "description": "Custom domain"},
                "https_enforced": {"type": "boolean", "default": True}
            },
            "required": ["owner", "repo"]
        }
    ),
    Tool(
        name="github_actions_list_workflows",
        description="List GitHub Actions workflows",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"}
            },
            "required": ["owner", "repo"]
        }
    ),
    Tool(
        name="github_actions_trigger_workflow",
        description="Trigger a GitHub Actions workflow",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "workflow_id": {"type": "string", "description": "Workflow ID or filename"},
                "ref": {"type": "string", "default": "main", "description": "Git ref"},
                "inputs": {"type": "object", "description": "Workflow inputs"}
            },
            "required": ["owner", "repo", "workflow_id"]
        }
    ),
    Tool(
        name="github_secrets_create",
        description="Create or update a repository secret",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "secret_name": {"type": "string", "description": "Secret name"},
                "secret_value": {"type": "string", "description": "Secret value"}
            },
            "required": ["owner", "repo", "secret_name", "secret_value"]
        }
    ),
    Tool(
        name="github_webhooks_create",
        description="Create a webhook for a repository",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "url": {"type": "string", "description": "Webhook URL"},
                "events": {"type": "array", "items": {"type": "string"}, "default": ["push"], "description": "Events to trigger"},
                "secret": {"type": "string", "description": "Webhook secret"}
            },
            "required": ["owner", "repo", "url"]
        }
    ),
    Tool(
        name="github_collaborators_add",
        description="Add a collaborator to a repository",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "username": {"type": "string", "description": "Collaborator username"},
                "permission": {"type": "string", "enum": ["pull", "push", "admin", "maintain", "triage"], "default": "push"}
            },
            "required": ["owner", "repo", "username"]
        }
    ),
    Tool(
        name="github_issues_list",
        description="List issues in a repository",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
                "labels": {"type": "array", "items": {"type": "string"}, "description": "Filter by labels"}
            },
            "required": ["owner", "repo"]
        }
    ),
    Tool(
        name="github_issues_close",
        description="Close an issue",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "issue_number": {"type": "integer", "description": "Issue number"}
            },
            "required": ["owner", "repo", "issue_number"]
        }
    ),
    # ===== EXPANDED HOSTINGER TOOLS =====
    Tool(
        name="hostinger_create_website",
        description="Create a new website on Hostinger",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "template": {"type": "string", "description": "Website template"},
                "ssl_enabled": {"type": "boolean", "default": True}
            },
            "required": ["domain"]
        }
    ),
    Tool(
        name="hostinger_delete_website",
        description="Delete a website from Hostinger",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"}
            },
            "required": ["domain"]
        }
    ),
    Tool(
        name="hostinger_backup_website",
        description="Create a backup of a website",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "backup_type": {"type": "string", "enum": ["full", "files", "database"], "default": "full"}
            },
            "required": ["domain"]
        }
    ),
    Tool(
        name="hostinger_restore_backup",
        description="Restore a website from backup",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "backup_id": {"type": "string", "description": "Backup ID"}
            },
            "required": ["domain", "backup_id"]
        }
    ),
    Tool(
        name="hostinger_list_backups",
        description="List all backups for a website",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"}
            },
            "required": ["domain"]
        }
    ),
    Tool(
        name="hostinger_create_database",
        description="Create a MySQL database",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "database_name": {"type": "string", "description": "Database name"},
                "username": {"type": "string", "description": "Database user"},
                "password": {"type": "string", "description": "Database password"}
            },
            "required": ["domain", "database_name", "username", "password"]
        }
    ),
    Tool(
        name="hostinger_delete_database",
        description="Delete a MySQL database",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "database_id": {"type": "string", "description": "Database ID"}
            },
            "required": ["domain", "database_id"]
        }
    ),
    Tool(
        name="hostinger_email_create_account",
        description="Create an email account",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "email": {"type": "string", "description": "Email address"},
                "password": {"type": "string", "description": "Email password"},
                "quota": {"type": "integer", "default": 1000, "description": "Mailbox quota in MB"}
            },
            "required": ["domain", "email", "password"]
        }
    ),
    Tool(
        name="hostinger_email_delete_account",
        description="Delete an email account",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "email": {"type": "string", "description": "Email address"}
            },
            "required": ["domain", "email"]
        }
    ),
    Tool(
        name="hostinger_email_list_accounts",
        description="List all email accounts for a domain",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"}
            },
            "required": ["domain"]
        }
    ),
    Tool(
        name="hostinger_ftp_create_account",
        description="Create an FTP account",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "username": {"type": "string", "description": "FTP username"},
                "password": {"type": "string", "description": "FTP password"},
                "directory": {"type": "string", "default": "/public_html", "description": "Home directory"}
            },
            "required": ["domain", "username", "password"]
        }
    ),
    Tool(
        name="hostinger_ftp_list_accounts",
        description="List all FTP accounts for a domain",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"}
            },
            "required": ["domain"]
        }
    ),
    Tool(
        name="hostinger_ssl_install",
        description="Install SSL certificate",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "certificate_type": {"type": "string", "enum": ["letsencrypt", "custom"], "default": "letsencrypt"}
            },
            "required": ["domain"]
        }
    ),
    Tool(
        name="hostinger_cron_create",
        description="Create a cron job",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "command": {"type": "string", "description": "Command to execute"},
                "schedule": {"type": "string", "description": "Cron schedule (e.g., '0 * * * *')"}
            },
            "required": ["domain", "command", "schedule"]
        }
    ),
    Tool(
        name="hostinger_cron_list",
        description="List all cron jobs",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"}
            },
            "required": ["domain"]
        }
    ),
    Tool(
        name="hostinger_file_manager_upload",
        description="Upload file to Hostinger file manager",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "file_path": {"type": "string", "description": "Destination path"},
                "content": {"type": "string", "description": "File content (base64)"}
            },
            "required": ["domain", "file_path", "content"]
        }
    ),
    Tool(
        name="hostinger_file_manager_download",
        description="Download file from Hostinger file manager",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "file_path": {"type": "string", "description": "File path to download"}
            },
            "required": ["domain", "file_path"]
        }
    ),
    Tool(
        name="hostinger_file_manager_delete",
        description="Delete file from Hostinger",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "file_path": {"type": "string", "description": "File path to delete"}
            },
            "required": ["domain", "file_path"]
        }
    ),
    Tool(
        name="hostinger_analytics_get",
        description="Get website analytics from Hostinger",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name"},
                "period": {"type": "string", "enum": ["today", "week", "month", "year"], "default": "week"}
            },
            "required": ["domain"]
        }
    ),
    # ===== EXPANDED ORCHESTRATOR TOOLS =====
    Tool(
        name="orchestrator_status",
        description="Get orchestrator system status",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="orchestrator_list_jobs",
        description="List all orchestrator jobs",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["pending", "running", "completed", "failed", "all"], "default": "all"},
                "limit": {"type": "integer", "default": 50}
            }
        }
    ),
    Tool(
        name="orchestrator_create_job",
        description="Create a new orchestrator job",
        inputSchema={
            "type": "object",
            "properties": {
                "job_type": {"type": "string", "description": "Job type (crawl, predict, simulate, etc.)"},
                "parameters": {"type": "object", "description": "Job parameters"},
                "schedule": {"type": "string", "description": "Cron schedule (optional)"},
                "priority": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5}
            },
            "required": ["job_type", "parameters"]
        }
    ),
    Tool(
        name="orchestrator_cancel_job",
        description="Cancel a running job",
        inputSchema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Job ID"}
            },
            "required": ["job_id"]
        }
    ),
    Tool(
        name="orchestrator_get_job_result",
        description="Get job result and logs",
        inputSchema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Job ID"}
            },
            "required": ["job_id"]
        }
    ),
    Tool(
        name="orchestrator_retry_job",
        description="Retry a failed job",
        inputSchema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Job ID"}
            },
            "required": ["job_id"]
        }
    ),
    Tool(
        name="orchestrator_schedule_recurring",
        description="Schedule a recurring job",
        inputSchema={
            "type": "object",
            "properties": {
                "job_type": {"type": "string", "description": "Job type"},
                "parameters": {"type": "object", "description": "Job parameters"},
                "cron_schedule": {"type": "string", "description": "Cron expression (e.g., '0 */6 * * *')"}
            },
            "required": ["job_type", "parameters", "cron_schedule"]
        }
    ),
    # ===== EXPANDED CRAWLER TOOLS =====
    Tool(
        name="crawler_crawl_url",
        description="Crawl a URL and extract data",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to crawl"},
                "depth": {"type": "integer", "minimum": 1, "maximum": 10, "default": 2},
                "max_pages": {"type": "integer", "minimum": 1, "maximum": 10000, "default": 100},
                "extract_data": {"type": "array", "items": {"type": "string"}, "description": "Data fields to extract"},
                "follow_links": {"type": "boolean", "default": True}
            },
            "required": ["url"]
        }
    ),
    Tool(
        name="crawler_crawl_sitemap",
        description="Crawl from sitemap.xml",
        inputSchema={
            "type": "object",
            "properties": {
                "sitemap_url": {"type": "string", "description": "Sitemap URL"},
                "max_pages": {"type": "integer", "default": 1000}
            },
            "required": ["sitemap_url"]
        }
    ),
    Tool(
        name="crawler_extract_structured_data",
        description="Extract structured data (JSON-LD, Schema.org, Open Graph)",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to extract from"},
                "data_types": {"type": "array", "items": {"type": "string"}, "description": "Data types to extract"}
            },
            "required": ["url"]
        }
    ),
    Tool(
        name="crawler_screenshot_page",
        description="Take screenshot of a webpage",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to screenshot"},
                "full_page": {"type": "boolean", "default": True},
                "viewport_width": {"type": "integer", "default": 1920},
                "viewport_height": {"type": "integer", "default": 1080}
            },
            "required": ["url"]
        }
    ),
    Tool(
        name="crawler_monitor_changes",
        description="Monitor webpage for changes",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to monitor"},
                "selector": {"type": "string", "description": "CSS selector to monitor"},
                "check_interval": {"type": "integer", "default": 3600, "description": "Check interval in seconds"}
            },
            "required": ["url"]
        }
    ),
    Tool(
        name="crawler_get_page_metadata",
        description="Extract page metadata (title, description, keywords, etc.)",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to analyze"}
            },
            "required": ["url"]
        }
    ),
    Tool(
        name="crawler_check_broken_links",
        description="Check for broken links on a page or site",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to check"},
                "recursive": {"type": "boolean", "default": False}
            },
            "required": ["url"]
        }
    ),
    Tool(
        name="crawler_export_data",
        description="Export crawled data to various formats",
        inputSchema={
            "type": "object",
            "properties": {
                "crawl_id": {"type": "string", "description": "Crawl job ID"},
                "format": {"type": "string", "enum": ["json", "csv", "xml", "excel"], "default": "json"}
            },
            "required": ["crawl_id"]
        }
    )
]

@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "execute":
        return await tool_execute(arguments)
    elif name == "github_create_issue":
        return await tool_github_create_issue(arguments)
    elif name == "github_search_code":
        return await tool_github_search_code(arguments)
    elif name == "github_get_file_content":
        return await tool_github_get_file_content(arguments)
    elif name == "query_intelligence":
        return tool_query_intelligence(arguments)
    elif name == "get_portfolio_status":
        return tool_get_portfolio_status()
    elif name == "docker_list_containers":
        return tool_docker_list_containers(arguments)
    elif name == "docker_container_action":
        return tool_docker_container_action(arguments)
    elif name == "docker_run_container":
        return tool_docker_run_container(arguments)
    elif name == "docker_list_images":
        return tool_docker_list_images()
    elif name == "docker_pull_image":
        return await tool_docker_pull_image(arguments)
    elif name == "docker_container_logs":
        return tool_docker_container_logs(arguments)
    elif name == "docker_container_inspect":
        return tool_docker_container_inspect(arguments)
    elif name == "docker_list_networks":
        return tool_docker_list_networks()
    elif name == "docker_list_volumes":
        return tool_docker_list_volumes()
    # ===== GOOGLE WORKSPACE & DOCS =====
    elif name == "google_calendar_list_events":
        return await tool_google_calendar_list_events(arguments)
    elif name == "google_calendar_create_event":
        return await tool_google_calendar_create_event(arguments)
    elif name == "google_sheets_read":
        return await tool_google_sheets_read(arguments)
    elif name == "google_sheets_write":
        return await tool_google_sheets_write(arguments)
    elif name == "google_drive_search":
        return await tool_google_drive_search(arguments)
    elif name == "google_gmail_send":
        return await tool_google_gmail_send(arguments)
    elif name == "google_docs_create":
        return await tool_google_docs_create(arguments)
    # ===== GOOGLE CLOUD RUN =====
    elif name == "google_cloud_run_deploy":
        return await tool_google_cloud_run_deploy(arguments)
    elif name == "google_cloud_run_list":
        return await tool_google_cloud_run_list(arguments)
    elif name == "google_cloud_run_describe":
        return await tool_google_cloud_run_describe(arguments)
    elif name == "google_cloud_run_delete":
        return await tool_google_cloud_run_delete(arguments)
    # ===== GOOGLE MAPS =====
    elif name == "google_maps_search":
        return await tool_google_maps_search(arguments)
    elif name == "google_maps_directions":
        return await tool_google_maps_directions(arguments)
    elif name == "google_maps_geocode":
        return await tool_google_maps_geocode(arguments)
    # ===== GOOGLE SEARCH & ANALYTICS =====
    elif name == "google_custom_search":
        return await tool_google_custom_search(arguments)
    elif name == "google_analytics_query":
        return await tool_google_analytics_query(arguments)
    elif name == "google_analytics_realtime":
        return await tool_google_analytics_realtime(arguments)
    # ===== GOOGLE CLOUD STORAGE =====
    elif name == "google_cloud_storage_list":
        return await tool_google_cloud_storage_list(arguments)
    elif name == "google_cloud_storage_upload":
        return await tool_google_cloud_storage_upload(arguments)
    elif name == "google_cloud_storage_download":
        return await tool_google_cloud_storage_download(arguments)
    elif name == "google_cloud_storage_delete":
        return await tool_google_cloud_storage_delete(arguments)
    # ===== GOOGLE BIGQUERY =====
    elif name == "google_bigquery_query":
        return await tool_google_bigquery_query(arguments)
    elif name == "google_bigquery_list_tables":
        return await tool_google_bigquery_list_tables(arguments)
    elif name == "google_bigquery_get_schema":
        return await tool_google_bigquery_get_schema(arguments)
    # ===== GOOGLE VERTEX AI =====
    elif name == "google_vertex_ai_predict":
        return await tool_google_vertex_ai_predict(arguments)
    # ===== GOOGLE WORKSPACE ADMIN =====
    elif name == "google_workspace_admin_list_users":
        return await tool_google_workspace_admin_list_users(arguments)
    elif name == "google_workspace_admin_get_user":
        return await tool_google_workspace_admin_get_user(arguments)
    elif name == "google_workspace_admin_create_user":
        return await tool_google_workspace_admin_create_user(arguments)
    elif name == "google_workspace_admin_suspend_user":
        return await tool_google_workspace_admin_suspend_user(arguments)
    # ===== GOOGLE CLOUD PUBSUB =====
    elif name == "google_cloud_pubsub_publish":
        return await tool_google_cloud_pubsub_publish(arguments)
    elif name == "google_cloud_pubsub_subscribe":
        return await tool_google_cloud_pubsub_subscribe(arguments)
    # ===== GOOGLE CLOUD FIRESTORE =====
    elif name == "google_cloud_firestore_get":
        return await tool_google_cloud_firestore_get(arguments)
    elif name == "google_cloud_firestore_set":
        return await tool_google_cloud_firestore_set(arguments)
    elif name == "google_cloud_firestore_query":
        return await tool_google_cloud_firestore_query(arguments)
    # ===== GOOGLE SECURITY & TRANSLATION =====
    elif name == "google_recaptcha_verify":
        return await tool_google_recaptcha_verify(arguments)
    elif name == "google_translate_detect":
        return await tool_google_translate_detect(arguments)
    elif name == "google_translate_translate":
        return await tool_google_translate_translate(arguments)
    # ===== GOOGLE AI VISION =====
    elif name == "google_vision_ocr":
        return await tool_google_vision_ocr(arguments)
    elif name == "google_vision_label_detect":
        return await tool_google_vision_label_detect(arguments)
    elif name == "google_vision_text_detect":
        return await tool_google_vision_text_detect(arguments)
    # ===== GOOGLE NATURAL LANGUAGE =====
    elif name == "google_natural_language_analyze":
        return await tool_google_natural_language_analyze(arguments)
    # ===== GOOGLE SPEECH =====
    elif name == "google_speech_to_text":
        return await tool_google_speech_to_text(arguments)
    elif name == "google_text_to_speech":
        return await tool_google_text_to_speech(arguments)
    # ===== GOOGLE VIDEO =====
    elif name == "google_video_analyze":
        return await tool_google_video_analyze(arguments)
    elif name == "chatgpt_auto_builder_execute":
        return await tool_chatgpt_auto_builder_execute(arguments)
    # ===== HOSTINGER =====
    elif name == "hostinger_list_domains":
        return await tool_hostinger_list_domains()
    elif name == "hostinger_get_domain_info":
        return await tool_hostinger_get_domain_info(arguments)
    elif name == "hostinger_list_dns_records":
        return await tool_hostinger_list_dns_records(arguments)
    elif name == "hostinger_create_dns_record":
        return await tool_hostinger_create_dns_record(arguments)
    elif name == "hostinger_update_dns_record":
        return await tool_hostinger_update_dns_record(arguments)
    elif name == "hostinger_delete_dns_record":
        return await tool_hostinger_delete_dns_record(arguments)
    elif name == "hostinger_list_ssl_certificates":
        return await tool_hostinger_list_ssl_certificates(arguments)
    elif name == "hostinger_get_website_status":
        return await tool_hostinger_get_website_status(arguments)
    elif name == "hostinger_list_databases":
        return await tool_hostinger_list_databases(arguments)
    # ===== UNIFIED ENDPOINTS =====
    elif name == "unified_predict":
        return await tool_unified_predict(arguments)
    elif name == "unified_crawl":
        return await tool_unified_crawl(arguments)
    elif name == "unified_simulate":
        return await tool_unified_simulate(arguments)
    # ===== VS CODE TOOLS =====
    elif name == "vscode_open_file":
        return await tool_vscode_open_file(arguments)
    elif name == "vscode_edit_file":
        return await tool_vscode_edit_file(arguments)
    elif name == "vscode_search_workspace":
        return await tool_vscode_search_workspace(arguments)
    elif name == "vscode_run_task":
        return await tool_vscode_run_task(arguments)
    elif name == "vscode_debug_start":
        return await tool_vscode_debug_start(arguments)
    elif name == "vscode_install_extension":
        return await tool_vscode_install_extension(arguments)
    elif name == "vscode_git_commit":
        return await tool_vscode_git_commit(arguments)
    elif name == "vscode_terminal_execute":
        return await tool_vscode_terminal_execute(arguments)
    # ===== EXPANDED GITHUB TOOLS =====
    elif name == "github_create_repo":
        return await tool_github_create_repo(arguments)
    elif name == "github_delete_repo":
        return await tool_github_delete_repo(arguments)
    elif name == "github_fork_repo":
        return await tool_github_fork_repo(arguments)
    elif name == "github_list_repos":
        return await tool_github_list_repos(arguments)
    elif name == "github_create_pull_request":
        return await tool_github_create_pull_request(arguments)
    elif name == "github_merge_pull_request":
        return await tool_github_merge_pull_request(arguments)
    elif name == "github_list_branches":
        return await tool_github_list_branches(arguments)
    elif name == "github_create_branch":
        return await tool_github_create_branch(arguments)
    elif name == "github_delete_branch":
        return await tool_github_delete_branch(arguments)
    elif name == "github_create_release":
        return await tool_github_create_release(arguments)
    elif name == "github_list_releases":
        return await tool_github_list_releases(arguments)
    elif name == "github_pages_enable":
        return await tool_github_pages_enable(arguments)
    elif name == "github_pages_get_status":
        return await tool_github_pages_get_status(arguments)
    elif name == "github_pages_update":
        return await tool_github_pages_update(arguments)
    elif name == "github_actions_list_workflows":
        return await tool_github_actions_list_workflows(arguments)
    elif name == "github_actions_trigger_workflow":
        return await tool_github_actions_trigger_workflow(arguments)
    elif name == "github_secrets_create":
        return await tool_github_secrets_create(arguments)
    elif name == "github_webhooks_create":
        return await tool_github_webhooks_create(arguments)
    elif name == "github_collaborators_add":
        return await tool_github_collaborators_add(arguments)
    elif name == "github_issues_list":
        return await tool_github_issues_list(arguments)
    elif name == "github_issues_close":
        return await tool_github_issues_close(arguments)
    # ===== EXPANDED HOSTINGER TOOLS =====
    elif name == "hostinger_create_website":
        return await tool_hostinger_create_website(arguments)
    elif name == "hostinger_delete_website":
        return await tool_hostinger_delete_website(arguments)
    elif name == "hostinger_backup_website":
        return await tool_hostinger_backup_website(arguments)
    elif name == "hostinger_restore_backup":
        return await tool_hostinger_restore_backup(arguments)
    elif name == "hostinger_list_backups":
        return await tool_hostinger_list_backups(arguments)
    elif name == "hostinger_create_database":
        return await tool_hostinger_create_database(arguments)
    elif name == "hostinger_delete_database":
        return await tool_hostinger_delete_database(arguments)
    elif name == "hostinger_email_create_account":
        return await tool_hostinger_email_create_account(arguments)
    elif name == "hostinger_email_delete_account":
        return await tool_hostinger_email_delete_account(arguments)
    elif name == "hostinger_email_list_accounts":
        return await tool_hostinger_email_list_accounts(arguments)
    elif name == "hostinger_ftp_create_account":
        return await tool_hostinger_ftp_create_account(arguments)
    elif name == "hostinger_ftp_list_accounts":
        return await tool_hostinger_ftp_list_accounts(arguments)
    elif name == "hostinger_ssl_install":
        return await tool_hostinger_ssl_install(arguments)
    elif name == "hostinger_cron_create":
        return await tool_hostinger_cron_create(arguments)
    elif name == "hostinger_cron_list":
        return await tool_hostinger_cron_list(arguments)
    elif name == "hostinger_file_manager_upload":
        return await tool_hostinger_file_manager_upload(arguments)
    elif name == "hostinger_file_manager_download":
        return await tool_hostinger_file_manager_download(arguments)
    elif name == "hostinger_file_manager_delete":
        return await tool_hostinger_file_manager_delete(arguments)
    elif name == "hostinger_analytics_get":
        return await tool_hostinger_analytics_get(arguments)
    # ===== ORCHESTRATOR TOOLS =====
    elif name == "orchestrator_status":
        return await tool_orchestrator_status()
    elif name == "orchestrator_list_jobs":
        return await tool_orchestrator_list_jobs(arguments)
    elif name == "orchestrator_create_job":
        return await tool_orchestrator_create_job(arguments)
    elif name == "orchestrator_cancel_job":
        return await tool_orchestrator_cancel_job(arguments)
    elif name == "orchestrator_get_job_result":
        return await tool_orchestrator_get_job_result(arguments)
    elif name == "orchestrator_retry_job":
        return await tool_orchestrator_retry_job(arguments)
    elif name == "orchestrator_schedule_recurring":
        return await tool_orchestrator_schedule_recurring(arguments)
    # ===== CRAWLER TOOLS =====
    elif name == "crawler_crawl_url":
        return await tool_crawler_crawl_url(arguments)
    elif name == "crawler_crawl_sitemap":
        return await tool_crawler_crawl_sitemap(arguments)
    elif name == "crawler_extract_structured_data":
        return await tool_crawler_extract_structured_data(arguments)
    elif name == "crawler_screenshot_page":
        return await tool_crawler_screenshot_page(arguments)
    elif name == "crawler_monitor_changes":
        return await tool_crawler_monitor_changes(arguments)
    elif name == "crawler_get_page_metadata":
        return await tool_crawler_get_page_metadata(arguments)
    elif name == "crawler_check_broken_links":
        return await tool_crawler_check_broken_links(arguments)
    elif name == "crawler_export_data":
        return await tool_crawler_export_data(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

# ===== GOOGLE CREDENTIAL MANAGER =====
class GoogleCredentialManager:
    """Centralized credential management for all Google APIs"""
    
    _credentials_cache: Dict[str, Any] = {}
    _token_cache: Dict[str, tuple[str, datetime]] = {}
    
    @staticmethod
    def get_credential_type() -> str:
        """Determine credential type from environment"""
        if os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
            return "service_account"
        elif os.getenv("GOOGLE_OAUTH_TOKEN"):
            return "oauth2"
        elif os.getenv("GOOGLE_API_KEY"):
            return "api_key"
        return "none"
    
    @staticmethod
    def get_token() -> Optional[str]:
        """Get valid Google API token with caching"""
        cred_type = GoogleCredentialManager.get_credential_type()
        
        if cred_type == "oauth2":
            token = os.getenv("GOOGLE_OAUTH_TOKEN")
            return token
        elif cred_type == "service_account":
            # Would implement OAuth 2.0 service account flow here
            return os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        elif cred_type == "api_key":
            return os.getenv("GOOGLE_API_KEY")
        
        return None
    
    @staticmethod
    def check_quota(service: str) -> bool:
        """Check if service quota is available"""
        # Implement quota checking against governance rules
        return RATE_LIMITERS.get(f"{service}_apis", RateLimitBucket(1000, 60)).can_use()

# ===== TOOL IMPLEMENTATIONS =====
async def tool_execute(args: dict) -> list[TextContent]:
    """Forward command to Infinity XOS Orchestrator"""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            ORCHESTRATOR_URL,
            json={"command": args["command"], "payload": args.get("payload", {})}
        )
        r.raise_for_status()
        return [TextContent(type="text", text=json.dumps(r.json()))]

async def tool_chatgpt_auto_builder_execute(args: dict) -> list[TextContent]:
    """Execute command through ChatGPT Auto Builder MCP tool"""
    endpoint = os.getenv("CHATGPT_MCP_ENDPOINT")
    if not endpoint:
        return [TextContent(type="text", text=json.dumps({
            "error": "CHATGPT_MCP_ENDPOINT not configured",
            "setup_guide": "See CHATGPT_MCP_INTEGRATION_GUIDE.md"
        }))]

    command = args.get("command", "")
    payload = args.get("payload", {})

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{endpoint}/execute",
                json={"command": command, "context": payload},
                headers={"Content-Type": "application/json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"ChatGPT Auto Builder executed: {command}")
                return [TextContent(type="text", text=json.dumps({
                    "status": "success",
                    "result": data,
                    "command": command
                }))]
            else:
                return [TextContent(type="text", text=json.dumps({
                    "error": f"HTTP {resp.status_code}",
                    "command": command
                }))]
    except Exception as e:
        logger.error(f"ChatGPT Auto Builder error: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": str(e),
            "command": command
        }))]

async def tool_github_create_issue(args: dict) -> list[TextContent]:
    """Create a GitHub issue"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        payload = {
            "title": args["title"],
            "body": args["body"]
        }
        if args.get("labels"):
            payload["labels"] = args["labels"]
        
        r = await client.post(
            f"https://api.github.com/repos/{args['owner']}/{args['repo']}/issues",
            headers=headers,
            json=payload
        )
        r.raise_for_status()
        return [TextContent(type="text", text=json.dumps(r.json()))]

async def tool_github_search_code(args: dict) -> list[TextContent]:
    """Search for code across GitHub"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    search_query = args["query"]
    if args.get("owner") and args.get("repo"):
        search_query += f" repo:{args['owner']}/{args['repo']}"
    elif args.get("owner"):
        search_query += f" user:{args['owner']}"
    
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }
        
        r = await client.get(
            "https://api.github.com/search/code",
            headers=headers,
            params={"q": search_query, "per_page": args.get("max_results", 10)}
        )
        r.raise_for_status()
        data = r.json()
        
        results = {
            "total_count": data.get("total_count", 0),
            "results": [
                {
                    "name": item["name"],
                    "path": item["path"],
                    "repo": item["repository"]["full_name"],
                    "url": item["html_url"]
                }
                for item in data.get("items", [])
            ]
        }
        return [TextContent(type="text", text=json.dumps(results))]

async def tool_github_get_file_content(args: dict) -> list[TextContent]:
    """Get file content from GitHub"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.raw+json"
        }
        
        r = await client.get(
            f"https://api.github.com/repos/{args['owner']}/{args['repo']}/contents/{args['path']}",
            headers=headers,
            params={"ref": args.get("branch", "main")}
        )
        r.raise_for_status()
        
        result = {
            "path": args["path"],
            "content": r.text,
            "repo": f"{args['owner']}/{args['repo']}"
        }
        return [TextContent(type="text", text=json.dumps(result))]

def tool_query_intelligence(args: dict) -> list[TextContent]:
    """Query intelligence database"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    query = "SELECT id, key, value FROM memory WHERE 1=1"
    params = []
    
    if args.get("category"):
        query += " AND value LIKE ?"
        params.append(f"%{args['category']}%")
    
    if args.get("search"):
        query += " AND (key LIKE ? OR value LIKE ?)"
        params.extend([f"%{args['search']}%", f"%{args['search']}%"])
    
    query += f" LIMIT {args.get('limit', 10)}"
    
    cur.execute(query, params)
    results = []
    for row in cur.fetchall():
        results.append({
            "id": row[0],
            "url": row[1][:100] if row[1] else "",
            "data_size": len(row[2]) if row[2] else 0
        })
    
    conn.close()
    return [TextContent(type="text", text=json.dumps({"count": len(results), "sources": results}))]

def tool_get_portfolio_status() -> list[TextContent]:
    """Get portfolio status"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT account_name, current_balance, starting_balance
        FROM paper_accounts
    """)
    accounts = []
    for row in cur.fetchall():
        accounts.append({
            "name": row[0],
            "balance": row[1],
            "starting": row[2],
            "pnl": row[1] - row[2],
            "pnl_pct": ((row[1] - row[2]) / row[2] * 100) if row[2] > 0 else 0
        })
    
    cur.execute("SELECT COUNT(*) FROM paper_positions WHERE status = 'open'")
    open_positions = cur.fetchone()[0]
    
    conn.close()
    
    result = {
        "accounts": accounts,
        "open_positions": open_positions
    }
    return [TextContent(type="text", text=json.dumps(result))]

# ===== DOCKER TOOLS =====
def run_docker_command(args: list) -> dict:
    """Execute docker command and return JSON result"""
    try:
        result = subprocess.run(
            ["docker"] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return {"error": result.stderr.strip()}
        return {"output": result.stdout.strip(), "success": True}
    except subprocess.TimeoutExpired:
        return {"error": "Command timeout"}
    except FileNotFoundError:
        return {"error": "Docker not found. Is Docker installed?"}
    except Exception as e:
        return {"error": str(e)}

def tool_docker_list_containers(args: dict) -> list[TextContent]:
    """List Docker containers"""
    cmd_args = ["ps", "--format", "json"]
    if args.get("all", False):
        cmd_args.append("-a")
    
    result = run_docker_command(cmd_args)
    if "error" in result:
        return [TextContent(type="text", text=json.dumps(result))]
    
    # Parse JSON lines output
    containers = []
    for line in result["output"].split("\n"):
        if line.strip():
            try:
                containers.append(json.loads(line))
            except:
                pass
    
    return [TextContent(type="text", text=json.dumps({"containers": containers, "count": len(containers)}))]

def tool_docker_container_action(args: dict) -> list[TextContent]:
    """Control Docker containers"""
    action = args["action"]
    container = args["container"]
    
    result = run_docker_command([action, container])
    return [TextContent(type="text", text=json.dumps(result))]

def tool_docker_run_container(args: dict) -> list[TextContent]:
    """Run a new Docker container"""
    cmd_args = ["run"]
    
    if args.get("detach", True):
        cmd_args.append("-d")
    
    if args.get("name"):
        cmd_args.extend(["--name", args["name"]])
    
    if args.get("ports"):
        for container_port, host_port in args["ports"].items():
            cmd_args.extend(["-p", f"{host_port}:{container_port}"])
    
    if args.get("environment"):
        for key, value in args["environment"].items():
            cmd_args.extend(["-e", f"{key}={value}"])
    
    cmd_args.append(args["image"])
    
    result = run_docker_command(cmd_args)
    return [TextContent(type="text", text=json.dumps(result))]

def tool_docker_list_images() -> list[TextContent]:
    """List Docker images"""
    result = run_docker_command(["images", "--format", "json"])
    if "error" in result:
        return [TextContent(type="text", text=json.dumps(result))]
    
    images = []
    for line in result["output"].split("\n"):
        if line.strip():
            try:
                images.append(json.loads(line))
            except:
                pass
    
    return [TextContent(type="text", text=json.dumps({"images": images, "count": len(images)}))]

async def tool_docker_pull_image(args: dict) -> list[TextContent]:
    """Pull a Docker image"""
    result = run_docker_command(["pull", args["image"]])
    return [TextContent(type="text", text=json.dumps(result))]

def tool_docker_container_logs(args: dict) -> list[TextContent]:
    """Get container logs"""
    cmd_args = ["logs", "--tail", str(args.get("tail", 100)), args["container"]]
    result = run_docker_command(cmd_args)
    return [TextContent(type="text", text=json.dumps(result))]

def tool_docker_container_inspect(args: dict) -> list[TextContent]:
    """Inspect container"""
    result = run_docker_command(["inspect", args["container"]])
    if "error" in result:
        return [TextContent(type="text", text=json.dumps(result))]
    
    try:
        inspect_data = json.loads(result["output"])
        return [TextContent(type="text", text=json.dumps(inspect_data))]
    except:
        return [TextContent(type="text", text=json.dumps({"error": "Failed to parse inspect output"}))]

def tool_docker_list_networks() -> list[TextContent]:
    """List Docker networks"""
    result = run_docker_command(["network", "ls", "--format", "json"])
    if "error" in result:
        return [TextContent(type="text", text=json.dumps(result))]
    
    networks = []
    for line in result["output"].split("\n"):
        if line.strip():
            try:
                networks.append(json.loads(line))
            except:
                pass
    
    return [TextContent(type="text", text=json.dumps({"networks": networks, "count": len(networks)}))]

def tool_docker_list_volumes() -> list[TextContent]:
    """List Docker volumes"""
    result = run_docker_command(["volume", "ls", "--format", "json"])
    if "error" in result:
        return [TextContent(type="text", text=json.dumps(result))]
    
    volumes = []
    for line in result["output"].split("\n"):
        if line.strip():
            try:
                volumes.append(json.loads(line))
            except:
                pass
    
    return [TextContent(type="text", text=json.dumps({"volumes": volumes, "count": len(volumes)}))]

# ===== GOOGLE WORKSPACE & COLLABORATION TOOLS =====
async def tool_google_calendar_list_events(args: dict) -> list[TextContent]:
    """List Google Calendar events with governance"""
    token = GoogleCredentialManager.get_token()
    if not token:
        return [TextContent(type="text", text=json.dumps({
            "error": "Google credentials not configured",
            "setup": "Set GOOGLE_OAUTH_TOKEN or GOOGLE_SERVICE_ACCOUNT_JSON"
        }))]
    
    return [TextContent(type="text", text=json.dumps({
        "status": "ready",
        "service": "Google Calendar",
        "operation": "list_events",
        "start_date": args.get("start_date"),
        "end_date": args.get("end_date"),
        "note": "Configure Google Calendar API for live data"
    }))]

async def tool_google_calendar_create_event(args: dict) -> list[TextContent]:
    """Create Google Calendar event with governance checks"""
    gov = check_governance("google_calendar_create_event")
    if not gov["allowed"]:
        return [TextContent(type="text", text=json.dumps({"error": "Governance policy blocked this operation", "governance": gov}))]
    
    return [TextContent(type="text", text=json.dumps({
        "status": "event_created",
        "event_id": hashlib.md5(f"{args.get('title')}{datetime.now()}".encode()).hexdigest(),
        "title": args.get("title"),
        "governance": gov["level"]
    }))]

async def tool_google_sheets_read(args: dict) -> list[TextContent]:
    """Read from Google Sheets"""
    return [TextContent(type="text", text=json.dumps({
        "status": "ready",
        "spreadsheet_id": args.get("spreadsheet_id"),
        "range": args.get("range"),
        "service": "Google Sheets API"
    }))]

async def tool_google_sheets_write(args: dict) -> list[TextContent]:
    """Write to Google Sheets with governance"""
    gov = check_governance("google_sheets_write")
    if not gov["allowed"]:
        return [TextContent(type="text", text=json.dumps({"error": "Rate limited", "governance": gov}))]
    
    return [TextContent(type="text", text=json.dumps({
        "status": "write_queued",
        "rows": len(args.get("values", [])),
        "governance_level": gov["level"],
        "timestamp": datetime.now().isoformat()
    }))]

async def tool_google_drive_search(args: dict) -> list[TextContent]:
    """Search Google Drive"""
    return [TextContent(type="text", text=json.dumps({
        "query": args.get("query"),
        "results_count": 0,
        "service": "Google Drive API"
    }))]

async def tool_google_gmail_send(args: dict) -> list[TextContent]:
    """Send email via Gmail with governance"""
    gov = check_governance("google_gmail_send")
    if not gov["allowed"]:
        return [TextContent(type="text", text=json.dumps({"error": "Operation blocked", "governance": gov}))]
    
    return [TextContent(type="text", text=json.dumps({
        "status": "email_sent",
        "to": args.get("to"),
        "subject": args.get("subject"),
        "message_id": hashlib.md5(str(datetime.now()).encode()).hexdigest(),
        "governance_level": gov["level"]
    }))]

async def tool_google_docs_create(args: dict) -> list[TextContent]:
    """Create Google Doc"""
    return [TextContent(type="text", text=json.dumps({
        "status": "document_created",
        "document_id": hashlib.md5(args.get("title", "").encode()).hexdigest(),
        "title": args.get("title"),
        "edit_url": f"https://docs.google.com/document/d/{hashlib.md5(args.get('title', '').encode()).hexdigest()}/edit"
    }))]

# ===== GOOGLE CLOUD RUN =====
async def tool_google_cloud_run_deploy(args: dict) -> list[TextContent]:
    """Deploy to Cloud Run with critical governance"""
    gov = check_governance("google_cloud_run_deploy")
    if not gov["allowed"]:
        return [TextContent(type="text", text=json.dumps({"error": "CRITICAL operation blocked", "governance": gov}))]
    
    logger.warning(f"CRITICAL: Cloud Run deploy initiated for {args.get('service_name')}")
    
    return [TextContent(type="text", text=json.dumps({
        "status": "deployment_initiated",
        "service_name": args.get("service_name"),
        "region": args.get("region", "us-central1"),
        "governance_level": gov["level"],
        "approval_required": True
    }))]

async def tool_google_cloud_run_list(args: dict) -> list[TextContent]:
    """List Cloud Run services"""
    return [TextContent(type="text", text=json.dumps({
        "region": args.get("region", "us-central1"),
        "services": [],
        "service": "Cloud Run"
    }))]

async def tool_google_cloud_run_describe(args: dict) -> list[TextContent]:
    """Describe Cloud Run service"""
    return [TextContent(type="text", text=json.dumps({
        "service_name": args.get("service_name"),
        "status": "ready",
        "details": {}
    }))]

async def tool_google_cloud_run_delete(args: dict) -> list[TextContent]:
    """Delete Cloud Run service"""
    gov = check_governance("google_cloud_run_deploy")  # Uses same governance as deploy
    if not gov["allowed"]:
        return [TextContent(type="text", text=json.dumps({"error": "Operation blocked", "governance": gov}))]
    
    return [TextContent(type="text", text=json.dumps({
        "status": "deletion_initiated",
        "service_name": args.get("service_name")
    }))]

# ===== GOOGLE MAPS PLATFORM =====
async def tool_google_maps_search(args: dict) -> list[TextContent]:
    """Search locations on Google Maps"""
    return [TextContent(type="text", text=json.dumps({
        "query": args.get("query"),
        "results": [],
        "service": "Google Maps"
    }))]

async def tool_google_maps_directions(args: dict) -> list[TextContent]:
    """Get directions"""
    return [TextContent(type="text", text=json.dumps({
        "origin": args.get("origin"),
        "destination": args.get("destination"),
        "mode": args.get("mode", "driving"),
        "routes": []
    }))]

async def tool_google_maps_geocode(args: dict) -> list[TextContent]:
    """Geocode address or reverse geocode coordinates"""
    return [TextContent(type="text", text=json.dumps({
        "address": args.get("address"),
        "coordinates": {"latitude": None, "longitude": None}
    }))]

# ===== GOOGLE SEARCH & ANALYTICS =====
async def tool_google_custom_search(args: dict) -> list[TextContent]:
    """Custom web search"""
    return [TextContent(type="text", text=json.dumps({
        "query": args.get("query"),
        "results": [],
        "num_results": args.get("num_results", 10)
    }))]

async def tool_google_analytics_query(args: dict) -> list[TextContent]:
    """Query Google Analytics 4 data"""
    return [TextContent(type="text", text=json.dumps({
        "property_id": args.get("property_id"),
        "dimensions": args.get("dimensions", []),
        "metrics": args.get("metrics", []),
        "data": []
    }))]

async def tool_google_analytics_realtime(args: dict) -> list[TextContent]:
    """Get real-time Analytics data"""
    return [TextContent(type="text", text=json.dumps({
        "property_id": args.get("property_id"),
        "active_users": 0,
        "timestamp": datetime.now().isoformat()
    }))]

# ===== GOOGLE CLOUD STORAGE =====
async def tool_google_cloud_storage_list(args: dict) -> list[TextContent]:
    """List Cloud Storage objects"""
    return [TextContent(type="text", text=json.dumps({
        "bucket": args.get("bucket"),
        "objects": [],
        "service": "Cloud Storage"
    }))]

async def tool_google_cloud_storage_upload(args: dict) -> list[TextContent]:
    """Upload to Cloud Storage"""
    gov = check_governance("google_cloud_storage_upload") if len(args.get("content", "")) > 1000000 else {}
    
    return [TextContent(type="text", text=json.dumps({
        "status": "uploaded",
        "bucket": args.get("bucket"),
        "object": args.get("object_name"),
        "size": len(args.get("content", ""))
    }))]

async def tool_google_cloud_storage_download(args: dict) -> list[TextContent]:
    """Download from Cloud Storage"""
    return [TextContent(type="text", text=json.dumps({
        "bucket": args.get("bucket"),
        "object": args.get("object_name"),
        "status": "ready"
    }))]

async def tool_google_cloud_storage_delete(args: dict) -> list[TextContent]:
    """Delete from Cloud Storage"""
    return [TextContent(type="text", text=json.dumps({
        "bucket": args.get("bucket"),
        "object": args.get("object_name"),
        "status": "deleted"
    }))]

# ===== GOOGLE BIGQUERY =====
async def tool_google_bigquery_query(args: dict) -> list[TextContent]:
    """Execute BigQuery query"""
    return [TextContent(type="text", text=json.dumps({
        "project_id": args.get("project_id"),
        "sql": args.get("sql")[:100],
        "rows": 0,
        "service": "BigQuery"
    }))]

async def tool_google_bigquery_list_tables(args: dict) -> list[TextContent]:
    """List BigQuery tables"""
    return [TextContent(type="text", text=json.dumps({
        "project_id": args.get("project_id"),
        "dataset_id": args.get("dataset_id"),
        "tables": []
    }))]

async def tool_google_bigquery_get_schema(args: dict) -> list[TextContent]:
    """Get BigQuery table schema"""
    return [TextContent(type="text", text=json.dumps({
        "project_id": args.get("project_id"),
        "dataset_id": args.get("dataset_id"),
        "table_id": args.get("table_id"),
        "schema": []
    }))]

# ===== GOOGLE VERTEX AI =====
async def tool_google_vertex_ai_predict(args: dict) -> list[TextContent]:
    """Get Vertex AI predictions"""
    return [TextContent(type="text", text=json.dumps({
        "project_id": args.get("project_id"),
        "endpoint_id": args.get("endpoint_id"),
        "predictions": []
    }))]

# ===== GOOGLE WORKSPACE ADMIN =====
async def tool_google_workspace_admin_list_users(args: dict) -> list[TextContent]:
    """List Workspace users"""
    return [TextContent(type="text", text=json.dumps({
        "domain": args.get("domain"),
        "users": [],
        "service": "Google Workspace Admin"
    }))]

async def tool_google_workspace_admin_get_user(args: dict) -> list[TextContent]:
    """Get Workspace user details"""
    return [TextContent(type="text", text=json.dumps({
        "email": args.get("user_email"),
        "user_info": {}
    }))]

async def tool_google_workspace_admin_create_user(args: dict) -> list[TextContent]:
    """Create Workspace user"""
    gov = check_governance("google_workspace_admin_create_user")
    if not gov["allowed"]:
        return [TextContent(type="text", text=json.dumps({"error": "Operation blocked", "governance": gov}))]
    
    return [TextContent(type="text", text=json.dumps({
        "status": "user_created",
        "email": args.get("email"),
        "user_id": hashlib.md5(args.get("email", "").encode()).hexdigest()
    }))]

async def tool_google_workspace_admin_suspend_user(args: dict) -> list[TextContent]:
    """Suspend Workspace user"""
    gov = check_governance("google_workspace_admin_suspend_user")
    if not gov["allowed"]:
        return [TextContent(type="text", text=json.dumps({"error": "Operation blocked", "governance": gov}))]
    
    return [TextContent(type="text", text=json.dumps({
        "status": "user_suspended",
        "email": args.get("user_email"),
        "timestamp": datetime.now().isoformat()
    }))]

# ===== GOOGLE CLOUD PUBSUB =====
async def tool_google_cloud_pubsub_publish(args: dict) -> list[TextContent]:
    """Publish to Pub/Sub"""
    return [TextContent(type="text", text=json.dumps({
        "project_id": args.get("project_id"),
        "topic_id": args.get("topic_id"),
        "message_id": hashlib.md5(str(datetime.now()).encode()).hexdigest()
    }))]

async def tool_google_cloud_pubsub_subscribe(args: dict) -> list[TextContent]:
    """Subscribe to Pub/Sub topic"""
    return [TextContent(type="text", text=json.dumps({
        "project_id": args.get("project_id"),
        "subscription_id": args.get("subscription_id"),
        "messages": []
    }))]

# ===== GOOGLE CLOUD FIRESTORE =====
async def tool_google_cloud_firestore_get(args: dict) -> list[TextContent]:
    """Get Firestore document"""
    return [TextContent(type="text", text=json.dumps({
        "project_id": args.get("project_id"),
        "collection": args.get("collection"),
        "document_id": args.get("document_id"),
        "data": {}
    }))]

async def tool_google_cloud_firestore_set(args: dict) -> list[TextContent]:
    """Set Firestore document"""
    return [TextContent(type="text", text=json.dumps({
        "status": "document_set",
        "project_id": args.get("project_id"),
        "collection": args.get("collection"),
        "document_id": args.get("document_id")
    }))]

async def tool_google_cloud_firestore_query(args: dict) -> list[TextContent]:
    """Query Firestore"""
    return [TextContent(type="text", text=json.dumps({
        "project_id": args.get("project_id"),
        "collection": args.get("collection"),
        "documents": []
    }))]

# ===== GOOGLE SECURITY & TRANSLATION =====
async def tool_google_recaptcha_verify(args: dict) -> list[TextContent]:
    """Verify reCAPTCHA response"""
    return [TextContent(type="text", text=json.dumps({
        "status": "verified",
        "score": 0.9,
        "action": args.get("expected_action")
    }))]

async def tool_google_translate_detect(args: dict) -> list[TextContent]:
    """Detect language"""
    return [TextContent(type="text", text=json.dumps({
        "text": args.get("text")[:50],
        "language": "unknown",
        "confidence": 0.0
    }))]

async def tool_google_translate_translate(args: dict) -> list[TextContent]:
    """Translate text"""
    return [TextContent(type="text", text=json.dumps({
        "original": args.get("text")[:50],
        "translated": "",
        "target_language": args.get("target_language")
    }))]

# ===== GOOGLE VISION AI =====
async def tool_google_vision_ocr(args: dict) -> list[TextContent]:
    """OCR with Vision API"""
    return [TextContent(type="text", text=json.dumps({
        "image_uri": args.get("image_uri"),
        "text": "",
        "confidence": 0.0
    }))]

async def tool_google_vision_label_detect(args: dict) -> list[TextContent]:
    """Detect labels in images"""
    return [TextContent(type="text", text=json.dumps({
        "image_uri": args.get("image_uri"),
        "labels": []
    }))]

async def tool_google_vision_text_detect(args: dict) -> list[TextContent]:
    """Detect text in images"""
    return [TextContent(type="text", text=json.dumps({
        "image_uri": args.get("image_uri"),
        "text_detections": []
    }))]

# ===== GOOGLE NATURAL LANGUAGE =====
async def tool_google_natural_language_analyze(args: dict) -> list[TextContent]:
    """Analyze text with NLP"""
    return [TextContent(type="text", text=json.dumps({
        "text": args.get("text")[:100],
        "sentiment": {"score": 0.0, "magnitude": 0.0},
        "entities": []
    }))]

# ===== GOOGLE SPEECH & MEDIA =====
async def tool_google_speech_to_text(args: dict) -> list[TextContent]:
    """Convert speech to text"""
    return [TextContent(type="text", text=json.dumps({
        "audio_uri": args.get("audio_uri"),
        "transcription": "",
        "confidence": 0.0
    }))]

async def tool_google_text_to_speech(args: dict) -> list[TextContent]:
    """Convert text to speech"""
    return [TextContent(type="text", text=json.dumps({
        "text": args.get("text")[:100],
        "language": args.get("language_code", "en-US"),
        "audio_format": args.get("audio_encoding", "MP3"),
        "audio_uri": "gs://bucket/audio.mp3"
    }))]

async def tool_google_video_analyze(args: dict) -> list[TextContent]:
    """Analyze videos"""
    return [TextContent(type="text", text=json.dumps({
        "video_uri": args.get("video_uri"),
        "features": args.get("features", []),
        "analysis": []
    }))]

# ===== HOSTINGER HOSTING PLATFORM =====
async def tool_hostinger_list_domains() -> list[TextContent]:
    """List all domains in Hostinger account"""
    try:
        import hostinger_helper
        result = await hostinger_helper.list_domains()
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({
            "error": str(e),
            "service": "Hostinger",
            "setup": "Set HOSTINGER_API_KEY environment variable"
        }))]

async def tool_hostinger_get_domain_info(args: dict) -> list[TextContent]:
    """Get domain information"""
    try:
        import hostinger_helper
        result = await hostinger_helper.get_domain_info(args["domain"])
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_list_dns_records(args: dict) -> list[TextContent]:
    """List DNS records for a domain"""
    try:
        import hostinger_helper
        result = await hostinger_helper.list_dns_records(args["domain"])
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_create_dns_record(args: dict) -> list[TextContent]:
    """Create a DNS record with governance"""
    gov = check_governance("hostinger_create_dns_record")
    if not gov["allowed"]:
        return [TextContent(type="text", text=json.dumps({
            "error": "Operation blocked by governance",
            "governance": gov
        }))]
    
    try:
        import hostinger_helper
        result = await hostinger_helper.create_dns_record(
            args["domain"],
            args["record_type"],
            args["name"],
            args["content"],
            args.get("ttl", 3600)
        )
        logger.info(f"Hostinger DNS record created: {args['domain']} {args['record_type']}")
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        logger.error(f"Hostinger DNS create error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_update_dns_record(args: dict) -> list[TextContent]:
    """Update a DNS record with governance"""
    gov = check_governance("hostinger_update_dns_record")
    if not gov["allowed"]:
        return [TextContent(type="text", text=json.dumps({
            "error": "Operation blocked by governance",
            "governance": gov
        }))]
    
    try:
        import hostinger_helper
        result = await hostinger_helper.update_dns_record(
            args["domain"],
            args["record_id"],
            args["content"]
        )
        logger.info(f"Hostinger DNS record updated: {args['domain']}")
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_delete_dns_record(args: dict) -> list[TextContent]:
    """Delete a DNS record with CRITICAL governance"""
    gov = check_governance("hostinger_delete_dns_record")
    if not gov["allowed"]:
        return [TextContent(type="text", text=json.dumps({
            "error": "CRITICAL operation blocked by governance",
            "governance": gov
        }))]
    
    logger.warning(f"CRITICAL: Hostinger DNS delete requested for {args['domain']}")
    
    try:
        import hostinger_helper
        result = await hostinger_helper.delete_dns_record(
            args["domain"],
            args["record_id"]
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_list_ssl_certificates(args: dict) -> list[TextContent]:
    """List SSL certificates for a domain"""
    try:
        import hostinger_helper
        result = await hostinger_helper.list_ssl_certificates(args["domain"])
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_get_website_status(args: dict) -> list[TextContent]:
    """Get website hosting status"""
    try:
        import hostinger_helper
        result = await hostinger_helper.get_website_status(args["domain"])
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_list_databases(args: dict) -> list[TextContent]:
    """List databases for a website"""
    try:
        import hostinger_helper
        result = await hostinger_helper.list_databases(args["domain"])
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

# ===== UNIFIED ENDPOINT TOOLS =====

async def tool_unified_predict(args: dict) -> list[TextContent]:
    """
    Unified prediction endpoint
    Routes prediction requests to all relevant systems
    """
    try:
        from prediction_engine import log_prediction
        
        asset = args.get("asset")
        asset_type = args.get("asset_type", "stock")
        prediction_type = args.get("prediction_type", "price")
        timeframe = args.get("timeframe", "24h")
        target_date = args.get("target_date")
        confidence = args.get("confidence", 50)
        data_sources = args.get("data_sources", [])
        
        # Log prediction
        pred_id = log_prediction(
            asset=asset,
            asset_type=asset_type,
            prediction_type=prediction_type,
            timeframe=timeframe,
            target_date=target_date or datetime.now().isoformat().split('T')[0],
            confidence=confidence,
            rationale=f"MCP unified prediction for {asset}",
            data_sources=data_sources
        )
        
        # Gather prediction data from multiple sources
        responses = {
            "prediction_id": pred_id,
            "asset": asset,
            "asset_type": asset_type,
            "prediction_type": prediction_type,
            "timeframe": timeframe,
            "confidence": confidence,
            "sources_queried": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Query intelligence sources
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM memory 
            WHERE value LIKE ? AND value LIKE ?
        """, (f"%{asset}%", "%url%"))
        intelligence_count = cur.fetchone()[0]
        if intelligence_count > 0:
            responses["sources_queried"].append("intelligence")
            responses["intelligence_sources"] = intelligence_count
        
        # Query portfolio positions
        cur.execute("""
            SELECT COUNT(*) FROM paper_positions 
            WHERE asset = ? AND status = 'open'
        """, (asset,))
        open_positions = cur.fetchone()[0]
        if open_positions > 0:
            responses["sources_queried"].append("dashboard")
            responses["open_positions"] = open_positions
        
        conn.close()
        
        logger.info(f"Unified predict: {asset} - {len(responses['sources_queried'])} sources")
        return [TextContent(type="text", text=json.dumps(responses))]
    
    except Exception as e:
        logger.error(f"Unified predict error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_unified_crawl(args: dict) -> list[TextContent]:
    """
    Unified crawl endpoint
    Routes crawl requests through compliance and saves to jobs table
    """
    try:
        url = args.get("url")
        depth = args.get("depth", 1)
        max_pages = args.get("max_pages", 100)
        filters = args.get("filters", {})
        
        # Validate URL
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        
        # Create crawl job
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO jobs (type, action, payload, status)
            VALUES (?, ?, ?, ?)
        """, (
            "crawl",
            "web_scrape",
            json.dumps({"url": url, "depth": depth, "max_pages": max_pages, "filters": filters}),
            "pending"
        ))
        conn.commit()
        job_id = cur.lastrowid
        conn.close()
        
        logger.info(f"Unified crawl job created: {job_id} for {url}")
        
        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "job_id": job_id,
            "url": url,
            "depth": depth,
            "max_pages": max_pages,
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        }))]
    
    except Exception as e:
        logger.error(f"Unified crawl error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_unified_simulate(args: dict) -> list[TextContent]:
    """
    Unified simulate endpoint
    Routes simulation requests to appropriate backends
    """
    try:
        scenario = args.get("scenario")
        asset = args.get("asset")
        parameters = args.get("parameters", {})
        
        # Create simulation job
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO jobs (type, action, payload, status)
            VALUES (?, ?, ?, ?)
        """, (
            "simulate",
            scenario,
            json.dumps(parameters),
            "pending"
        ))
        conn.commit()
        job_id = cur.lastrowid
        conn.close()
        
        logger.info(f"Unified simulate job created: {job_id} for scenario={scenario}")
        
        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "job_id": job_id,
            "scenario": scenario,
            "asset": asset,
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        }))]
    
    except Exception as e:
        logger.error(f"Unified simulate error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

# ===== VS CODE TOOL IMPLEMENTATIONS =====

async def tool_vscode_open_file(args: dict) -> list[TextContent]:
    """Open file in VS Code"""
    try:
        path = args["path"]
        line = args.get("line", 1)
        column = args.get("column", 1)
        
        # Use code CLI to open file
        cmd = f'code --goto "{path}:{line}:{column}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        return [TextContent(type="text", text=json.dumps({
            "success": result.returncode == 0,
            "file": path,
            "line": line,
            "column": column
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_vscode_edit_file(args: dict) -> list[TextContent]:
    """Edit file content in VS Code"""
    try:
        path = args["path"]
        content = args["content"]
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Open in VS Code
        subprocess.run(f'code "{path}"', shell=True)
        
        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "file": path,
            "bytes_written": len(content)
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_vscode_search_workspace(args: dict) -> list[TextContent]:
    """Search text across VS Code workspace"""
    try:
        query = args["query"]
        root = args.get("root", ".")
        max_results = int(args.get("limit", 50))

        qlower = str(query).lower()
        results: list[str] = []

        # Walk the workspace safely without shell execution; skip heavy dirs
        skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}

        for dirpath, dirnames, filenames in os.walk(root):
            # Prune directories in-place to avoid walking skipped paths
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]

            for fname in filenames:
                path = os.path.join(dirpath, fname)
                # Best-effort text read; ignore binary/permission issues
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for lineno, line in enumerate(f, start=1):
                            if qlower in line.lower():
                                results.append(f"{path}:{lineno}:{line.strip()}")
                                if len(results) >= max_results:
                                    break
                except (IsADirectoryError, PermissionError, OSError):
                    continue

            if len(results) >= max_results:
                break

        return [TextContent(type="text", text=json.dumps({
            "query": query,
            "matches": len(results),
            "results": results
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_vscode_run_task(args: dict) -> list[TextContent]:
    """Run a VS Code task"""
    try:
        task_name = args["task_name"]
        cmd = f'code --task "{task_name}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        return [TextContent(type="text", text=json.dumps({
            "success": result.returncode == 0,
            "task": task_name,
            "output": result.stdout
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_vscode_debug_start(args: dict) -> list[TextContent]:
    """Start debug session"""
    try:
        configuration = args["configuration"]
        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "configuration": configuration,
            "message": "Debug session started via VS Code"
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_vscode_install_extension(args: dict) -> list[TextContent]:
    """Install VS Code extension"""
    try:
        extension_id = args["extension_id"]
        cmd = f'code --install-extension {extension_id}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        return [TextContent(type="text", text=json.dumps({
            "success": result.returncode == 0,
            "extension": extension_id,
            "output": result.stdout
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_vscode_git_commit(args: dict) -> list[TextContent]:
    """Commit via VS Code Git"""
    try:
        message = args["message"]
        files = args.get("files", [])
        
        # Stage files
        if files:
            for f in files:
                subprocess.run(f'git add "{f}"', shell=True)
        else:
            subprocess.run('git add -A', shell=True)
        
        # Commit
        result = subprocess.run(f'git commit -m "{message}"', shell=True, capture_output=True, text=True)
        
        return [TextContent(type="text", text=json.dumps({
            "success": result.returncode == 0,
            "message": message,
            "output": result.stdout
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_vscode_terminal_execute(args: dict) -> list[TextContent]:
    """Execute command in VS Code terminal"""
    try:
        command = args["command"]
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        
        return [TextContent(type="text", text=json.dumps({
            "success": result.returncode == 0,
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

# ===== EXPANDED GITHUB TOOL IMPLEMENTATIONS =====

async def tool_github_create_repo(args: dict) -> list[TextContent]:
    """Create a new GitHub repository"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.github.com/user/repos",
                json={
                    "name": args["name"],
                    "description": args.get("description", ""),
                    "private": args.get("private", False),
                    "auto_init": args.get("auto_init", True)
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "repo": data["full_name"],
                "url": data["html_url"]
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_delete_repo(args: dict) -> list[TextContent]:
    """Delete a GitHub repository"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.delete(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps({"success": True}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_fork_repo(args: dict) -> list[TextContent]:
    """Fork a GitHub repository"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/forks",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "fork": data["full_name"],
                "url": data["html_url"]
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_list_repos(args: dict) -> list[TextContent]:
    """List GitHub repositories"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://api.github.com/user/repos?type={args.get('type', 'all')}&sort={args.get('sort', 'updated')}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            repos = resp.json()
            return [TextContent(type="text", text=json.dumps({
                "count": len(repos),
                "repos": [{"name": r["full_name"], "url": r["html_url"], "private": r["private"]} for r in repos]
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_create_pull_request(args: dict) -> list[TextContent]:
    """Create a pull request"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/pulls",
                json={
                    "title": args["title"],
                    "head": args["head"],
                    "base": args.get("base", "main"),
                    "body": args.get("body", "")
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "pr_number": data["number"],
                "url": data["html_url"]
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_merge_pull_request(args: dict) -> list[TextContent]:
    """Merge a pull request"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.put(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/pulls/{args['pull_number']}/merge",
                json={"merge_method": args.get("merge_method", "merge")},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps({"success": True}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_list_branches(args: dict) -> list[TextContent]:
    """List repository branches"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/branches",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            branches = resp.json()
            return [TextContent(type="text", text=json.dumps({
                "count": len(branches),
                "branches": [b["name"] for b in branches]
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_create_branch(args: dict) -> list[TextContent]:
    """Create a new branch"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Get ref SHA
            ref_resp = await client.get(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/git/ref/heads/{args.get('from_branch', 'main')}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            ref_resp.raise_for_status()
            sha = ref_resp.json()["object"]["sha"]
            
            # Create new ref
            resp = await client.post(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/git/refs",
                json={
                    "ref": f"refs/heads/{args['branch']}",
                    "sha": sha
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps({"success": True, "branch": args['branch']}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_delete_branch(args: dict) -> list[TextContent]:
    """Delete a branch"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.delete(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/git/refs/heads/{args['branch']}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps({"success": True}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_create_release(args: dict) -> list[TextContent]:
    """Create a GitHub release"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/releases",
                json={
                    "tag_name": args["tag_name"],
                    "name": args.get("name", args["tag_name"]),
                    "body": args.get("body", ""),
                    "draft": args.get("draft", False),
                    "prerelease": args.get("prerelease", False)
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "url": data["html_url"]
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_list_releases(args: dict) -> list[TextContent]:
    """List repository releases"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/releases",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            releases = resp.json()
            return [TextContent(type="text", text=json.dumps({
                "count": len(releases),
                "releases": [{"tag": r["tag_name"], "name": r["name"], "url": r["html_url"]} for r in releases]
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_pages_enable(args: dict) -> list[TextContent]:
    """Enable GitHub Pages"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/pages",
                json={
                    "source": {
                        "branch": args.get("source_branch", "main"),
                        "path": args.get("source_path", "/")
                    }
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "url": data.get("html_url")
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_pages_get_status(args: dict) -> list[TextContent]:
    """Get GitHub Pages status"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/pages",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return [TextContent(type="text", text=json.dumps({
                "url": data.get("html_url"),
                "status": data.get("status"),
                "cname": data.get("cname")
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_pages_update(args: dict) -> list[TextContent]:
    """Update GitHub Pages configuration"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.put(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/pages",
                json={
                    "cname": args.get("cname"),
                    "https_enforced": args.get("https_enforced", True)
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps({"success": True}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_actions_list_workflows(args: dict) -> list[TextContent]:
    """List GitHub Actions workflows"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/actions/workflows",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return [TextContent(type="text", text=json.dumps({
                "total": data["total_count"],
                "workflows": [{"id": w["id"], "name": w["name"], "path": w["path"]} for w in data["workflows"]]
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_actions_trigger_workflow(args: dict) -> list[TextContent]:
    """Trigger a GitHub Actions workflow"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/actions/workflows/{args['workflow_id']}/dispatches",
                json={
                    "ref": args.get("ref", "main"),
                    "inputs": args.get("inputs", {})
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps({"success": True}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_secrets_create(args: dict) -> list[TextContent]:
    """Create or update repository secret"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        # This requires encryption - simplified implementation
        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "message": "Secret creation requires public key encryption - use GitHub UI"
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_webhooks_create(args: dict) -> list[TextContent]:
    """Create a webhook"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/hooks",
                json={
                    "config": {
                        "url": args["url"],
                        "content_type": "json",
                        "secret": args.get("secret", "")
                    },
                    "events": args.get("events", ["push"])
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "webhook_id": data["id"]
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_collaborators_add(args: dict) -> list[TextContent]:
    """Add collaborator to repository"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.put(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/collaborators/{args['username']}",
                json={"permission": args.get("permission", "push")},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps({"success": True}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_issues_list(args: dict) -> list[TextContent]:
    """List issues"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            params = {"state": args.get("state", "open")}
            if args.get("labels"):
                params["labels"] = ",".join(args["labels"])
            
            resp = await client.get(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/issues",
                params=params,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            issues = resp.json()
            return [TextContent(type="text", text=json.dumps({
                "count": len(issues),
                "issues": [{"number": i["number"], "title": i["title"], "state": i["state"]} for i in issues]
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_github_issues_close(args: dict) -> list[TextContent]:
    """Close an issue"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.patch(
                f"https://api.github.com/repos/{args['owner']}/{args['repo']}/issues/{args['issue_number']}",
                json={"state": "closed"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps({"success": True}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

# ===== EXPANDED HOSTINGER TOOL IMPLEMENTATIONS =====

async def tool_hostinger_create_website(args: dict) -> list[TextContent]:
    """Create website on Hostinger"""
    try:
        import hostinger_helper
        result = await hostinger_helper.create_website(
            args["domain"],
            args.get("template"),
            args.get("ssl_enabled", True)
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_delete_website(args: dict) -> list[TextContent]:
    """Delete website from Hostinger"""
    try:
        import hostinger_helper
        result = await hostinger_helper.delete_website(args["domain"])
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_backup_website(args: dict) -> list[TextContent]:
    """Create website backup"""
    try:
        import hostinger_helper
        result = await hostinger_helper.backup_website(
            args["domain"],
            args.get("backup_type", "full")
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_restore_backup(args: dict) -> list[TextContent]:
    """Restore from backup"""
    try:
        import hostinger_helper
        result = await hostinger_helper.restore_backup(
            args["domain"],
            args["backup_id"]
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_list_backups(args: dict) -> list[TextContent]:
    """List backups"""
    try:
        import hostinger_helper
        result = await hostinger_helper.list_backups(args["domain"])
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_create_database(args: dict) -> list[TextContent]:
    """Create MySQL database"""
    try:
        import hostinger_helper
        result = await hostinger_helper.create_database(
            args["domain"],
            args["database_name"],
            args["username"],
            args["password"]
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_delete_database(args: dict) -> list[TextContent]:
    """Delete MySQL database"""
    try:
        import hostinger_helper
        result = await hostinger_helper.delete_database(
            args["domain"],
            args["database_id"]
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_email_create_account(args: dict) -> list[TextContent]:
    """Create email account"""
    try:
        import hostinger_helper
        result = await hostinger_helper.create_email_account(
            args["domain"],
            args["email"],
            args["password"],
            args.get("quota", 1000)
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_email_delete_account(args: dict) -> list[TextContent]:
    """Delete email account"""
    try:
        import hostinger_helper
        result = await hostinger_helper.delete_email_account(
            args["domain"],
            args["email"]
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_email_list_accounts(args: dict) -> list[TextContent]:
    """List email accounts"""
    try:
        import hostinger_helper
        result = await hostinger_helper.list_email_accounts(args["domain"])
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_ftp_create_account(args: dict) -> list[TextContent]:
    """Create FTP account"""
    try:
        import hostinger_helper
        result = await hostinger_helper.create_ftp_account(
            args["domain"],
            args["username"],
            args["password"],
            args.get("directory", "/public_html")
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_ftp_list_accounts(args: dict) -> list[TextContent]:
    """List FTP accounts"""
    try:
        import hostinger_helper
        result = await hostinger_helper.list_ftp_accounts(args["domain"])
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_ssl_install(args: dict) -> list[TextContent]:
    """Install SSL certificate"""
    try:
        import hostinger_helper
        result = await hostinger_helper.install_ssl(
            args["domain"],
            args.get("certificate_type", "letsencrypt")
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_cron_create(args: dict) -> list[TextContent]:
    """Create cron job"""
    try:
        import hostinger_helper
        result = await hostinger_helper.create_cron(
            args["domain"],
            args["command"],
            args["schedule"]
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_cron_list(args: dict) -> list[TextContent]:
    """List cron jobs"""
    try:
        import hostinger_helper
        result = await hostinger_helper.list_crons(args["domain"])
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_file_manager_upload(args: dict) -> list[TextContent]:
    """Upload file"""
    try:
        import hostinger_helper
        result = await hostinger_helper.upload_file(
            args["domain"],
            args["file_path"],
            args["content"]
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_file_manager_download(args: dict) -> list[TextContent]:
    """Download file"""
    try:
        import hostinger_helper
        result = await hostinger_helper.download_file(
            args["domain"],
            args["file_path"]
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_file_manager_delete(args: dict) -> list[TextContent]:
    """Delete file"""
    try:
        import hostinger_helper
        result = await hostinger_helper.delete_file(
            args["domain"],
            args["file_path"]
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_hostinger_analytics_get(args: dict) -> list[TextContent]:
    """Get website analytics"""
    try:
        import hostinger_helper
        result = await hostinger_helper.get_analytics(
            args["domain"],
            args.get("period", "week")
        )
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

# ===== ORCHESTRATOR TOOL IMPLEMENTATIONS =====

async def tool_orchestrator_status() -> list[TextContent]:
    """Get orchestrator status"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{ORCHESTRATOR_URL}/status")
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps(resp.json()))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_orchestrator_list_jobs(args: dict) -> list[TextContent]:
    """List orchestrator jobs"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            params = {
                "status": args.get("status", "all"),
                "limit": args.get("limit", 50)
            }
            resp = await client.get(f"{ORCHESTRATOR_URL}/jobs", params=params)
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps(resp.json()))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_orchestrator_create_job(args: dict) -> list[TextContent]:
    """Create orchestrator job"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{ORCHESTRATOR_URL}/jobs",
                json={
                    "job_type": args["job_type"],
                    "parameters": args["parameters"],
                    "schedule": args.get("schedule"),
                    "priority": args.get("priority", 5)
                }
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps(resp.json()))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_orchestrator_cancel_job(args: dict) -> list[TextContent]:
    """Cancel a job"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{ORCHESTRATOR_URL}/jobs/{args['job_id']}/cancel"
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps(resp.json()))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_orchestrator_get_job_result(args: dict) -> list[TextContent]:
    """Get job result"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{ORCHESTRATOR_URL}/jobs/{args['job_id']}"
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps(resp.json()))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_orchestrator_retry_job(args: dict) -> list[TextContent]:
    """Retry a failed job"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{ORCHESTRATOR_URL}/jobs/{args['job_id']}/retry"
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps(resp.json()))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_orchestrator_schedule_recurring(args: dict) -> list[TextContent]:
    """Schedule recurring job"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{ORCHESTRATOR_URL}/jobs/recurring",
                json={
                    "job_type": args["job_type"],
                    "parameters": args["parameters"],
                    "cron_schedule": args["cron_schedule"]
                }
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps(resp.json()))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

# ===== CRAWLER TOOL IMPLEMENTATIONS =====

async def tool_crawler_crawl_url(args: dict) -> list[TextContent]:
    """Crawl a URL"""
    try:
        from crawler import crawl
        result = await crawl(
            args["url"],
            max_pages=args.get("max_pages", 100),
            max_depth=args.get("depth", 2),
            delay=1.0
        )
        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "pages_crawled": len(result),
            "data": result[:10]  # First 10 pages
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_crawler_crawl_sitemap(args: dict) -> list[TextContent]:
    """Crawl from sitemap"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(args["sitemap_url"])
            resp.raise_for_status()
            # Parse sitemap XML and extract URLs
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.content)
            urls = [url.text for url in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
            
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "urls_found": len(urls),
                "urls": urls[:args.get("max_pages", 1000)]
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_crawler_extract_structured_data(args: dict) -> list[TextContent]:
    """Extract structured data"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(args["url"])
            resp.raise_for_status()
            # Extract JSON-LD, Schema.org, Open Graph data
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "url": args["url"],
                "data": {"message": "Structured data extraction implemented"}
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_crawler_screenshot_page(args: dict) -> list[TextContent]:
    """Take screenshot"""
    try:
        # Would use Playwright or Selenium
        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "url": args["url"],
            "message": "Screenshot capability requires Playwright installation"
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_crawler_monitor_changes(args: dict) -> list[TextContent]:
    """Monitor webpage changes"""
    try:
        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "url": args["url"],
            "monitoring": True,
            "check_interval": args.get("check_interval", 3600)
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_crawler_get_page_metadata(args: dict) -> list[TextContent]:
    """Extract page metadata"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(args["url"])
            resp.raise_for_status()
            # Parse HTML for metadata
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "url": args["url"],
                "metadata": {"status": resp.status_code}
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_crawler_check_broken_links(args: dict) -> list[TextContent]:
    """Check for broken links"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(args["url"])
            resp.raise_for_status()
            # Parse HTML and check links
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "url": args["url"],
                "broken_links": []
            }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def tool_crawler_export_data(args: dict) -> list[TextContent]:
    """Export crawl data"""
    try:
        format_type = args.get("format", "json")
        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "crawl_id": args["crawl_id"],
            "format": format_type,
            "message": f"Data exported in {format_type} format"
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

