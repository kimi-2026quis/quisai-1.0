"""Multi-source fashion product search engine (no API keys, 100% public data).
Supports: ZARA, H&M, and web-based product discovery via DuckDuckGo + direct page scraping."""
import asyncio
import re
import json
from urllib.parse import unquote, quote
from crawl4ai import AsyncWebCrawler, BrowserConfig


# ─── ZARA ───────────────────────────────────────────────────────────

ZARA_CATEGORY_URLS = {
    "连衣裙": "https://www.zara.cn/cn/zh/%E5%A5%B3%E5%A3%AB-%E9%80%A3%E8%BA%AB%E8%A3%99-l1066.html",
    "上衣":   "https://www.zara.cn/cn/zh/%E5%A5%B3%E5%A3%AB-%E4%B8%8A%E8%A1%A3-l1322.html",
    "外套":   "https://www.zara.cn/cn/zh/%E5%A5%B3%E5%A3%AB-%E5%A4%96%E5%A5%97-l1202.html",
    "裤子":   "https://www.zara.cn/cn/zh/%E5%A5%B3%E5%A3%AB-%E8%A4%B2%E5%AD%90-l1355.html",
}

async def _scrape_zara(url: str) -> list[dict]:
    """Scrape products from a ZARA category page."""
    products = []
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url, word_count_threshold=10, bypass_cache=True, magic=True)
        html = result.html or ""
        # Extract product URLs with names and prices
        matches = re.findall(
            r'(https://www\.zara\.cn/cn/zh/([^/]*?)-p\d+[^\s\"\\<>]*?\.html).*?',
            html
        )
        prices = re.findall(r'¥[\s]*([\d,]+\.?\d*)', html)
        seen = set()
        for i, (full_url, name_enc) in enumerate(matches):
            url = full_url.split('?')[0]
            if url in seen: continue
            seen.add(url)
            try:
                name = unquote(name_enc)
            except:
                name = name_enc
            price = f"¥{prices[i]}" if i < len(prices) else "见商品页"
            products.append({
                "title": name, "url": url, "price": price,
                "brand": "ZARA", "source": "zara.cn",
            })
    return products


# ─── H&M ────────────────────────────────────────────────────────────

HM_BASE = "https://www2.hm.com"

async def _scrape_hm(category_path: str = "women/products/dresses.html") -> list[dict]:
    """Scrape H&M product listings. H&M loads data via JS, so we extract
    product IDs from listing page, then scrape each detail page."""
    products = []
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            f"{HM_BASE}/zh_cn/{category_path}",
            word_count_threshold=10, bypass_cache=True, magic=True
        )
        html = result.html or ""
        # Extract product IDs
        ids = re.findall(r'id=(\d+)', html)
        seen_ids = set()
        for pid in ids:
            if pid in seen_ids: continue
            seen_ids.add(pid)
            detail_url = f"{HM_BASE}/items/espier-detail?id={pid}"
            try:
                detail = await crawler.arun(detail_url, word_count_threshold=10, bypass_cache=True)
                detail_html = detail.html or ""
                # Extract product name from HTML title/meta
                title = ""
                t_match = re.search(r'<title>([^<]+)</title>', detail_html)
                if t_match: title = t_match.group(1).split('|')[0].strip()
                # Extract price
                price_match = re.search(r'(?:¥|￥|价格)\s*([\d,.]+)', detail_html)
                price = f"¥{price_match.group(1)}" if price_match else "见商品页"
                # Extract image
                img_match = re.search(r'(https://[^\"\\<> ]*?hm\.com[^\"\\<> ]*?product[^\"\\<> ]*?\.(?:jpg|png|webp)[^\"]*)', detail_html)
                img_url = img_match.group(1) if img_match else ""
                products.append({
                    "title": title or f"H&M商品 #{pid}",
                    "url": detail_url,
                    "price": price,
                    "brand": "H&M",
                    "source": "hm.com",
                    "image_url": img_url,
                })
            except Exception:
                continue
            if len(products) >= 10: break
    return products


# ─── Web Search (DuckDuckGo) ───────────────────────────────────────

async def _web_search_products(keyword: str, max_results: int = 15) -> list[dict]:
    """Search for products across the web using DuckDuckGo.
    Returns product-like results with URLs, titles, and snippets."""
    import time
    from duckduckgo_search import DDGS
    
    products = []
    queries = [
        f"{keyword} 购买",
        f"{keyword} 新款 2026",
    ]
    
    for query in queries:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                for r in results:
                    url = r.get('href', '')
                    title = r.get('title', '')
                    body = r.get('body', '')
                    # Only include URLs that look like product pages
                    if any(k in url.lower() for k in ['.com', '.cn', '.shop', '.store']):
                        # Skip known non-product domains
                        if any(skip in url.lower() for skip in ['facebook', 'instagram', 'twitter', 'youtube', 'pinterest', 'zhihu']):
                            continue
                        products.append({
                            "title": title.strip()[:80],
                            "url": url,
                            "price": "见商品页",
                            "brand": "全网",
                            "source": url.split('/')[2] if '//' in url else "web",
                            "snippet": body.strip()[:120] if body else "",
                        })
            time.sleep(1)  # Rate limit
        except Exception as e:
            print(f"    DDGS error: {e}")
            continue
    
    return products[:max_results]


# ─── Main Search ───────────────────────────────────────────────────

