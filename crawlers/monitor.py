"""Competitor brand monitoring"""
import asyncio
from crawl4ai import AsyncWebCrawler

MONITOR_SOURCES = {
    "zara": "https://www.zara.com/cn/",
    "uniqlo": "https://www.uniqlo.com/cn/",
    "hm": "https://www2.hm.com/zh_cn/",
}


async def check_brand_updates(brand_name: str, url: str) -> dict:
    """Check a brand for new products, price changes, etc."""
    result = {
        "brand": brand_name,
        "url": url,
        "status": "checked",
        "products_found": 0,
        "new_products": 0,
        "alerts": [],
    }
    
    try:
        async with AsyncWebCrawler() as crawler:
            page = await crawler.arun(url, word_count_threshold=30)
            if page.markdown:
                lines = [l.strip() for l in page.markdown.split("\n") if l.strip()]
                result["products_found"] = len(lines)
                result["page_summary"] = page.markdown[:500]
    except Exception as e:
        result["status"] = f"error: {e}"
    
    return result


async def run_monitor_brands(brands: list[str] | None = None) -> list[dict]:
    """Monitor specified brands or defaults."""
    targets = {}
    if brands:
        for b in brands:
            b_lower = b.lower()
            if b_lower in MONITOR_SOURCES:
                targets[b] = MONITOR_SOURCES[b_lower]
    else:
        targets = dict(list(MONITOR_SOURCES.items())[:3])
    
    results = []
    for brand, url in targets.items():
        print(f"🔍 Checking {brand}...")
        data = await check_brand_updates(brand, url)
        results.append(data)
        print(f"   {data['status']} - {data['products_found']} items found")
    
    return results


if __name__ == "__main__":
    results = asyncio.run(run_monitor_brands())
    for r in results:
        print(f"{r['brand']}: {r['status']} ({r['products_found']} products)")
