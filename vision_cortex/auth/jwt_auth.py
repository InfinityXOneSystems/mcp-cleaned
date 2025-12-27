"""Simple JWT auth helper using HMAC SHA256 and PyJWT.

Set `JWT_SECRET` and optionally `JWT_ALGORITHM` (default HS256) in env.
"""
from __future__ import annotations

import os
import logging
from typing import Optional, Dict, Any

import jwt

logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")


def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception as e:
        logger.debug("JWT verification failed: %s", e)
        return None