async def search_products(keyword: str, max_total: int = 30) -> list[dict]:
    """Search for products from ALL sources: ZARA, H&M, and web search.
    Returns list of {title, url, price, brand, source, image_url}"""
    all_products = []
    
    print(f"\n📦 Multi-source product search: {keyword}")
    
    # 1. ZARA
    category = "连衣裙" if any(k in keyword for k in ["裙", "dress", "连衣裙"]) else \
               "上衣" if any(k in keyword for k in ["上衣", "top", "shirt", "衬衫"]) else \
               "外套" if any(k in keyword for k in ["外套", "jacket", "夹克"]) else None
    if category:
        url = ZARA_CATEGORY_URLS.get(category)
        if url:
            print(f"  🔴 ZARA ({category})...")
            try:
                prods = await _scrape_zara(url)
                all_products.extend(prods)
                print(f"    → {len(prods)} products")
            except Exception as e:
                print(f"    → Error: {e}")
    
    # 2. H&M
    print(f"  🟡 H&M...")
    try:
        hm_products = await _scrape_hm()
        all_products.extend(hm_products)
        print(f"    → {len(hm_products)} products")
    except Exception as e:
        print(f"    → Error: {e}")
    
    # 3. Web Search
    print(f"  🔵 Web search...")
    try:
        web_products = await _web_search_products(keyword)
        all_products.extend(web_products)
        print(f"    → {len(web_products)} products")
    except Exception as e:
        print(f"    → Error: {e}")
    
    # Deduplicate
    seen = set()
    unique = []
    for p in all_products:
        key = p.get('url', '')[:80]
        if key and key not in seen:
            seen.add(key)
            unique.append(p)
    
    print(f"\n  📊 Total: {len(unique)} unique products from {len(set(p['source'] for p in unique))} sources")
    return unique[:max_total]


# ─── DeepSeek Analysis ────────────────────────────────────────────

def analyze_with_deepseek(products: list[dict], keyword: str) -> dict:
    """Analyze real product data with DeepSeek."""
    from openai import OpenAI
    from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL
    import os
    
    api_key = os.getenv("DEEPSEEK_API_KEY") or DEEPSEEK_API_KEY
    if not api_key:
        return {"error": "No DeepSeek API key"}
    
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    # Build product summary
    summaries = []
    sources = set()
    for p in products[:20]:
        summaries.append(f"- [{p['brand']}] {p['title']} | {p['price']}")
        sources.add(p['brand'])
    
    prompt = f"""你是服装行业数据分析师。基于以下从多个来源（{', '.join(sources)}）采集的"{keyword}"真实商品数据，做市场趋势分析。

真实商品数据（含品牌、名称、价格、链接）：
{chr(10).join(summaries)}

请用JSON格式回复（不要markdown）：
{{
  "keyword": "{keyword}",
  "total_products": {len(products)},
  "data_sources": {json.dumps(list(sources))},
  "price_range": "价格区间",
  "top_styles": ["风格1 - 占比%", "风格2 - 占比%"],
  "top_brands": [{{"name":"品牌","source":"数据来源","note":"特点"}}],
  "trend_direction": "上升|下降|稳定",
  "key_insight": "关键洞察50字",
  "suggestions": ["建议1","建议2","建议3"],
  "sample_products": [
    {{"title":"商品名","price":"价格","url":"链接","brand":"品牌"}}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=2000,
        )
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except Exception as e:
        return {"error": str(e), "keyword": keyword}


# ─── Image Search (Bing) ───────────────────────────────────────────

async def search_product_images(keyword: str, max_images: int = 10) -> list[str]:
    """Search for product images via Bing image search."""
    images = []
    async with AsyncWebCrawler() as crawler:
        try:
            result = await crawler.arun(
                f"https://www.bing.com/images/search?q={keyword}&form=HDRSC2",
                word_count_threshold=10, bypass_cache=True,
            )
            html = result.html or ""
            # Extract image URLs
            img_urls = re.findall(
                r'(https?://[^\s"\\<>]*?\.(?:jpg|jpeg|png|webp)(?:\?[^\s"\\<>]*?)?)', html
            )
            for url in img_urls:
                if any(skip in url for skip in ['th.bing.com', 'ts=1', 'sig=']):
                    continue
                if url not in images:
                    images.append(url)
                if len(images) >= max_images:
                    break
        except Exception as e:
            print(f"Image search error: {e}")
    return images


# ─── Full Pipeline ────────────────────────────────────────────────

async def run_analysis(keyword: str) -> dict:
    """Full pipeline: search all sources → analyze → return results."""
    products = await search_products(keyword)
    analysis = analyze_with_deepseek(products, keyword)
    return {"keyword": keyword, "products": products, "analysis": analysis,
            "product_count": len(products), "source_count": len(set(p['source'] for p in products))}


if __name__ == "__main__":
    result = asyncio.run(run_analysis("连衣裙"))
    print("\n" + "="*60)
    print(f"✅ Found {result['product_count']} products from {result['source_count']} sources")
    a = result.get('analysis', {})
    if isinstance(a, dict) and not a.get('error'):
        print(f"📊 价格区间: {a.get('price_range','?')}")
        print(f"📊 趋势: {a.get('trend_direction','?')}")
        print(f"📊 洞察: {a.get('key_insight','?')}")
        print("\n📦 商品清单:")
        for p in result['products'][:10]:
            print(f"  {p['price']:>10s} | {p['brand']:6s} | {p['title'][:40]}")
            print(f"  {'':>10s}   {p['url'][:80]}")
