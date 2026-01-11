import asyncio

from async_crawler import crawl_url


async def t():
    res = await crawl_url(
        "http://example.com", max_pages=2, max_depth=1, concurrency=2, rate_limit=0.1
    )
    print("got", len(res))


if __name__ == "__main__":
    asyncio.run(t())
