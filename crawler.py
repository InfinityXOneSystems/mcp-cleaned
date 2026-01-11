from typing import List

from async_crawler import crawl_url
from safety import filter_allowed_domains, validate_url


async def crawl(
    start_url: str,
    max_pages: int = 50,
    max_depth: int = 2,
    allowed_domains: List[str] | None = None,
    delay: float = 1.0,
    concurrency: int = 5,
):
    """Safe wrapper around the async crawler with allowlist and robots enforcement."""
    start_host = validate_url(start_url)
    allowed = filter_allowed_domains(allowed_domains)
    if start_host not in allowed:
        allowed.append(start_host)
    return await crawl_url(
        start_url,
        max_pages=max_pages,
        max_depth=max_depth,
        allowed_domains=allowed,
        concurrency=concurrency,
        rate_limit=delay,
    )
