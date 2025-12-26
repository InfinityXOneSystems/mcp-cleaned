"""
Security manager for API keys, encryption, and secure access
"""
import os
import json
import hashlib
import secrets
from typing import Dict, Optional, Any
from functools import lru_cache
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class SecurityManager:
    """Centralized security management"""

    def __init__(self, env_file: Optional[str] = None):
        """Initialize security manager with .env file"""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        self._secrets = {}
        self._load_secrets()

    @lru_cache(maxsize=1)
    def _load_secrets(self) -> None:
        """Load secrets from environment variables"""
        # API Keys
        self._secrets = {
            # OpenAI
            "openai_api_key": self._get_secret("OPENAI_API_KEY"),
            # Google Cloud
            "google_credentials": self._get_secret("GOOGLE_APPLICATION_CREDENTIALS"),
            "firestore_project": self._get_secret("FIRESTORE_PROJECT"),
            # Redis
            "redis_url": self._get_secret("REDIS_URL", "redis://localhost:6379/0"),
            # Celery
            "celery_broker": self._get_secret("CELERY_BROKER_URL", "redis://localhost:6379/1"),
            "celery_backend": self._get_secret("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
            # MCP
            "mcp_api_key": self._get_secret("MCP_API_KEY"),
            # Security
            "jwt_secret": self._get_secret("JWT_SECRET_KEY", self._generate_jwt_secret()),
            "safe_mode": self._get_secret("SAFE_MODE", "true").lower() == "true",
        }

    @staticmethod
    def _get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
        """Safely retrieve secret from environment"""
        value = os.environ.get(key, default)
        if value and key.endswith("_KEY"):
            logger.debug(f"✓ Loaded secret: {key[:20]}...")
        return value

    @staticmethod
    def _generate_jwt_secret() -> str:
        """Generate secure JWT secret if not provided"""
        return secrets.token_urlsafe(32)

    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret by key"""
        return self._secrets.get(key)

    def get_openai_key(self) -> str:
        """Get OpenAI API key"""
        key = self._secrets.get("openai_api_key")
        if not key:
            raise ValueError("OPENAI_API_KEY not configured")
        return key

    def get_redis_url(self) -> str:
        """Get Redis URL"""
        return self._secrets.get("redis_url", "redis://localhost:6379/0")

    def get_celery_broker(self) -> str:
        """Get Celery broker URL"""
        return self._secrets.get("celery_broker", "redis://localhost:6379/1")

    def get_celery_backend(self) -> str:
        """Get Celery result backend URL"""
        return self._secrets.get("celery_backend", "redis://localhost:6379/2")

    def get_jwt_secret(self) -> str:
        """Get JWT secret"""
        return self._secrets.get("jwt_secret", "")

    def is_safe_mode(self) -> bool:
        """Check if safe mode is enabled"""
        return self._secrets.get("safe_mode", True)

    def validate_api_key(self, provided_key: str, expected_env_var: str = "MCP_API_KEY") -> bool:
        """Validate API key matches environment"""
        expected = os.environ.get(expected_env_var)
        if not expected:
            logger.warning(f"{expected_env_var} not set")
            return False
        return self._timing_safe_compare(provided_key, expected)

    @staticmethod
    def _timing_safe_compare(a: str, b: str) -> bool:
        """Timing-safe string comparison to prevent timing attacks"""
        if len(a) != len(b):
            return False
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        return result == 0

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    def create_secure_env(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Create a secure environment dict for subprocess"""
        env = os.environ.copy()
        
        # Add known secrets
        if self.get_secret("openai_api_key"):
            env["OPENAI_API_KEY"] = self.get_secret("openai_api_key")
        
        # Apply overrides
        if overrides:
            env.update(overrides)
        
        return env

    def validate_domain(self, url: str, allowed_domains: Optional[list] = None) -> bool:
        """Validate domain against allowlist for browser automation"""
        if allowed_domains is None:
            allowed_domains = ["localhost", "127.0.0.1", "example.com"]
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.split(":")[0]
            return domain in allowed_domains
        except Exception as e:
            logger.error(f"Domain validation error: {e}")
            return False

    def get_firestore_credentials(self) -> Optional[Dict[str, Any]]:
        """Get Firestore credentials from file"""
        cred_path = self._secrets.get("google_credentials")
        if not cred_path:
            return None
        
        try:
            if os.path.exists(cred_path):
                with open(cred_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Firestore credentials: {e}")
        
        return None


# Global security manager instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager(env_file: Optional[str] = None) -> SecurityManager:
    """Get or create global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager(env_file)
    return _security_manager
