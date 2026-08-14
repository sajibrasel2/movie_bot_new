-- Add direct link ads table
CREATE TABLE IF NOT EXISTS direct_link_ads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ad_name VARCHAR(100) NOT NULL,
    ad_network VARCHAR(50) NOT NULL COMMENT 'adsterra, monetag, etc',
    redirect_url TEXT NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    click_count INT DEFAULT 0,
    display_priority INT DEFAULT 0 COMMENT 'Higher priority shows more often',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (is_active),
    INDEX idx_priority (display_priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert your ads
INSERT INTO direct_link_ads (ad_name, ad_network, redirect_url, display_priority) VALUES
('Adsterra Direct Link', 'adsterra', 'https://omg10.com/4/11017767', 10),
('Monetag Direct Link', 'monetag', 'https://www.effectivecpmnetwork.com/mgtqwzbp?key=5c4003e0ae2b0ebd387daded087bc9aa', 10);

-- Add global settings for direct link behavior
INSERT INTO movie_ads_settings (setting_key, setting_value, description) VALUES
('direct_link_enabled', '1', 'Enable/disable direct link ads on clickable buttons'),
('direct_link_rotation', 'random', 'Rotation strategy: random, priority, round-robin')
ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value);
