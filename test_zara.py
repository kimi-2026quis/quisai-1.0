"""QuisAI 全面功能测试 - 仅 ZARA 数据源"""
import asyncio
import json
import os
import dotenv
from datetime import datetime

dotenv.load_dotenv()
ssl_file = os.getenv("SSL_CERT_FILE")
if ssl_file:
    os.environ["SSL_CERT_FILE"] = ssl_file

PASS = 0
FAIL = 0

def test(name, fn, *args, **kw):
    global PASS, FAIL
    try:
        result = fn(*args, **kw)
        if result is False:
            raise AssertionError("returned False")
        PASS += 1
        print(f"  ✅ {name}")
        return result
    except Exception as e:
        FAIL += 1
        print(f"  ❌ {name}: {e}")
        return None

print("=" * 60)
print("QUISAI - ZARA 全功能测试")
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 60)

# ── 0. Config check ──
print("\n📋 [0/6] 环境检查")
from config import SUPABASE_URL, DEEPSEEK_API_KEY
test("Supabase URL 存在", lambda: bool(SUPABASE_URL))
test("DeepSeek API Key 存在", lambda: bool(DEEPSEEK_API_KEY) and DEEPSEEK_API_KEY.startswith("sk"))

# ── 1. RSS News Crawler ──
print("\n📰 [1/6] RSS新闻抓取")
from crawlers.news import run_news_crawler
articles = test("RSS抓取新闻", lambda: asyncio.run(run_news_crawler()))
if articles:
    print(f"    → {len(articles)} 篇文章")
    has_detail = any(a.get("content") for a in articles[:3])
    print(f"    → 含详情内容: {'✅' if has_detail else '❌'}")

# ── 2. ZARA Product Search ──
print("\n🛒 [2/6] ZARA商品搜索")
from crawlers.product_search import ZARA_CATEGORY_URLS, _scrape_zara

products_zara = test("ZARA连衣裙搜索", lambda: asyncio.run(_scrape_zara(ZARA_CATEGORY_URLS["连衣裙"])))
if products_zara:
    print(f"    → {len(products_zara)} 件商品")
    with_price = sum(1 for p in products_zara if p.get("price") and "见商品页" not in p["price"])
    with_link = sum(1 for p in products_zara if p.get("url","").startswith("http"))
    print(f"    → 含价格: {with_price}/{len(products_zara)}")
    print(f"    → 含链接: {with_link}/{len(products_zara)}")
    print(f"\n    前5件商品:")
    for p in products_zara[:5]:
        print(f"      {p['price']:>10s} | {p['title'][:35]}")
        print(f"      {'':>10s}   {p['url'][:70]}")

# ── 3. Image Search ──
print("\n🖼️ [3/6] 商品图片搜索")
from crawlers.product_search import search_product_images
images = test("Bing图片搜索", lambda: asyncio.run(search_product_images("连衣裙 2026")))
if images is not None:
    print(f"    → {len(images)} 张图片")
    if images:
        print(f"    → 首图: {images[0][:80]}")

# ── 4. DeepSeek Analysis ──
print("\n🤖 [4/6] DeepSeek AI分析")
from crawlers.product_search import analyze_with_deepseek
if products_zara:
    analysis = test("DeepSeek趋势分析", lambda: analyze_with_deepseek(products_zara[:15], "连衣裙"))
    if analysis and isinstance(analysis, dict):
        print(f"    → 价格区间: {analysis.get('price_range','?')}")
        print(f"    → 趋势方向: {analysis.get('trend_direction','?')}")
        print(f"    → 关键洞察: {analysis.get('key_insight','?')}")
        print(f"    → 示例商品: {len(analysis.get('sample_products',[]))} 个")
        if analysis.get('suggestions'):
            for s in analysis['suggestions']:
                print(f"    → 建议: {s}")

# ── 5. Supabase ──
print("\n💾 [5/6] Supabase数据库")
from supabase_client import get_admin_client
try:
    client = get_admin_client()
    resp = client.table("fashion_news").select("id").limit(1).execute()
    count_resp = client.table("fashion_news").select("id", count="exact").limit(0).execute()
    print(f"  ✅ Supabase连接正常")
    print(f"    → fashion_news 表记录数: {getattr(count_resp, 'count', '?')}")
    PASS += 1
except Exception as e:
    print(f"  ❌ Supabase: {e}")
    FAIL += 1

# Test saving products to Supabase
if products_zara:
    try:
        from supabase_client import save_analysis_report
        save_analysis_report("连衣裙", "zara", {
            "products": products_zara[:10],
            "analysis": analysis if isinstance(analysis, dict) else {},
            "product_count": len(products_zara),
        })
        print(f"  ✅ 分析结果写入Supabase (fashion_news表)")
        PASS += 1
    except Exception as e:
        print(f"  ❌ 写入Supabase: {e}")
        FAIL += 1

# ── 6. Competitor Monitor ──
print("\n🏪 [6/6] 竞品监控")
from crawlers.monitor import run_monitor_brands
monitor_results = test("竞品监控", lambda: asyncio.run(run_monitor_brands(["zara", "uniqlo", "hm"])))
if monitor_results:
    for r in monitor_results:
        print(f"    → {r['brand']}: {r.get('status','?')} ({r.get('products_found',0)} items)")

# ── Summary ──
print("\n" + "=" * 60)
print(f"📊 测试总结: {PASS} ✅ 通过, {FAIL} ❌ 失败")
if FAIL > 0:
    print("⚠️  有失败项，需要排查")
else:
    print("🎉 全部通过！")
print("=" * 60)
