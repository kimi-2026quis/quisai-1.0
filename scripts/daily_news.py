"""Run daily: Fetch fashion news and save to Supabase"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.news import run_news_crawler
from supabase_client import save_fashion_news


async def main():
    print("=" * 40)
    print("📰 QuisAI Daily News Crawler")
    print("=" * 40)
    
    articles = await run_news_crawler()
    print(f"\n✅ Crawled {len(articles)} articles")
    
    saved = save_fashion_news(articles)
    print(f"💾 Saved {saved} new articles to database")
    
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
