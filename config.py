"""QuisAI Backend Configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("COZE_SUPABASE_URL", "https://qmucxbbvudypfqfcmntb.supabase.co")
SUPABASE_KEY = os.getenv("COZE_SUPABASE_ANON_KEY", "")

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"

# Crawl4AI
CRAWL4AI_TIMEOUT = 30

# Search
SEARCH_ENGINE = "duckduckgo"  # Free, no API key needed

# News RSS Feeds (working sources as of 2026)
FASHION_RSS_FEEDS = [
    "https://www.wwd.com/rss",
    "https://www.businessoffashion.com/feed",
    # Add more Chinese fashion sources below
    # "https://www.vogue.com/rss",
    # "https://www.harpersbazaar.com/rss",
    # "https://www.thecut.com/rss",
]
