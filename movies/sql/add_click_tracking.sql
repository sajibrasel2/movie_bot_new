-- Add detailed click tracking
CREATE TABLE IF NOT EXISTS ad_click_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ad_id INT NOT NULL,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_ip VARCHAR(45),
    user_agent TEXT,
    context VARCHAR(100) COMMENT 'download, search, movie_card, etc',
    INDEX idx_ad_id (ad_id),
    INDEX idx_date (clicked_at),
    FOREIGN KEY (ad_id) REFERENCES direct_link_ads(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add today_clicks column for quick access
ALTER TABLE direct_link_ads
ADD COLUMN IF NOT EXISTS today_clicks INT DEFAULT 0 COMMENT 'Clicks today (reset daily)',
ADD COLUMN IF NOT EXISTS last_reset_date DATE COMMENT 'Last date when today_clicks was reset';
