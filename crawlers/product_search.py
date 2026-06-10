"""Product search from public fashion brand websites (no API keys needed).
Searches ZARA, UNIQLO, H&M category pages for real product data with links, prices, and images."""
import asyncio
import re
import json
from urllib.parse import unquote
from crawl4ai import AsyncWebCrawler, BrowserConfig

# Public brand category page URLs
BRAND_CATEGORIES = {
    "zara_dresses": "https://www.zara.cn/cn/zh/%E5%A5%B3%E5%A3%AB-%E9%80%A3%E8%BA%AB%E8%A3%99-l1066.html",
    "zara_tops": "https://www.zara.cn/cn/zh/%E5%A5%B3%E5%A3%AB-%E4%B8%8A%E8%A1%A3-l1322.html",
    "uniqlo_dresses": "https://www.uniqlo.cn/zh_CN/%E5%A5%B3%E8%A3%85/%E8%BF%9E%E8%A1%A3%E8%A3%99.html",
    "hm_dresses": "https://www2.hm.com/zh_cn/women/products/dresses.html",
}


def extract_product_name(url: str) -> str:
    """Extract Chinese product name from ZARA URL."""
    # URL format: https://www.zara.cn/cn/zh/产品名-pXXX.html
    match = re.search(r'/([^/]+)-p\d+\.html', url)
    if match:
        name_encoded = match.group(1)
        try:
            return unquote(name_encoded)
        except:
            return name_encoded
    return ""


async def scrape_zara_category(url: str) -> list[dict]:
    """Scrape ZARA category page for product listings."""
    products = []
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url,
            word_count_threshold=10,
            bypass_cache=True,
            magic=True
        )
        
        html = result.html or ""
        
        # Extract product URLs with names
        # ZARA format: https://www.zara.cn/cn/zh/name-pXXXXX.html
        product_matches = re.findall(
            r'(https://www\.zara\.cn/cn/zh/[^\s\"\\<>]*?-p\d+[^\s\"\\<>]*?\.html)',
            html
        )
        
        # Extract all prices
        prices = re.findall(r'¥[\s]*([\d,]+\.?\d*)', html)
        
        seen_urls = set()
        for i, url in enumerate(product_matches):
            url = url.split('?')[0]  # Clean URL
            if url not in seen_urls:
                seen_urls.add(url)
                name = extract_product_name(url)
                price = prices[i] if i < len(prices) else ""
                
                products.append({
                    "title": name,
                    "url": url,
                    "price": f"¥{price}" if price else "见商品页",
                    "brand": "ZARA",
                    "source": "zara.cn",
                    "category": "女装连衣裙",
                    "image_url": "",  # Will get from product page
                })
    
    return products


async def scrape_uniqlo_category(url: str) -> list[dict]:
    """Scrape UNIQLO category page."""
    products = []
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url,
            word_count_threshold=10,
            bypass_cache=True,
        )
        
        md = result.markdown or ""
        html = result.html or ""
        
        # UNIQLO has simpler structure
        # Look for product patterns in markdown
        lines = [l.strip() for l in md.split('\n') if l.strip()]
        
        for line in lines:
            # Skip navigation/UI
            if len(line) < 10 or line.startswith('[') or line.startswith('*'):
                continue
            # Look for product price with ¥
            if '¥' in line or '￥' in line:
                price_match = re.search(r'[¥￥]\s*[\d,]+', line)
                if price_match:
                    # Extract URL from the line
                    url_match = re.search(r'https?://[^\s\)\]>\'\"\[\]]+', line)
                    if url_match:
                        products.append({
                            "title": line.replace(price_match.group(0), '').strip()[:60],
                            "url": url_match.group(0).split('?')[0],
                            "price": price_match.group(0),
                            "brand": "UNIQLO",
                            "source": "uniqlo.cn",
                            "image_url": "",
                        })
        
        # Also try to find product URLs in HTML
        if len(products) < 5:
            product_urls = re.findall(
                r'(https://www\.uniqlo\.cn/[^\s\"\\<>]*?(?:product|goods)[^\s\"\\<>]*?\.html)',
                html
            )
            for url in product_urls:
                name_match = re.search(r'/([^/]+?)\.html', url)
                name = name_match.group(1) if name_match else ""
                products.append({
                    "title": name.replace('-', ' ').title()[:60],
                    "url": url.split('?')[0],
                    "price": "见商品页",
                    "brand": "UNIQLO",
                    "source": "uniqlo.cn",
                    "image_url": "",
                })
    
    return products


