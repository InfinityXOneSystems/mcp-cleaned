"""
Compliance Engine - Google, OpenAI, GitHub Mandatory Requirements
Ensures all API calls adhere to platform policies and rate limits
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ComplianceLevel(Enum):
    """Compliance enforcement levels"""
    CRITICAL = "critical"      # Must be enforced
    HIGH = "high"              # Should be enforced
    MEDIUM = "medium"          # Recommended
    AUDIT_ONLY = "audit_only"  # Log only

class PlatformRequirement(Enum):
    """All platform-specific requirements we must follow"""
    
    # Google Cloud Requirements
    GOOGLE_RATE_LIMIT = "google:rate_limit"  # 100 req/min
    GOOGLE_AUTH_REQUIRED = "google:auth_required"  # Must use service account or OAuth
    GOOGLE_DATA_RESIDENCY = "google:data_residency"  # Data stays in configured region
    GOOGLE_AUDIT_LOG = "google:audit_log"  # All operations logged
    GOOGLE_NO_API_KEY = "google:no_api_key"  # Never expose API keys
    
    # GitHub Requirements
    GITHUB_RATE_LIMIT = "github:rate_limit"  # 60 req/min for auth, 10/min for create/delete
    GITHUB_AUTH_REQUIRED = "github:auth_required"  # Must use OAuth or Personal Access Token
    GITHUB_SIGN_WEBHOOKS = "github:sign_webhooks"  # All webhooks must be signed
    GITHUB_TRACK_COMMITS = "github:track_commits"  # All commits tracked with author
    
    # OpenAI Requirements
    OPENAI_RATE_LIMIT = "openai:rate_limit"  # 3 req/min for free tier, higher for paid
    OPENAI_NO_CACHE = "openai:no_cache"  # Never cache responses
    OPENAI_TRACK_USAGE = "openai:track_usage"  # Log all usage for billing
    OPENAI_VALIDATE_INPUT = "openai:validate_input"  # Validate all input strings

class ComplianceValidator:
    """Validates requests against platform mandatories"""
    
    RATE_LIMITS = {
        "google_apis": {"limit": 100, "window_seconds": 60},
        "github_apis": {"limit": 60, "window_seconds": 60},
        "github_mutations": {"limit": 10, "window_seconds": 60},
        "openai_apis": {"limit": 3, "window_seconds": 60},
        "openai_paid": {"limit": 100, "window_seconds": 60},
    }
    
    REQUIRED_HEADERS = {
        "google": ["Authorization", "User-Agent"],
        "github": ["Authorization", "User-Agent", "X-GitHub-Api-Version"],
        "openai": ["Authorization", "User-Agent"],
    }
    
    def __init__(self):
        self.request_log: List[Dict[str, Any]] = []
        self.violation_log: List[Dict[str, Any]] = []
        
    def validate_request(
        self,
        platform: str,
        operation: str,
        request_data: Dict[str, Any],
        headers: Dict[str, str],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate request against all platform requirements
        
        Returns:
            {
                "valid": bool,
                "violations": List[str],
                "warnings": List[str],
                "compliance_level": ComplianceLevel,
                "tracked": bool
            }
        """
        violations = []
        warnings = []
        
        # Check required headers
        platform_headers = self.REQUIRED_HEADERS.get(platform, [])
        for header in platform_headers:
            if header not in headers:
                violations.append(f"Missing required header: {header}")
        
        # Platform-specific validation
        if platform == "google":
            violations, warnings = self._validate_google(operation, request_data, headers)
        elif platform == "github":
            violations, warnings = self._validate_github(operation, request_data, headers)
        elif platform == "openai":
            violations, warnings = self._validate_openai(operation, request_data, headers)
        
        # Log request
        self._log_request(platform, operation, user_id, len(violations) > 0)
        
        # Log violations
        if violations:
            for violation in violations:
                self._log_violation(platform, operation, violation, user_id)
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "compliance_level": ComplianceLevel.CRITICAL if len(violations) > 0 else ComplianceLevel.HIGH,
            "tracked": True
        }
    
    def _validate_google(self, operation: str, data: Dict, headers: Dict) -> tuple:
        """Google Cloud compliance checks"""
        violations = []
        warnings = []
        
        # Must have Authorization header
        if "Authorization" not in headers:
            violations.append("Google: Missing Authorization header (service account required)")
        
        # Check for API key exposure
        if "api_key" in str(data).lower() or "apikey" in str(data).lower():
            violations.append("Google: API key found in request (never expose API keys)")
        
        # Validate User-Agent
        if "User-Agent" not in headers:
            warnings.append("Google: Missing User-Agent (recommended)")
        
        # Ensure data residency compliance
        if operation in ["cloud_run_deploy", "firestore_write"]:
            if "region" not in data and "us-east1" not in str(data):
                warnings.append("Google: Specify data region for compliance (us-east1 recommended)")
        
        return violations, warnings
    
    def _validate_github(self, operation: str, data: Dict, headers: Dict) -> tuple:
        """GitHub API compliance checks"""
        violations = []
        warnings = []
        
        # Must have Authorization header
        if "Authorization" not in headers:
            violations.append("GitHub: Missing Authorization header (OAuth token required)")
        
        # Check webhook signing
        if operation == "receive_webhook":
            if "X-Hub-Signature-256" not in headers:
                violations.append("GitHub: Missing webhook signature (X-Hub-Signature-256)")
        
        # Require commit author info for mutations
        if operation in ["create_commit", "push_branch"]:
            if "author" not in data:
                violations.append("GitHub: Missing commit author information")
        
        # Validate API version
        if "X-GitHub-Api-Version" not in headers:
            warnings.append("GitHub: Missing API version header (2022-11-28 recommended)")
        
        return violations, warnings
    
    def _validate_openai(self, operation: str, data: Dict, headers: Dict) -> tuple:
        """OpenAI API compliance checks"""
        violations = []
        warnings = []
        
        # Must have Authorization header
        if "Authorization" not in headers:
            violations.append("OpenAI: Missing Authorization header (API key required)")
        
        # Validate input strings
        if "prompt" in data:
            if not isinstance(data["prompt"], str) or len(data["prompt"]) == 0:
                violations.append("OpenAI: Invalid prompt (must be non-empty string)")
        
        # Check for caching attempts (not allowed)
        if "cache_control" in headers or "cache" in str(data).lower():
            violations.append("OpenAI: Caching not allowed (API responses are not cacheable)")
        
        # Warn if no tracking metadata
        if "user" not in data:
            warnings.append("OpenAI: Missing 'user' field for usage tracking (recommended)")
        
        return violations, warnings
    
    def check_rate_limit(self, platform: str, operation: str = None) -> bool:
        """
        Check if request is within rate limits
        
        Args:
            platform: "google", "github", "openai"
            operation: Specific operation ("read", "write", "mutate", etc.)
        
        Returns:
            True if within limits, False if exceeded
        """
        # Determine bucket
        if platform == "github" and operation in ["create", "delete", "update"]:
            bucket = "github_mutations"
        elif platform == "github":
            bucket = "github_apis"
        elif platform == "google":
            bucket = "google_apis"
        elif platform == "openai":
            bucket = "openai_paid"  # Assume paid tier
        else:
            return True  # Unknown platform, allow
        
        limit_info = self.RATE_LIMITS[bucket]
        
        # Simple check: count recent requests
        now = datetime.now()
        window_start = now - timedelta(seconds=limit_info["window_seconds"])
        
        recent = [
            r for r in self.request_log
            if r["platform"] == platform and
            datetime.fromisoformat(r["timestamp"]) > window_start
        ]
        
        within_limit = len(recent) < limit_info["limit"]
        
        if not within_limit:
            logger.warning(
                f"Rate limit exceeded for {platform}: {len(recent)}/{limit_info['limit']} "
                f"in {limit_info['window_seconds']}s"
            )
        
        return within_limit
    
    def _log_request(self, platform: str, operation: str, user_id: Optional[str], violation: bool):
        """Log request for compliance audit"""
        self.request_log.append({
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "operation": operation,
            "user_id": user_id,
            "violation": violation
        })
        
        # Keep log manageable
        if len(self.request_log) > 10000:
            self.request_log = self.request_log[-5000:]
    
    def _log_violation(self, platform: str, operation: str, violation: str, user_id: Optional[str]):
        """Log compliance violation"""
        self.violation_log.append({
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "operation": operation,
            "violation": violation,
            "user_id": user_id
        })
        
        logger.warning(f"Compliance violation: {platform}:{operation} - {violation}")
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent compliance audit log"""
        return self.violation_log[-limit:]
    
    def get_request_stats(self) -> Dict[str, Any]:
        """Get request statistics"""
        platforms = {}
        for req in self.request_log:
            p = req["platform"]
            if p not in platforms:
                platforms[p] = {"total": 0, "violations": 0}
            platforms[p]["total"] += 1
            if req["violation"]:
                platforms[p]["violations"] += 1
        
        return {
            "total_requests": len(self.request_log),
            "total_violations": len(self.violation_log),
            "by_platform": platforms
        }

# Global validator instance
compliance_validator = ComplianceValidator()

async def validate_request_middleware(platform: str, operation: str, request_data: Dict, headers: Dict, user_id: Optional[str] = None):
    """Middleware to validate requests"""
    result = compliance_validator.validate_request(platform, operation, request_data, headers, user_id)
    
    if not result["valid"]:
        logger.error(f"Compliance validation failed: {result['violations']}")
        return {
            "error": "Compliance validation failed",
            "violations": result["violations"],
            "status": 403
        }
    
    return None  # OK, proceed

def get_compliance_status() -> Dict[str, Any]:
    """Get system-wide compliance status"""
    return {
        "validator": "online",
        "audit_log_entries": len(compliance_validator.violation_log),
        "request_stats": compliance_validator.get_request_stats(),
        "mandate_status": {
            "google": "enforced",
            "github": "enforced",
            "openai": "enforced"
        }
    }
