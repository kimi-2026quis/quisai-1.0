-- Additional tables for crawler data

-- Fashion News (crawled from RSS)
CREATE TABLE IF NOT EXISTS fashion_news (
  id VARCHAR(36) DEFAULT gen_random_uuid() PRIMARY KEY,
  title VARCHAR(500) NOT NULL,
  summary TEXT,
  content TEXT,
  category VARCHAR(50) DEFAULT '时尚资讯',
  source VARCHAR(200),
  source_url VARCHAR(1000),
  image_url VARCHAR(1000),
  tags JSONB DEFAULT '[]',
  is_hot BOOLEAN DEFAULT false,
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS fashion_news_category_idx ON fashion_news (category);
CREATE INDEX IF NOT EXISTS fashion_news_published_idx ON fashion_news (published_at DESC);

-- Monitor Data (competitor tracking snapshots)
CREATE TABLE IF NOT EXISTS monitor_data (
  id VARCHAR(36) DEFAULT gen_random_uuid() PRIMARY KEY,
  brand_name VARCHAR(128) NOT NULL,
  platform VARCHAR(50) NOT NULL,
  data JSONB NOT NULL DEFAULT '{}',
  captured_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS monitor_data_brand_idx ON monitor_data (brand_name);
CREATE INDEX IF NOT EXISTS monitor_data_captured_idx ON monitor_data (captured_at DESC);
