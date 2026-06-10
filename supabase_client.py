"""Supabase database client wrapper"""
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY

_supabase: Client | None = None


def get_client() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase


def save_fashion_news(articles: list[dict]) -> int:
    """Save news articles to Supabase. Returns count saved."""
    client = get_client()
    saved = 0
    for article in articles:
        # Check if article already exists by title hash
        existing = client.table("fashion_news").select("id").eq("title", article["title"]).execute()
        if existing.data:
            continue
        client.table("fashion_news").insert({
            "title": article.get("title", ""),
            "summary": article.get("summary", ""),
            "content": article.get("content", ""),
            "category": article.get("category", "时尚资讯"),
            "source": article.get("source", ""),
            "source_url": article.get("url", ""),
            "image_url": article.get("image_url", ""),
            "published_at": article.get("published_at"),
            "tags": article.get("tags", []),
            "is_hot": article.get("is_hot", False),
        }).execute()
        saved += 1
    return saved


def save_monitor_data(brand: str, platform: str, data: dict) -> None:
    """Save competitor monitoring data."""
    client = get_client()
    client.table("monitor_data").insert({
        "brand_name": brand,
        "platform": platform,
        "data": data,
    }).execute()


def save_analysis_report(keyword: str, platform: str, report: dict) -> None:
    """Save an analysis report."""
    client = get_client()
    client.table("reports").insert({
        "keyword": keyword,
        "platform": platform,
        "result_data": report,
        "points_consumed": report.get("points_consumed", 0),
        "status": "completed",
    }).execute()
