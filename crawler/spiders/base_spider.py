from typing import Dict, Any

class BaseSpider:
    name = "base"
    async def crawl(self, seed_entry: Dict[str, Any]) -> Dict:
        """
        Must return dict with keys: url, html, text, metadata
        """
        raise NotImplementedError()
