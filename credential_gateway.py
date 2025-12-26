"""
Credential Gateway - Safe read-only credential access with governance
Exposes credentials via API with:
- Secret Manager as source of truth
- Read-only access (no writes via API)
- Governance and audit logging
- Token-based access control
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import logging
import hashlib
from datetime import datetime
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credentials", tags=["credentials"])

# Credential types registry
CREDENTIAL_REGISTRY = {
    "github_app": {
        "config": "projects/896380409704/secrets/github-app-config",
        "private_key": "projects/896380409704/secrets/github-app-private-key",
    },
    "firebase": {
        "config": "projects/896380409704/secrets/firebase-config",
        "gemini_key": "projects/896380409704/secrets/gemini-api-key",
    },
    "openai": {
        "api_key": "projects/896380409704/secrets/openai-api-key",
    },
    "hostinger": {
        "api_key": "projects/896380409704/secrets/hostinger-api-key",
    },
    "gcp": {
        "service_account": "projects/896380409704/secrets/workspace-sa-json",
    },
}

def get_secret_client():
    """Get Secret Manager client"""
    try:
        return secretmanager.SecretManagerServiceClient()
    except Exception as e:
        logger.error(f"Failed to create Secret Manager client: {e}")
        return None

def validate_credential_token(x_credential_token: Optional[str] = Header(None)):
    """Validate credential access token"""
    expected = os.environ.get("CREDENTIAL_GATEWAY_TOKEN", os.environ.get("MCP_API_KEY"))
    if not expected:
        # In dev mode, allow without token
        if os.environ.get("DEV_MODE", "false").lower() == "true":
            return True
        raise HTTPException(status_code=500, detail="Credential gateway not configured")
    
    if not x_credential_token or x_credential_token != expected:
        raise HTTPException(status_code=401, detail="Invalid credential token")
    return True

def audit_log_credential_access(credential_type: str, secret_name: str, requester: str = "unknown"):
    """Log credential access to Firestore for audit trail"""
    try:
        from google.cloud import firestore
        project = os.environ.get("FIRESTORE_PROJECT", "infinity-x-one-systems")
        client = firestore.Client(project=project)
        
        doc = {
            "type": "credential_access",
            "credential_type": credential_type,
            "secret_name": secret_name,
            "requester": requester,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "access_hash": hashlib.sha256(f"{credential_type}{secret_name}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16],
        }
        
        client.collection("mcp_memory").document(f"audit_{doc['access_hash']}").set(doc)
        logger.info(f"Credential access logged: {credential_type}/{secret_name}")
    except Exception as e:
        logger.error(f"Failed to log credential access: {e}")

@router.get("/health")
async def credential_health():
    """Health check for credential gateway"""
    client = get_secret_client()
    return JSONResponse(content={
        "status": "healthy",
        "secret_manager_available": client is not None,
        "credential_types": list(CREDENTIAL_REGISTRY.keys())
    })

@router.get("/list")
async def list_credentials(
    _: bool = Depends(validate_credential_token)
):
    """List available credential types (no secrets exposed)"""
    return JSONResponse(content={
        "success": True,
        "credential_types": list(CREDENTIAL_REGISTRY.keys()),
        "registry": {k: list(v.keys()) for k, v in CREDENTIAL_REGISTRY.items()}
    })

class CredentialRequest(BaseModel):
    credential_type: str
    key: Optional[str] = None  # Specific key within credential type
    masked: bool = False  # Return masked version for display

@router.post("/get")
async def get_credential(
    req: CredentialRequest,
    x_credential_token: Optional[str] = Header(None),
    x_requester: Optional[str] = Header("api_caller"),
    _: bool = Depends(validate_credential_token)
):
    """Get credential value from Secret Manager"""
    
    if req.credential_type not in CREDENTIAL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Credential type not found: {req.credential_type}")
    
    cred_config = CREDENTIAL_REGISTRY[req.credential_type]
    
    # Determine which secret to fetch
    if req.key:
        if req.key not in cred_config:
            raise HTTPException(status_code=404, detail=f"Key not found: {req.key}")
        secret_name = cred_config[req.key]
    else:
        # Return all keys for this credential type
        secret_name = None
    
    client = get_secret_client()
    if not client:
        raise HTTPException(status_code=503, detail="Secret Manager unavailable")
    
    try:
        if secret_name:
            # Fetch single secret
            name = f"{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            value = response.payload.data.decode('UTF-8')
            
            # Audit log
            audit_log_credential_access(req.credential_type, secret_name, x_requester)
            
            # Mask if requested
            if req.masked and len(value) > 8:
                value = value[:4] + "..." + value[-4:]
            
            return JSONResponse(content={
                "success": True,
                "credential_type": req.credential_type,
                "key": req.key,
                "value": value,
                "masked": req.masked
            })
        else:
            # Fetch all secrets for this credential type
            results = {}
            for key, secret_path in cred_config.items():
                try:
                    name = f"{secret_path}/versions/latest"
                    response = client.access_secret_version(request={"name": name})
                    value = response.payload.data.decode('UTF-8')
                    
                    audit_log_credential_access(req.credential_type, secret_path, x_requester)
                    
                    if req.masked and len(value) > 8:
                        value = value[:4] + "..." + value[-4:]
                    
                    results[key] = value
                except Exception as e:
                    logger.error(f"Failed to fetch {key}: {e}")
                    results[key] = None
            
            return JSONResponse(content={
                "success": True,
                "credential_type": req.credential_type,
                "values": results,
                "masked": req.masked
            })
    
    except Exception as e:
        logger.error(f"Failed to fetch credential: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inject")
async def inject_credentials(
    req: CredentialRequest,
    _: bool = Depends(validate_credential_token)
):
    """Inject credentials into environment (for serverless functions)"""
    
    if req.credential_type not in CREDENTIAL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Credential type not found: {req.credential_type}")
    
    client = get_secret_client()
    if not client:
        raise HTTPException(status_code=503, detail="Secret Manager unavailable")
    
    cred_config = CREDENTIAL_REGISTRY[req.credential_type]
    injected = {}
    
    try:
        for key, secret_path in cred_config.items():
            try:
                name = f"{secret_path}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                value = response.payload.data.decode('UTF-8')
                
                # Map to environment variable name
                env_var_name = f"{req.credential_type.upper()}_{key.upper()}"
                os.environ[env_var_name] = value
                injected[env_var_name] = "injected"
                
                audit_log_credential_access(req.credential_type, secret_path, "env_inject")
            except Exception as e:
                logger.error(f"Failed to inject {key}: {e}")
                injected[key] = f"failed: {str(e)}"
        
        return JSONResponse(content={
            "success": True,
            "credential_type": req.credential_type,
            "injected": injected
        })
    
    except Exception as e:
        logger.error(f"Failed to inject credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit")
async def get_credential_audit_log(
    limit: int = 50,
    _: bool = Depends(validate_credential_token)
):
    """Get credential access audit log"""
    try:
        from google.cloud import firestore
        project = os.environ.get("FIRESTORE_PROJECT", "infinity-x-one-systems")
        client = firestore.Client(project=project)
        
        docs = client.collection("mcp_memory").where("type", "==", "credential_access").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        audit_entries = []
        for doc in docs:
            data = doc.to_dict()
            # Remove sensitive info from audit log display
            data.pop("access_hash", None)
            audit_entries.append(data)
        
        return JSONResponse(content={
            "success": True,
            "count": len(audit_entries),
            "audit_log": audit_entries
        })
    
    except Exception as e:
        logger.error(f"Failed to get audit log: {e}")
        raise HTTPException(status_code=500, detail=str(e))
