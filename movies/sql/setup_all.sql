-- ============================================
-- COMPLETE DATABASE SETUP (MySQL 5.6+ Compatible)
-- ============================================

-- 1. movie_categories table
CREATE TABLE IF NOT EXISTS movie_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    category_slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50) DEFAULT 'fa-film',
    display_order INT DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_slug (category_slug),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. movie_category_links table
CREATE TABLE IF NOT EXISTS movie_category_links (
    id INT AUTO_INCREMENT PRIMARY KEY,
    movie_id INT NOT NULL,
    category_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_movie_category (movie_id, category_id),
    INDEX idx_movie (movie_id),
    INDEX idx_category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. direct_link_ads table
CREATE TABLE IF NOT EXISTS direct_link_ads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ad_name VARCHAR(100) NOT NULL,
    ad_network VARCHAR(50) NOT NULL,
    redirect_url TEXT NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    click_count INT DEFAULT 0,
    today_clicks INT DEFAULT 0,
    last_reset_date DATE,
    display_priority INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (is_active),
    INDEX idx_priority (display_priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. ad_click_logs table
CREATE TABLE IF NOT EXISTS ad_click_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ad_id INT NOT NULL,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_ip VARCHAR(45),
    user_agent TEXT,
    context VARCHAR(100),
    INDEX idx_ad_id (ad_id),
    INDEX idx_date (clicked_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. movie_ads_settings table
CREATE TABLE IF NOT EXISTS movie_ads_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Add columns to mlsbd_movies (using stored procedure to skip if exists)
DROP PROCEDURE IF EXISTS add_column_if_not_exists;
DELIMITER //
CREATE PROCEDURE add_column_if_not_exists(
    IN tbl VARCHAR(100),
    IN col VARCHAR(100),
    IN col_def VARCHAR(200)
)
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = tbl
        AND COLUMN_NAME = col
    ) THEN
        SET @sql = CONCAT('ALTER TABLE `', tbl, '` ADD COLUMN `', col, '` ', col_def);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END //
DELIMITER ;

CALL add_column_if_not_exists('mlsbd_movies', 'detected_categories', 'TEXT');
CALL add_column_if_not_exists('mlsbd_movies', 'language', 'VARCHAR(50)');
CALL add_column_if_not_exists('mlsbd_movies', 'genre', 'VARCHAR(100)');
CALL add_column_if_not_exists('mlsbd_movies', 'available_qualities', 'TEXT');
CALL add_column_if_not_exists('mlsbd_movies', 'base_movie_title', 'VARCHAR(500)');
CALL add_column_if_not_exists('mlsbd_movies', 'quality_variants', 'TEXT');
CALL add_column_if_not_exists('mlsbd_movies', 'movie_slug', 'VARCHAR(300)');
CALL add_column_if_not_exists('mlsbd_movies', 'poster_url', 'TEXT');
CALL add_column_if_not_exists('mlsbd_movies', 'website_posted', 'TINYINT(1) DEFAULT 0');

DROP PROCEDURE IF EXISTS add_column_if_not_exists;

-- 7. Insert default categories
INSERT IGNORE INTO movie_categories (category_name, category_slug, description, icon, display_order) VALUES
('Bengali Movies', 'bengali-movies', 'Latest Bengali movies in HD quality', 'fa-language', 1),
('Hindi Movies', 'hindi-movies', 'Bollywood and Hindi dubbed movies', 'fa-film', 2),
('English Movies', 'english-movies', 'Hollywood movies and English films', 'fa-video', 3),
('Tamil Movies', 'tamil-movies', 'Tamil movies and dubbed versions', 'fa-film', 4),
('Telugu Movies', 'telugu-movies', 'Telugu movies in HD quality', 'fa-film', 5),
('Web Series', 'web-series', 'Latest web series from various platforms', 'fa-tv', 6),
('Dual Audio', 'dual-audio', 'Dual audio movies (Hindi-English, Hindi-Tamil)', 'fa-language', 7),
('720p HD', '720p-hd', 'Movies in 720p HD quality', 'fa-film', 8),
('1080p Full HD', '1080p-full-hd', 'Movies in 1080p Full HD quality', 'fa-film', 9),
('4K Ultra HD', '4k-ultra-hd', 'Movies in 4K Ultra HD quality', 'fa-crown', 10),
('480p Movies', '480p', 'Movies in 480p quality', 'fa-film', 11),
('Action', 'action', 'Action and adventure movies', 'fa-bolt', 12),
('Comedy', 'comedy', 'Comedy and funny movies', 'fa-face-laugh', 13),
('Drama', 'drama', 'Drama and emotional movies', 'fa-masks-theater', 14),
('Horror', 'horror', 'Horror and thriller movies', 'fa-ghost', 15),
('Romance', 'romance', 'Romantic movies', 'fa-heart', 16);

-- 8. Insert ad networks
INSERT IGNORE INTO direct_link_ads (ad_name, ad_network, redirect_url, display_priority) VALUES
('Adsterra Direct Link', 'adsterra', 'https://omg10.com/4/11017767', 10),
('Monetag Direct Link', 'monetag', 'https://www.effectivecpmnetwork.com/mgtqwzbp?key=5c4003e0ae2b0ebd387daded087bc9aa', 10);

-- Update if already exists
UPDATE direct_link_ads SET redirect_url='https://omg10.com/4/11017767', is_active=1 WHERE ad_network='adsterra';
UPDATE direct_link_ads SET redirect_url='https://www.effectivecpmnetwork.com/mgtqwzbp?key=5c4003e0ae2b0ebd387daded087bc9aa', is_active=1 WHERE ad_network='monetag';

-- 9. Insert settings
INSERT IGNORE INTO movie_ads_settings (setting_key, setting_value, description) VALUES
('direct_link_enabled', '1', 'Enable/disable direct link ads'),
('direct_link_rotation', 'random', 'Rotation: random, priority, round-robin');

SELECT 'Database setup complete!' as status;
SHOW TABLES;
