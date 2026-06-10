"""Fashion news crawler using RSS feeds and Crawl4AI"""
import asyncio
import feedparser
from datetime import datetime
from crawl4ai import AsyncWebCrawler

from config import FASHION_RSS_FEEDS, DEEPSEEK_API_KEY

FASHION_KEYWORDS = [
    "fashion", "服装", "时尚", "designer", "collection", "runway",
    "trend", "布料", "面料", "服装行业", "retail",
]


async def fetch_rss_entries() -> list[dict]:
    """Fetch latest entries from fashion RSS feeds."""
    articles = []
    for feed_url in FASHION_RSS_FEEDS[:3]:  # Limit to 3 feeds for speed
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                articles.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "source": feed.feed.get("title", "Fashion Media"),
                    "published_at": entry.get("published", datetime.now().isoformat()),
                    "image_url": "",
                    "tags": [],
                    "category": classify_by_title(entry.get("title", "")),
                    "is_hot": False,
                })
        except Exception as e:
            print(f"RSS error {feed_url}: {e}")
    return articles


def classify_by_title(title: str) -> str:
    """Classify article by title keywords."""
    t = title.lower()
    if any(w in t for w in ["runway", "时装周", "collection", "秀场"]):
        return "走秀"
    if any(w in t for w in ["brand", "品牌", "财报", "收购", "zara", "uniqlo"]):
        return "品牌动向"
    if any(w in t for w in ["new", "上新", "新品", "发布", "联名"]):
        return "新品发布"
    if any(w in t for w in ["trend", "趋势", "流行", "style"]):
        return "时尚潮流"
    if any(w in t for w in ["tech", "ai", "技术", "数字", "3d"]):
        return "技术更新"
    if any(w in t for w in ["fabric", "面料", "material", "sustainable", "可持续"]):
        return "时尚资讯"
    return "行业资讯"


async def crawl_article_detail(url: str) -> str:
    """Crawl full article content."""
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url, word_count_threshold=50)
            return result.markdown[:5000] if result.markdown else ""
    except Exception as e:
        print(f"Crawl error {url}: {e}")
        return ""


def translate_article(title: str, content: str) -> dict:
    """Use DeepSeek to translate & summarize foreign articles (placeholder)."""
    if not DEEPSEEK_API_KEY:
        return {"title": title, "summary": content[:200] + "..."}
    # DeepSeek integration would go here
    return {"title": title, "summary": content[:200] + "..."}


async def run_news_crawler() -> list[dict]:
    """Main entry: fetch RSS, crawl details, return structured articles."""
    print("📰 Fetching RSS feeds...")
    articles = await fetch_rss_entries()
    print(f"   Found {len(articles)} articles from RSS")
    
    # Crawl top 5 articles for full content
    for i, article in enumerate(articles[:5]):
        if article["url"]:
            content = await crawl_article_detail(article["url"])
            articles[i]["content"] = content[:3000]
            articles[i]["summary"] = articles[i]["summary"][:300]
    
    return articles


if __name__ == "__main__":
    result = asyncio.run(run_news_crawler())
    print(f"✅ Crawled {len(result)} articles")
    for a in result[:3]:
        print(f"  - [{a['category']}] {a['title']}")
