"""Supabase database client wrapper"""
import json
import os
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY

_supabase: Client | None = None
_supabase_admin: Client | None = None


def get_client() -> Client:
    """Get client with anon key (read-only for RLS-protected tables)."""
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase


def get_admin_client() -> Client:
    """Get client with service_role key (bypasses RLS, for writes)."""
    global _supabase_admin
    if _supabase_admin is None:
        service_key = os.getenv("COZE_SUPABASE_SERVICE_KEY")
        if service_key:
            _supabase_admin = create_client(SUPABASE_URL, service_key)
        else:
            _supabase_admin = get_client()
    return _supabase_admin


def save_fashion_news(articles: list[dict]) -> int:
    """Save news articles to Supabase. Returns count saved."""
    client = get_admin_client()
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
    client = get_admin_client()
    client.table("monitor_data").insert({
        "brand_name": brand,
        "platform": platform,
        "data": data,
    }).execute()


def save_analysis_report(keyword: str, platform: str, report: dict) -> None:
    """Save an analysis report to fashion_news table."""
    from datetime import datetime
    client = get_admin_client()
    # Save as a news entry with analysis data
    client.table("fashion_news").insert({
        "title": f"📊 趋势分析：{keyword}",
        "summary": json.dumps(report.get("analysis", {}), ensure_ascii=False)[:500],
        "content": json.dumps(report, ensure_ascii=False),
        "category": "趋势分析",
        "source": f"QuisAI分析/{platform}",
        "source_url": report.get("products", [{}])[0].get("url", "") if report.get("products") else "",
        "tags": [keyword, "趋势分析", platform],
        "is_hot": True,
        "published_at": datetime.now().isoformat(),
    }).execute()
