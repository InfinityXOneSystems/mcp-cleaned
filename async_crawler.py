import asyncio
import aiohttp
from aiohttp import ClientTimeout
from urllib import robotparser
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from safety import (
    SCRAPER_USER_AGENT,
    RateLimiter,
    filter_allowed_domains,
    robots_can_fetch_aiohttp,
    validate_url,
)


class AsyncCrawler:
    def __init__(self, max_tasks=10, max_pages=100, max_depth=2, allowed_domains=None, rate_limit=1.0, user_agent: str = SCRAPER_USER_AGENT):
        self.max_tasks = max_tasks
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.allowed_domains = set(filter_allowed_domains(allowed_domains)) if allowed_domains else set()
        self.rate_limit = rate_limit
        self.visited = set()
        self.to_visit = asyncio.Queue()
        self.results = []
        self.sem = asyncio.Semaphore(max_tasks)
        self.user_agent = user_agent
        self.robots = {}
        self._rate_limiter = RateLimiter(min_delay=rate_limit)

    async def fetch(self, session, url):
        # politeness: per-host delay
        parsed = urlparse(url)
        host = parsed.netloc
        await self._rate_limiter.wait(host)
        headers = {'User-Agent': self.user_agent}
        try:
            async with session.get(url, timeout=ClientTimeout(total=20), headers=headers) as resp:
                if resp.content_type and 'html' in resp.content_type:
                    text = await resp.text(errors='ignore')
                    return text, resp.status
                else:
                    return None, resp.status
        except Exception:
            return None, None

    async def allowed_by_robots(self, session, url):
        parsed = urlparse(url)
        host = parsed.netloc
        cached = self.robots.get(host)
        if isinstance(cached, robotparser.RobotFileParser):
            return cached.can_fetch(self.user_agent, url)
        if cached is False:
            return False
        rp = robotparser.RobotFileParser()
        robots_url = f"{parsed.scheme}://{host}/robots.txt"
        try:
            async with session.get(robots_url, headers={'User-Agent': self.user_agent}, timeout=ClientTimeout(total=5)) as resp:
                if resp.status >= 400:
                    self.robots[host] = False
                    return False
                text = await resp.text()
                rp.parse(text.splitlines())
        except Exception:
            self.robots[host] = False
            return False
        self.robots[host] = rp
        return rp.can_fetch(self.user_agent, url)

    def extract_links(self, base, html):
        soup = BeautifulSoup(html, 'lxml')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('mailto:') or href.startswith('javascript:'):
                continue
            joined = urljoin(base, href)
            parsed = urlparse(joined)
            if parsed.scheme not in ('http','https'):
                continue
            if self.allowed_domains and parsed.netloc not in self.allowed_domains:
                continue
            links.add(joined.split('#')[0])
        return links

    async def worker(self, session):
        while len(self.results) < self.max_pages:
            try:
                url, depth = await asyncio.wait_for(self.to_visit.get(), timeout=5.0)
            except asyncio.TimeoutError:
                break
            if url in self.visited:
                continue
            if self.allowed_domains:
                if urlparse(url).netloc not in self.allowed_domains:
                    continue
            async with self.sem:
                ok = await self.allowed_by_robots(session, url)
                if not ok:
                    self.visited.add(url)
                    self.to_visit.task_done()
                    continue
                html, status = await self.fetch(session, url)
                self.visited.add(url)
                if html:
                    links = self.extract_links(url, html)
                    self.results.append({'url': url, 'html': html, 'status': status})
                    if depth < self.max_depth:
                        for l in links:
                            if l not in self.visited and self.to_visit.qsize() + len(self.results) < self.max_pages:
                                await self.to_visit.put((l, depth+1))
                self.to_visit.task_done()

    async def crawl(self, start_url):
        start_host = validate_url(start_url)
        if not self.allowed_domains:
            self.allowed_domains = {start_host}
        else:
            # ensure allowed domains remain allowed after validation
            self.allowed_domains = set(filter_allowed_domains(self.allowed_domains)) | {start_host}
        await self.to_visit.put((start_url, 0))
        timeout = ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [asyncio.create_task(self.worker(session)) for _ in range(self.max_tasks)]
            await asyncio.gather(*tasks)
        return self.results

async def crawl_url(start_url, max_pages=100, max_depth=2, allowed_domains=None, concurrency=10, rate_limit=1.0):
    c = AsyncCrawler(max_tasks=concurrency, max_pages=max_pages, max_depth=max_depth, allowed_domains=allowed_domains, rate_limit=rate_limit)
    return await c.crawl(start_url)
