-- Create categories table
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

-- Create movie-category relationship table (many-to-many)
CREATE TABLE IF NOT EXISTS movie_category_links (
    id INT AUTO_INCREMENT PRIMARY KEY,
    movie_id INT NOT NULL,
    category_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (movie_id) REFERENCES mlsbd_movies(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES movie_categories(id) ON DELETE CASCADE,
    UNIQUE KEY unique_movie_category (movie_id, category_id),
    INDEX idx_movie (movie_id),
    INDEX idx_category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default categories based on MLSBD structure
INSERT INTO movie_categories (category_name, category_slug, description, icon, display_order) VALUES
('Bengali Movies', 'bengali-movies', 'Latest Bengali movies in HD quality', 'fa-language', 1),
('Hindi Movies', 'hindi-movies', 'Bollywood and Hindi dubbed movies', 'fa-film', 2),
('English Movies', 'english-movies', 'Hollywood movies and English films', 'fa-video', 3),
('Tamil Movies', 'tamil-movies', 'Tamil movies and dubbed versions', 'fa-film', 4),
('Telugu Movies', 'telugu-movies', 'Telugu movies in HD quality', 'fa-film', 5),
('Web Series', 'web-series', 'Latest web series from various platforms', 'fa-tv', 6),
('Dual Audio', 'dual-audio', 'Dual audio movies (Hindi-English, Hindi-Tamil)', 'fa-language', 7),
('720p HD', '720p-hd', 'Movies in 720p HD quality', 'fa-hd-video', 8),
('1080p Full HD', '1080p-full-hd', 'Movies in 1080p Full HD quality', 'fa-film', 9),
('4K Ultra HD', '4k-ultra-hd', 'Movies in 4K Ultra HD quality', 'fa-crown', 10),
('Action', 'action', 'Action and adventure movies', 'fa-explosion', 11),
('Comedy', 'comedy', 'Comedy and funny movies', 'fa-face-laugh', 12),
('Drama', 'drama', 'Drama and emotional movies', 'fa-masks-theater', 13),
('Horror', 'horror', 'Horror and thriller movies', 'fa-ghost', 14),
('Romance', 'romance', 'Romantic movies', 'fa-heart', 15)
ON DUPLICATE KEY UPDATE display_order=VALUES(display_order);

-- Add category extraction columns to mlsbd_movies if not exists
ALTER TABLE mlsbd_movies 
ADD COLUMN IF NOT EXISTS detected_categories TEXT COMMENT 'JSON array of auto-detected categories',
ADD COLUMN IF NOT EXISTS language VARCHAR(50),
ADD COLUMN IF NOT EXISTS genre VARCHAR(100);
