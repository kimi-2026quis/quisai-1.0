"""QuisAI 全面测试脚本 - 测试所有模块"""
import asyncio
import json
import os
import dotenv
from datetime import datetime

dotenv.load_dotenv()
ssl_file = os.getenv("SSL_CERT_FILE")
if ssl_file:
    os.environ["SSL_CERT_FILE"] = ssl_file

results = {"pass": 0, "fail": 0, "tests": []}

def report(name, status, detail=""):
    icon = "✅" if status else "❌"
    results["pass" if status else "fail"] += 1
    results["tests"].append({"name": name, "status": status, "detail": detail[:200]})
    print(f"  {icon} {name}")
    if detail:
        for line in str(detail).split("\n")[:3]:
            print(f"     {line}")


print("=" * 60)
print("QUISAI 全面功能测试")
print(f"Time: {datetime.now().isoformat()}")
print("=" * 60)

# ========== TEST 1: RSS News Crawler ==========
print("\n📰 [1/6] RSS新闻抓取")
try:
    from crawlers.news import run_news_crawler
    articles = asyncio.run(run_news_crawler())
    assert len(articles) > 0, "0 articles returned"
    has_content = any(a.get("content") for a in articles[:5])
    report("RSS抓取新闻", True, f"{len(articles)} 篇文章, 有详情: {has_content}")
except Exception as e:
    report("RSS抓取新闻", False, str(e))

# ========== TEST 2: Product Search (ZARA) ==========
print("\n🛒 [2/6] ZARA商品搜索")
try:
    from crawlers.product_search import search_products
    products = asyncio.run(search_products("连衣裙"))
    assert len(products) > 0, "0 products"
    with_prices = sum(1 for p in products if p.get("price") and "见商品页" not in p["price"])
    with_links = sum(1 for p in products if p.get("url", "").startswith("http"))
    report("ZARA商品搜索", True, f"{len(products)} 件商品, 含价格: {with_prices}, 含链接: {with_links}")
    # Show sample
    if products:
        p = products[0]
        report("商品样例", True, f"[{p['brand']}] {p['title']} | {p['price']}")
except Exception as e:
    report("ZARA商品搜索", False, str(e))

# ========== TEST 3: Image Search ==========
print("\n🖼️ [3/6] 商品图片搜索")
try:
    from crawlers.product_search import search_product_images
    images = asyncio.run(search_product_images("连衣裙 2026"))
    assert len(images) > 0, "0 images"
    report("图片搜索", True, f"{len(images)} 张图片, 首图: {images[0][:80]}")
except Exception as e:
    report("图片搜索", False, str(e))

# ========== TEST 4: DeepSeek Analysis ==========
print("\n🤖 [4/6] DeepSeek AI分析")
try:
    from crawlers.product_search import analyze_with_deepseek, search_products
    products_sample = asyncio.run(search_products("连衣裙"))
    analysis = analyze_with_deepseek(products_sample[:10], "连衣裙")
    assert isinstance(analysis, dict), "Not a dict"
    assert not analysis.get("error"), analysis.get("error", "")
    has_key_insight = bool(analysis.get("key_insight"))
    has_price_range = bool(analysis.get("price_range"))
    has_sample_products = bool(analysis.get("sample_products"))
    report("DeepSeek分析", True, 
           f"价格区间: {analysis.get('price_range','?')} | "
           f"趋势: {analysis.get('trend_direction','?')} | "
           f"洞察: {analysis.get('key_insight','?')[:40]}...")
    report("分析含关键洞察", has_key_insight)
    report("分析含价格区间", has_price_range)
    report("分析含示例商品", has_sample_products, 
           f"{len(analysis.get('sample_products',[]))} 个商品")
except Exception as e:
    report("DeepSeek分析", False, str(e))

# ========== TEST 5: Supabase Data Save ==========
print("\n💾 [5/6] Supabase数据入库")
try:
    from supabase_client import save_fashion_news, get_admin_client
    
    # Test save
    from crawlers.news import run_news_crawler
    articles = asyncio.run(run_news_crawler())
    if articles:
        saved = save_fashion_news(articles)
        report("新闻入库", True, f"保存 {saved} 条新闻")
    
    # Test connectivity
    client = get_admin_client()
    resp = client.table("fashion_news").select("id").limit(1).execute()
    report("数据库连接", True, "Supabase 连接正常")
    
    # Count existing records
    count = client.table("fashion_news").select("id", count="exact").execute()
    report("数据查询", True, f"fashion_news 表共 {count.count if hasattr(count, 'count') else '?'} 条记录")
except Exception as e:
    report("Supabase操作", False, str(e))

# ========== TEST 6: Full Pipeline (ZARA only) ==========
print("\n🔗 [6/6] 完整链路测试 (ZARA → DeepSeek → Supabase)")
try:
    from crawlers.product_search import search_products, analyze_with_deepseek
    from supabase_client import save_analysis_report
    
    products = asyncio.run(search_products("连衣裙"))
    assert len(products) >= 5, f"Only {len(products)} products"
    
    analysis = analyze_with_deepseek(products[:15], "连衣裙")
    assert isinstance(analysis, dict) and not analysis.get("error")
    
    save_analysis_report("连衣裙", "zara", {
        "products": products[:10],
        "analysis": analysis,
        "product_count": len(products),
    })
    
    report("完整链路", True, 
           f"爬虫 → {len(products)}商品 → AI分析 → Supabase入库 ✅")
    
    # Show final product samples
    print("\n  最终输出商品样例:")
    for p in products[:5]:
        print(f"    {p['price']:>10s} | {p['title'][:35]:35s} | {p['brand']}")
        print(f"    {'':>10s}   {p['url'][:70]}")
    
except Exception as e:
    report("完整链路", False, str(e))

# ========== SUMMARY ==========
print("\n" + "=" * 60)
print(f"📊 测试总结: {results['pass']} ✅ 通过, {results['fail']} ❌ 失败")
print("=" * 60)
