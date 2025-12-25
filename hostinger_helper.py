"""
Hostinger API Integration Helper
Manages domains, hosting, DNS, and SSL via Hostinger API
"""
import os
import httpx
from typing import Dict, List, Optional, Any

HOSTINGER_API_BASE = "https://api.hostinger.com/v1"


def get_api_key() -> Optional[str]:
    """Get Hostinger API key from environment"""
    return os.getenv('HOSTINGER_API_KEY')


def get_headers() -> Dict[str, str]:
    """Build Hostinger API headers"""
    api_key = get_api_key()
    if not api_key:
        raise ValueError("HOSTINGER_API_KEY not set")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }


async def list_domains() -> Dict[str, Any]:
    """List all domains in Hostinger account"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{HOSTINGER_API_BASE}/domains",
                headers=get_headers()
            )
            resp.raise_for_status()
            return {"status": "success", "domains": resp.json()}
    except Exception as e:
        return {"error": str(e)}


async def get_domain_info(domain: str) -> Dict[str, Any]:
    """Get information about a specific domain"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{HOSTINGER_API_BASE}/domains/{domain}",
                headers=get_headers()
            )
            resp.raise_for_status()
            return {"status": "success", "domain": resp.json()}
    except Exception as e:
        return {"error": str(e)}


async def list_dns_records(domain: str) -> Dict[str, Any]:
    """List DNS records for a domain"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{HOSTINGER_API_BASE}/domains/{domain}/dns",
                headers=get_headers()
            )
            resp.raise_for_status()
            return {"status": "success", "records": resp.json()}
    except Exception as e:
        return {"error": str(e)}


async def create_dns_record(domain: str, record_type: str, name: str, content: str, ttl: int = 3600) -> Dict[str, Any]:
    """Create a DNS record"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{HOSTINGER_API_BASE}/domains/{domain}/dns",
                headers=get_headers(),
                json={
                    "type": record_type,
                    "name": name,
                    "content": content,
                    "ttl": ttl
                }
            )
            resp.raise_for_status()
            return {"status": "success", "record": resp.json()}
    except Exception as e:
        return {"error": str(e)}


async def update_dns_record(domain: str, record_id: str, content: str) -> Dict[str, Any]:
    """Update a DNS record"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.put(
                f"{HOSTINGER_API_BASE}/domains/{domain}/dns/{record_id}",
                headers=get_headers(),
                json={"content": content}
            )
            resp.raise_for_status()
            return {"status": "success", "record": resp.json()}
    except Exception as e:
        return {"error": str(e)}


async def delete_dns_record(domain: str, record_id: str) -> Dict[str, Any]:
    """Delete a DNS record"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.delete(
                f"{HOSTINGER_API_BASE}/domains/{domain}/dns/{record_id}",
                headers=get_headers()
            )
            resp.raise_for_status()
            return {"status": "success", "deleted": record_id}
    except Exception as e:
        return {"error": str(e)}


async def list_ssl_certificates(domain: str) -> Dict[str, Any]:
    """List SSL certificates for a domain"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{HOSTINGER_API_BASE}/domains/{domain}/ssl",
                headers=get_headers()
            )
            resp.raise_for_status()
            return {"status": "success", "certificates": resp.json()}
    except Exception as e:
        return {"error": str(e)}


async def get_website_status(domain: str) -> Dict[str, Any]:
    """Get website hosting status"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{HOSTINGER_API_BASE}/websites/{domain}",
                headers=get_headers()
            )
            resp.raise_for_status()
            return {"status": "success", "website": resp.json()}
    except Exception as e:
        return {"error": str(e)}


async def list_databases(domain: str) -> Dict[str, Any]:
    """List databases for a website"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{HOSTINGER_API_BASE}/websites/{domain}/databases",
                headers=get_headers()
            )
            resp.raise_for_status()
            return {"status": "success", "databases": resp.json()}
    except Exception as e:
        return {"error": str(e)}


def test_connection() -> Dict[str, Any]:
    """Test Hostinger API connection"""
    api_key = get_api_key()
    if not api_key:
        return {
            "status": "not_configured",
            "message": "HOSTINGER_API_KEY not set"
        }
    return {
        "status": "configured",
        "message": "Hostinger API key present",
        "key_prefix": api_key[:8] + "..." if len(api_key) > 8 else "***"
    }


if __name__ == "__main__":
    import asyncio
    result = test_connection()
    print(result)
    if result["status"] == "configured":
        print("\nTesting domain list...")
        domains = asyncio.run(list_domains())
        print(domains)
