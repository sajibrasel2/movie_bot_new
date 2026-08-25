-- =====================================================
-- News Queue Table
-- Bangladesh News Scraper + Facebook Auto Poster
-- =====================================================
-- Run once on server:
-- mysql -u techandc_bot -p'12345Sajibs6@' techandc_prompts < news_schema.sql
-- =====================================================

CREATE TABLE IF NOT EXISTS news_queue (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    url_hash    VARCHAR(64) UNIQUE NOT NULL COMMENT 'MD5 of news URL - prevents duplicates',
    title       TEXT NOT NULL,
    summary     TEXT,
    source      VARCHAR(200),
    news_url    TEXT,
    image_url   TEXT,
    published   VARCHAR(100),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
