-- =====================================================
-- Ads Management System Database Schema
-- movies.techandclick.site
-- =====================================================

USE techandc_prompts;

-- Create ads configuration table
CREATE TABLE IF NOT EXISTS movie_ads_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Ad identification
    ad_name VARCHAR(100) NOT NULL COMMENT 'Ad name (e.g., Adsterra PopUnder)',
    ad_type ENUM('popunder', 'banner', 'native', 'social_bar', 'interstitial', 'adsense', 'custom') NOT NULL,
    ad_network VARCHAR(50) NOT NULL COMMENT 'adsterra, monetag, adsense, custom',
    
    -- Ad placement
    placement ENUM('header', 'before_poster', 'after_details', 'between_downloads', 'sidebar', 'footer', 'before_content', 'after_content') NOT NULL,
    
    -- Ad code
    ad_code TEXT NOT NULL COMMENT 'Ad script/HTML code',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Enable/disable ad',
    
    -- Display settings
    display_on_homepage BOOLEAN DEFAULT TRUE,
    display_on_movie_page BOOLEAN DEFAULT TRUE,
    display_on_search_page BOOLEAN DEFAULT TRUE,
    
    -- Priority (higher number = higher priority)
    priority INT DEFAULT 0 COMMENT 'Display order priority',
    
    -- Statistics
    impressions INT DEFAULT 0 COMMENT 'Number of times displayed',
    last_displayed_at DATETIME DEFAULT NULL,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_placement (placement),
    INDEX idx_active (is_active),
    INDEX idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create global ads settings table
CREATE TABLE IF NOT EXISTS movie_ads_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    description VARCHAR(500),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default settings
INSERT INTO movie_ads_settings (setting_key, setting_value, description) VALUES
('ads_enabled', '1', 'Master switch for all ads (0=off, 1=on)'),
('adsterra_enabled', '1', 'Enable/disable Adsterra ads'),
('monetag_enabled', '1', 'Enable/disable Monetag ads'),
('adsense_enabled', '1', 'Enable/disable Google AdSense'),
('custom_ads_enabled', '1', 'Enable/disable custom ads'),
('ads_on_mobile', '1', 'Show ads on mobile devices'),
('ads_delay_seconds', '0', 'Delay before showing ads (seconds)')
ON DUPLICATE KEY UPDATE setting_key=setting_key;

-- Insert sample ad configurations
INSERT INTO movie_ads_config (ad_name, ad_type, ad_network, placement, ad_code, is_active, display_on_homepage, display_on_movie_page, priority) VALUES
('Adsterra PopUnder', 'popunder', 'adsterra', 'header', '<!-- Adsterra PopUnder Code -->\n<script type="text/javascript">\natOptions = {\n\t"key" : "YOUR_ADSTERRA_KEY",\n\t"format" : "iframe",\n\t"height" : 60,\n\t"width" : 468\n};\n</script>\n<script type="text/javascript" src="//www.topcreativeformat.com/YOUR_ADSTERRA_KEY/invoke.js"></script>', TRUE, TRUE, TRUE, 100),

('Adsterra Banner Top', 'banner', 'adsterra', 'before_poster', '<!-- Adsterra Banner -->\n<script type="text/javascript">\natOptions = {\n\t"key" : "YOUR_BANNER_KEY",\n\t"format" : "iframe",\n\t"height" : 250,\n\t"width" : 300\n};\n</script>\n<script type="text/javascript" src="//www.topcreativeformat.com/YOUR_BANNER_KEY/invoke.js"></script>', FALSE, FALSE, TRUE, 90),

('Monetag Social Bar', 'social_bar', 'monetag', 'footer', '<!-- Monetag Social Bar -->\n<script src="https://alwingulla.com/88/tag.min.js" data-zone="YOUR_ZONE_ID" async data-cfasync="false"></script>', FALSE, TRUE, TRUE, 80),

('Google AdSense Display', 'adsense', 'adsense', 'after_details', '<!-- Google AdSense -->\n<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>\n<ins class="adsbygoogle"\n     style="display:block"\n     data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"\n     data-ad-slot="XXXXXXXXXX"\n     data-ad-format="auto"\n     data-full-width-responsive="true"></ins>\n<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>', FALSE, TRUE, TRUE, 70)
ON DUPLICATE KEY UPDATE ad_name=ad_name;

-- Show created tables
SHOW TABLES LIKE 'movie_ads%';

SELECT 'Ads tables created successfully!' AS Status;
