"""
Optimized Crawler/Scraper System
FAANG-level efficiency with LLM integration and RAG
"""
import asyncio
import hashlib
import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

import aiohttp
import httpx
from bs4 import BeautifulSoup
from aiohttp import ClientSession, ClientTimeout

from safety import (
    SCRAPER_USER_AGENT,
    RateLimiter,
    filter_allowed_domains,
    robots_can_fetch_httpx,
    validate_url,
)

@dataclass
class CrawlConfig:
    """Crawler configuration"""
    max_pages: int = 100
    max_depth: int = 3
    max_concurrent: int = 10
    timeout_sec: int = 30
    allowed_domains: List[str] = field(default_factory=list)
    blocked_patterns: List[str] = field(default_factory=lambda: [
        r'\.pdf$', r'\.zip$', r'\.exe$', r'\.dmg$',
        r'/login', r'/signin', r'/logout', r'/signout'
    ])
    extract_images: bool = False
    extract_tables: bool = True
    extract_links: bool = True
    dedup_content: bool = True
    llm_analyze: bool = False
    sheet_id: Optional[str] = None

@dataclass
class CrawlResult:
    """Result from crawling a single page"""
    url: str
    status_code: int
    html: str
    text: str
    title: str
    meta: Dict[str, str]
    links: List[str]
    images: List[str]
    tables: List[List[List[str]]]
    content_hash: str
    fetched_at: str
    depth: int
    error: Optional[str] = None

class OptimizedCrawler:
    """High-performance async crawler with deduplication and LLM integration"""
    
    def __init__(self, config: CrawlConfig):
        self.config = config
        self.visited: Set[str] = set()
        self.content_hashes: Set[str] = set()
        self.results: List[CrawlResult] = []
        self.rate_limiter = RateLimiter()
        self.host_last_fetch: Dict[str, float] = defaultdict(float)
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication"""
        parsed = urlparse(url)
        # Remove fragment, query params (optional), trailing slash
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip('/'),
            '',  # params
            '',  # query - remove for strict dedup
            ''   # fragment
        ))
        return normalized
    
    def _content_fingerprint(self, text: str) -> str:
        """Generate content fingerprint for deduplication"""
        # Normalize whitespace
        clean = re.sub(r'\s+', ' ', text.strip())
        return hashlib.sha256(clean.encode()).hexdigest()
    
    def _is_blocked(self, url: str) -> bool:
        """Check if URL matches blocked patterns"""
        for pattern in self.config.blocked_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract and normalize links from HTML"""
        links = []
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            absolute = urljoin(base_url, href)
            normalized = self._normalize_url(absolute)
            
            # Filter by domain
            parsed = urlparse(normalized)
            if not self.config.allowed_domains or parsed.netloc in self.config.allowed_domains:
                if not self._is_blocked(normalized):
                    links.append(normalized)
        return links
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[List[List[str]]]:
        """Extract tables from HTML"""
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        return tables
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text from HTML"""
        # Remove scripts, styles
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        # Collapse whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text
    
    async def _fetch_page(self, session: ClientSession, url: str, depth: int) -> Optional[CrawlResult]:
        """Fetch and parse a single page"""
        async with self.semaphore:
            # Rate limiting per host
            parsed = urlparse(url)
            host = parsed.netloc
            
            last_fetch = self.host_last_fetch.get(host, 0)
            elapsed = time.time() - last_fetch
            if elapsed < 1.0:  # Min 1 second between requests to same host
                await asyncio.sleep(1.0 - elapsed)
            
            try:
                # Robots check
                allowed = await robots_can_fetch_httpx(url, SCRAPER_USER_AGENT)
                if not allowed:
                    return None
                
                # Fetch
                async with session.get(
                    url,
                    headers={'User-Agent': SCRAPER_USER_AGENT},
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout_sec)
                ) as response:
                    self.host_last_fetch[host] = time.time()
                    
                    if response.status != 200:
                        return CrawlResult(
                            url=url,
                            status_code=response.status,
                            html='',
                            text='',
                            title='',
                            meta={},
                            links=[],
                            images=[],
                            tables=[],
                            content_hash='',
                            fetched_at=datetime.now().isoformat(),
                            depth=depth,
                            error=f"HTTP {response.status}"
                        )
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Extract data
                    title = soup.title.string if soup.title else ''
                    text = self._extract_text(soup)
                    content_hash = self._content_fingerprint(text)
                    
                    # Deduplication
                    if self.config.dedup_content and content_hash in self.content_hashes:
                        return None
                    
                    self.content_hashes.add(content_hash)
                    
                    meta = {}
                    for tag in soup.find_all('meta'):
                        name = tag.get('name') or tag.get('property')
                        content = tag.get('content')
                        if name and content:
                            meta[name] = content
                    
                    links = self._extract_links(soup, url) if self.config.extract_links else []
                    images = [img.get('src') for img in soup.find_all('img', src=True)] if self.config.extract_images else []
                    tables = self._extract_tables(soup) if self.config.extract_tables else []
                    
                    return CrawlResult(
                        url=url,
                        status_code=response.status,
                        html=html[:50000],  # Truncate large HTML
                        text=text,
                        title=title,
                        meta=meta,
                        links=links,
                        images=images,
                        tables=tables,
                        content_hash=content_hash,
                        fetched_at=datetime.now().isoformat(),
                        depth=depth
                    )
                    
            except Exception as e:
                return CrawlResult(
                    url=url,
                    status_code=0,
                    html='',
                    text='',
                    title='',
                    meta={},
                    links=[],
                    images=[],
                    tables=[],
                    content_hash='',
                    fetched_at=datetime.now().isoformat(),
                    depth=depth,
                    error=str(e)
                )
    
    async def crawl(self, start_url: str) -> List[CrawlResult]:
        """Execute crawl from start URL"""
        start_normalized = self._normalize_url(start_url)
        
        # BFS queue
        queue: List[Tuple[str, int]] = [(start_normalized, 0)]
        
        async with aiohttp.ClientSession() as session:
            while queue and len(self.results) < self.config.max_pages:
                # Batch fetch
                batch = []
                while queue and len(batch) < self.config.max_concurrent:
                    url, depth = queue.pop(0)
                    if url in self.visited or depth > self.config.max_depth:
                        continue
                    self.visited.add(url)
                    batch.append((url, depth))
                
                if not batch:
                    break
                
                # Fetch batch
                tasks = [self._fetch_page(session, url, depth) for url, depth in batch]
                results = await asyncio.gather(*tasks)
                
                # Process results
                for result in results:
                    if result and not result.error:
                        self.results.append(result)
                        
                        # Add child links to queue
                        if result.depth < self.config.max_depth:
                            for link in result.links:
                                if link not in self.visited:
                                    queue.append((link, result.depth + 1))
        
        return self.results
    
    def to_dict(self) -> Dict:
        """Convert results to dictionary"""
        return {
            'start_url': self.results[0].url if self.results else '',
            'pages_crawled': len(self.results),
            'total_links': sum(len(r.links) for r in self.results),
            'total_tables': sum(len(r.tables) for r in self.results),
            'results': [
                {
                    'url': r.url,
                    'title': r.title,
                    'text_length': len(r.text),
                    'links_count': len(r.links),
                    'tables_count': len(r.tables),
                    'depth': r.depth,
                    'fetched_at': r.fetched_at,
                    'error': r.error
                }
                for r in self.results
            ]
        }

async def crawl_optimized(start_url: str, config: CrawlConfig) -> Dict:
    """Main entry point for optimized crawling"""
    crawler = OptimizedCrawler(config)
    await crawler.crawl(start_url)
    return crawler.to_dict()
