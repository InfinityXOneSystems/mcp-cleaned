import asyncio
import ipaddress
import os
import socket
import time
from typing import Iterable, Set
from urllib.parse import urlparse
from urllib import robotparser

import httpx

SCRAPER_ALLOWED_HOSTS: Set[str] = {
    h.strip().lower() for h in os.getenv("SCRAPER_ALLOWED_HOSTS", "").split(",") if h.strip()
}
SCRAPER_USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT", "InfinityXOSBot/1.0 (+contact: security@infinity-xos.local)"
)
SCRAPER_MIN_DELAY = float(os.getenv("SCRAPER_MIN_DELAY", "1.0"))


def _ensure_allowlist() -> None:
    if not SCRAPER_ALLOWED_HOSTS:
        raise ValueError("SCRAPER_ALLOWED_HOSTS must be set to a comma-separated host allowlist")


def _host_in_allowlist(host: str) -> bool:
    host = host.lower()
    for allowed in SCRAPER_ALLOWED_HOSTS:
        if host == allowed or host.endswith("." + allowed):
            return True
    return False


def _resolve_ips(host: str) -> Set[str]:
    infos = socket.getaddrinfo(host, None)
    return {info[4][0] for info in infos}


def _assert_public_host(host: str) -> None:
    try:
        ips = _resolve_ips(host)
    except socket.gaierror as exc:
        raise ValueError(f"DNS lookup failed for host {host}: {exc}") from exc
    for ip in ips:
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local or addr.is_multicast:
            raise ValueError(f"Host {host} resolves to a non-public IP ({ip})")


def validate_url(url: str) -> str:
    """Validate URL scheme, allowlist, and public IP constraints; returns hostname."""
    _ensure_allowlist()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http/https URLs are allowed")
    host = parsed.hostname
    if not host:
        raise ValueError("URL is missing a hostname")
    if not _host_in_allowlist(host):
        raise ValueError(f"Host {host} is not in the allowlist")
    _assert_public_host(host)
    return host


def filter_allowed_domains(domains: Iterable[str] | None) -> list[str]:
    """Return the subset of domains that are in the configured allowlist."""
    if not domains:
        return []
    allowed = []
    for domain in domains:
        host = domain.strip().lower()
        if _host_in_allowlist(host):
            allowed.append(host)
    # preserve order, drop duplicates
    seen = set()
    result = []
    for host in allowed:
        if host not in seen:
            seen.add(host)
            result.append(host)
    return result


class RateLimiter:
    def __init__(self, min_delay: float = SCRAPER_MIN_DELAY):
        self.min_delay = min_delay
        self._last: dict[str, float] = {}

    async def wait(self, host: str) -> None:
        now = time.time()
        last = self._last.get(host, 0)
        wait = self.min_delay - (now - last)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last[host] = time.time()


async def robots_can_fetch_httpx(url: str, user_agent: str = SCRAPER_USER_AGENT, timeout: float = 5.0) -> bool:
    """Return False on any failure (default-deny) or robots disallow."""
    _ensure_allowlist()
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    headers = {"User-Agent": user_agent}
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            resp = await client.get(robots_url)
            if resp.status_code >= 400:
                return False
            rp.parse(resp.text.splitlines())
    except Exception:
        return False
    return rp.can_fetch(user_agent, url)


async def robots_can_fetch_aiohttp(session, url: str, user_agent: str = SCRAPER_USER_AGENT, timeout: float = 5.0) -> bool:
    """Same as robots_can_fetch_httpx but reuses an aiohttp session; default-deny on error."""
    _ensure_allowlist()
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        async with session.get(robots_url, headers={"User-Agent": user_agent}, timeout=timeout) as resp:
            if resp.status >= 400:
                return False
            text = await resp.text()
            rp.parse(text.splitlines())
    except Exception:
        return False
    return rp.can_fetch(user_agent, url)
