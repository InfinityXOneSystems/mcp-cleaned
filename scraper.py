from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from safety import RateLimiter, SCRAPER_USER_AGENT, robots_can_fetch_httpx, validate_url

_rate_limiter = RateLimiter()


async def fetch_html(url: str, timeout: int = 20) -> str:
    host = validate_url(url)
    allowed = await robots_can_fetch_httpx(url, user_agent=SCRAPER_USER_AGENT)
    if not allowed:
        raise PermissionError("Blocked by robots.txt")
    await _rate_limiter.wait(host)
    async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": SCRAPER_USER_AGENT}) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    # Remove scripts and styles
    for s in soup(["script", "style", "noscript"]):
        s.extract()
    # Extract visible text
    texts = soup.stripped_strings
    return "\n".join(texts)


async def scrape(url: str, timeout: int = 20) -> dict:
    html = await fetch_html(url, timeout=timeout)
    text = extract_text(html)
    return {"url": url, "text": text}
