<?php
// =====================================================
// Movie Website Configuration
// Domain: movies.techandclick.site
// =====================================================

// Auto-detect environment (local vs production)
$isLocal = (isset($_SERVER['SERVER_NAME']) && $_SERVER['SERVER_NAME'] === 'localhost')
        || php_uname('n') === 'localhost'
        || file_exists('C:/xampp');

// Database Configuration
define('DB_HOST', 'localhost');
define('DB_USER', $isLocal ? 'root' : 'techandc_bot');
define('DB_PASS', $isLocal ? '' : '12345Sajibs6@');
define('DB_NAME', 'techandc_prompts');

// Site Configuration
define('SITE_NAME', 'TechAndClick Movies');
define('SITE_URL', 'https://movies.techandclick.site');
define('SITE_DESCRIPTION', 'Watch and Download Latest Movies in HD Quality');

// Paths
define('ASSETS_URL', SITE_URL . '/assets');
define('API_URL', SITE_URL . '/api');

// Database Connection
function getDBConnection() {
    static $conn = null;
    
    if ($conn === null) {
        try {
            $conn = new PDO(
                "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4",
                DB_USER,
                DB_PASS,
                [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                    PDO::ATTR_EMULATE_PREPARES => false
                ]
            );
        } catch (PDOException $e) {
            error_log("Database connection failed: " . $e->getMessage());
            die("Database connection error. Please try again later.");
        }
    }
    
    return $conn;
}

// Helper Functions
function generateSlug($title) {
    // Remove special characters and convert to lowercase
    $slug = strtolower($title);
    $slug = preg_replace('/[^a-z0-9\s-]/', '', $slug);
    $slug = preg_replace('/[\s-]+/', '-', $slug);
    $slug = trim($slug, '-');
    return $slug;
}

function formatBytes($bytes, $precision = 2) {
    if ($bytes == 0) return '0 B';
    $units = ['B', 'KB', 'MB', 'GB', 'TB'];
    $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
    $pow = min($pow, count($units) - 1);
    $bytes /= (1 << (10 * $pow));
    return round($bytes, $precision) . ' ' . $units[$pow];
}

function timeAgo($datetime) {
    $timestamp = strtotime($datetime);
    $diff = time() - $timestamp;
    
    if ($diff < 60) {
        return $diff . ' seconds ago';
    } elseif ($diff < 3600) {
        return floor($diff / 60) . ' minutes ago';
    } elseif ($diff < 86400) {
        return floor($diff / 3600) . ' hours ago';
    } elseif ($diff < 2592000) {
        return floor($diff / 86400) . ' days ago';
    } elseif ($diff < 31536000) {
        return floor($diff / 2592000) . ' months ago';
    } else {
        return floor($diff / 31536000) . ' years ago';
    }
}

function getMovieBySlug($slug) {
    $conn = getDBConnection();
    $stmt = $conn->prepare("
        SELECT * FROM mlsbd_movies 
        WHERE slug = :slug 
        LIMIT 1
    ");
    $stmt->execute(['slug' => $slug]);
    return $stmt->fetch();
}

function incrementViewCount($movieId) {
    $conn = getDBConnection();
    $stmt = $conn->prepare("
        UPDATE mlsbd_movies 
        SET view_count = view_count + 1 
        WHERE id = :id
    ");
    $stmt->execute(['id' => $movieId]);
}

function getRecentMovies($limit = 12) {
    $conn = getDBConnection();
    $stmt = $conn->prepare("
        SELECT id, movie_title, slug, poster_url, quality, movie_size_readable, 
               created_at, view_count, year, available_qualities
        FROM mlsbd_movies 
        WHERE poster_url IS NOT NULL
        ORDER BY created_at DESC 
        LIMIT :limit
    ");
    $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
    $stmt->execute();
    return $stmt->fetchAll();
}

function getFeaturedMovies($limit = 6) {
    $conn = getDBConnection();
    $stmt = $conn->prepare("
        SELECT id, movie_title, slug, poster_url, quality, movie_size_readable, 
               created_at, view_count, year, available_qualities
        FROM mlsbd_movies 
        WHERE poster_url IS NOT NULL AND is_featured = 1
        ORDER BY created_at DESC 
        LIMIT :limit
    ");
    $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
    $stmt->execute();
    return $stmt->fetchAll();
}

function searchMovies($query, $limit = 20) {
    $conn = getDBConnection();
    $stmt = $conn->prepare("
        SELECT id, movie_title, slug, poster_url, quality, movie_size_readable, 
               created_at, view_count, year
        FROM mlsbd_movies 
        WHERE poster_url IS NOT NULL
        AND (movie_title LIKE :query OR slug LIKE :query)
        ORDER BY created_at DESC 
        LIMIT :limit
    ");
    $searchTerm = '%' . $query . '%';
    $stmt->bindValue(':query', $searchTerm, PDO::PARAM_STR);
    $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
    $stmt->execute();
    return $stmt->fetchAll();
}

// Category Functions
function getAllCategories() {
    $conn = getDBConnection();
    $stmt = $conn->prepare("
        SELECT c.*, COUNT(mcl.movie_id) as movie_count
        FROM movie_categories c
        LEFT JOIN movie_category_links mcl ON c.id = mcl.category_id
        WHERE c.is_active = 1
        GROUP BY c.id
        ORDER BY c.display_order ASC
    ");
    $stmt->execute();
    return $stmt->fetchAll();
}

function getCategoryBySlug($slug) {
    $conn = getDBConnection();
    $stmt = $conn->prepare("
        SELECT * FROM movie_categories 
        WHERE category_slug = :slug AND is_active = 1
        LIMIT 1
    ");
    $stmt->execute(['slug' => $slug]);
    return $stmt->fetch();
}

function getMoviesByCategory($categorySlug, $limit = 24, $offset = 0) {
    $conn = getDBConnection();
    $stmt = $conn->prepare("
        SELECT m.id, m.movie_title, m.slug, m.poster_url, m.quality, 
               m.movie_size_readable, m.created_at, m.view_count, m.year, m.available_qualities
        FROM mlsbd_movies m
        INNER JOIN movie_category_links mcl ON m.id = mcl.movie_id
        INNER JOIN movie_categories c ON mcl.category_id = c.id
        WHERE c.category_slug = :slug 
         
        AND m.poster_url IS NOT NULL
        ORDER BY m.created_at DESC 
        LIMIT :limit OFFSET :offset
    ");
    $stmt->bindValue(':slug', $categorySlug, PDO::PARAM_STR);
    $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
    $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
    $stmt->execute();
    return $stmt->fetchAll();
}

function getMovieCategoryCount($categorySlug) {
    $conn = getDBConnection();
    $stmt = $conn->prepare("
        SELECT COUNT(DISTINCT m.id) as total
        FROM mlsbd_movies m
        INNER JOIN movie_category_links mcl ON m.id = mcl.movie_id
        INNER JOIN movie_categories c ON mcl.category_id = c.id
        WHERE c.category_slug = :slug 
         
        AND m.poster_url IS NOT NULL
    ");
    $stmt->execute(['slug' => $categorySlug]);
    $result = $stmt->fetch();
    return $result ? $result['total'] : 0;
}