async def search_fashion_products(keyword: str, max_products: int = 20) -> list[dict]:
    """Search for fashion products across brand websites.
    Maps keyword to appropriate brand categories and scrapes them."""
    all_products = []
    
    # Determine which categories to search based on keyword
    targets = []
    if any(k in keyword for k in ['连衣裙', 'dress', '裙']):
        targets = ["zara_dresses", "uniqlo_dresses", "hm_dresses"]
    elif any(k in keyword for k in ['上衣', 'top', 'shirt', '衬衫']):
        targets = ["zara_tops"]
    else:
        targets = ["zara_dresses", "zara_tops"]
    
    for target in targets:
        url = BRAND_CATEGORIES.get(target)
        if not url:
            continue
        
        print(f"  Scraping {target}...")
        try:
            if target.startswith("zara"):
                products = await scrape_zara_category(url)
            elif target.startswith("uniqlo"):
                products = await scrape_uniqlo_category(url)
            else:
                products = []
            
            print(f"    Found {len(products)} products")
            all_products.extend(products)
        except Exception as e:
            print(f"    Error: {e}")
        
        if len(all_products) >= max_products:
            break
    
    # Deduplicate
    seen = set()
    unique = []
    for p in all_products:
        if p['url'] not in seen:
            seen.add(p['url'])
            unique.append(p)
    
    return unique[:max_products]


async def search_product_images(keyword: str, max_images: int = 10) -> list[str]:
    """Search for product images using Bing image search via Crawl4AI."""
    images = []
    
    encoded = keyword
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            f"https://www.bing.com/images/search?q={encoded}&form=HDRSC2",
            word_count_threshold=10,
            bypass_cache=True,
        )
        
        html = result.html or ""
        # Extract image URLs from Bing results
        img_urls = re.findall(
            r'(https?://[^\s\"\\<>]*?\.(?:jpg|jpeg|png|webp)(?:\?[^\s\"\\<>]*?)?)',
            html
        )
        
        for url in img_urls:
            # Filter out small/thumnail images
            if any(d in url for d in ['th.bing.com', 'ts=1', 'sig=']):
                continue
            if url not in images:
                images.append(url)
            if len(images) >= max_images:
                break
    
    return images


def analyze_products_with_deepseek(products: list[dict], keyword: str) -> dict:
    """Use DeepSeek to analyze scraped product data and generate trend report."""
    from openai import OpenAI
    from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL
    import os
    
    api_key = os.getenv("DEEPSEEK_API_KEY") or DEEPSEEK_API_KEY
    if not api_key:
        return {"error": "No DeepSeek API key"}
    
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    # Build product summary for analysis
    product_summaries = []
    for p in products[:15]:
        product_summaries.append(f"- {p['title']} | 品牌: {p['brand']} | 价格: {p['price']}")
    
    prompt = f"""你是服装行业数据分析师。基于以下从ZARA、UNIQLO等品牌官网采集的"{keyword}"真实商品数据，做趋势分析。

真实商品数据：
{chr(10).join(product_summaries)}

请分析并用JSON格式回复（不要markdown）：
{{
  "keyword": "{keyword}",
  "total_products": {len(products)},
  "price_range": "价格区间",
  "top_styles": ["风格1 - 占比%", "风格2 - 占比%"],
  "top_colors": [{{"name":"颜色","hex":"#十六进制","percentage":"占比%"}}],
  "top_brands": [{{"name":"品牌名","position":"定位"}}],
  "trend_direction": "上升|下降|稳定",
  "key_insight": "关键洞察50字",
  "suggestions": ["建议1","建议2"],
  "sample_products": [
    {{"title":"商品名","price":"价格","url":"商品链接"}}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
        )
        content = response.choices[0].message.content
        # Clean markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except Exception as e:
        print(f"DeepSeek error: {e}")
        return {"error": str(e), "keyword": keyword, "total_products": len(products)}


async def run_trend_analysis(keyword: str) -> dict:
    """Complete pipeline: search products → get images → DeepSeek analysis."""
    print(f"\n{'='*50}")
    print(f"🔍 QuisAI Trend Analysis: {keyword}")
    print(f"{'='*50}")
    
    # Step 1: Search products from brand websites
    print(f"\n📦 Step 1: Searching products...")
    products = await search_fashion_products(keyword)
    print(f"   Found {len(products)} real products")
    
    # Step 2: Get product images
    print(f"\n🖼️  Step 2: Searching images...")
    images = await search_product_images(keyword)
    print(f"   Found {len(images)} images")
    
    # Step 3: DeepSeek analysis
    print(f"\n🤖 Step 3: DeepSeek trend analysis...")
    analysis = analyze_products_with_deepseek(products, keyword)
    
    return {
        "keyword": keyword,
        "products": products,
        "images": images,
        "analysis": analysis,
        "product_count": len(products),
        "image_count": len(images),
    }


if __name__ == "__main__":
    result = asyncio.run(run_trend_analysis("连衣裙"))
    print("\n=== RESULTS ===")
    print(f"Products: {result['product_count']}")
    print(f"Images: {result['image_count']}")
    if result['products']:
        print("\nSample products:")
        for p in result['products'][:5]:
            print(f"  {p['price']:>10} | {p['title'][:40]} | {p['brand']}")
    if isinstance(result.get('analysis'), dict) and not result['analysis'].get('error'):
        print(f"\nAnalysis:")
        a = result['analysis']
        print(f"  价格区间: {a.get('price_range','?')}")
        print(f"  趋势: {a.get('trend_direction','?')}")
        print(f"  关键洞察: {a.get('key_insight','?')}")
