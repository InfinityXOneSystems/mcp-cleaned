from .base_spider import BaseSpider
from typing import Dict, Any
import asyncio
from playwright.async_api import async_playwright

class SocialSpider(BaseSpider):
    name = "social"
    async def crawl(self, seed_entry: Dict[str, Any]) -> Dict[str, Any]:
        url = seed_entry["url"]
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            html = await page.content()
            text = await page.inner_text("body")
            await browser.close()
            return {"url": url, "html": html, "text": text, "metadata": {"source_type": seed_entry.get("type")}}

# Example usage from engine: instantiate and call crawl(seed_entry)
