<?php
/**
 * API endpoint: receives movie post data from Telegram bot
 * and stores it in movies.json for the website.
 *
 * POST JSON body:
 *   { "title", "link", "thumbnail", "download_links": [{text,url},...],
 *     "source_name", "source_emoji", "channel_msg_id" }
 *
 * Secret key must match bot config to prevent abuse.
 */

header('Content-Type: application/json; charset=utf-8');

$SECRET = 'tc_movie_2026_secret';
$DATA_FILE = __DIR__ . '/movies.json';

// Only allow POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Read JSON body
$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data || empty($data['title'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing required fields']);
    exit;
}

// Verify secret
if (empty($data['secret']) || $data['secret'] !== $SECRET) {
    http_response_code(403);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

// Remove secret from stored data
unset($data['secret']);

// Generate slug from title
$slug = generate_slug($data['title']);
$data['slug'] = $slug;
$data['posted_at'] = date('c');  // ISO 8601

// Load existing movies
$movies = [];
if (file_exists($DATA_FILE)) {
    $json = file_get_contents($DATA_FILE);
    $movies = json_decode($json, true) ?: [];
}

// De-duplicate: skip if same slug posted within last 24h
$skip = false;
foreach ($movies as $i => $m) {
    if (($m['slug'] ?? '') === $slug) {
        // Update existing entry instead of adding duplicate
        $movies[$i] = array_merge($m, $data);
        $skip = true;
        break;
    }
}
if (!$skip) {
    array_unshift($movies, $data);  // newest first
}

// Remove movies older than 10 days
$movies = cleanup_old_movies($movies);

// Keep max 500 movies
$movies = array_slice($movies, 0, 500);

// Save
file_put_contents($DATA_FILE, json_encode($movies, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));

// Regenerate sitemap for movie pages
generate_movie_sitemap($movies);

echo json_encode(['ok' => true, 'slug' => $slug, 'count' => count($movies)]);


// ── Helper functions ──

function cleanup_old_movies($movies) {
    $ten_days_ago = time() - (10 * 24 * 60 * 60);
    $cleaned = [];
    $removed = 0;
    foreach ($movies as $m) {
        $ts = strtotime($m['posted_at'] ?? 'now');
        if ($ts >= $ten_days_ago) {
            $cleaned[] = $m;
        } else {
            $removed++;
        }
    }
    if ($removed > 0) {
        // Log for debugging (optional)
        error_log("cleanup_old_movies: removed $removed movies older than 10 days");
    }
    return $cleaned;
}

function generate_slug($title) {
    // Remove common brackets/suffixes like [DODI Repack], (2025), etc.
    $t = preg_replace('/[\[\(].*?[\]\)]/', '', $title);
    $t = preg_replace('/[^a-zA-Z0-9\s\-]/', '', $t);
    $t = trim(strtolower($t));
    $t = preg_replace('/\s+/', '-', $t);
    $t = preg_replace('/-+/', '-', $t);
    $t = trim($t, '-');
    if (strlen($t) < 2) {
        $t = 'movie-' . substr(md5($title), 0, 8);
    }
    return $t;
}

function generate_movie_sitemap($movies) {
    $base = 'https://techandclick.site';
    $xml  = '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
    $xml .= '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";

    // Movies listing page
    $xml .= "  <url>\n    <loc>$base/movies.php</loc>\n    <changefreq>daily</changefreq>\n    <priority>0.9</priority>\n  </url>\n";

    foreach ($movies as $m) {
        $slug = htmlspecialchars($m['slug'] ?? '', ENT_XML1);
        if (!$slug) continue;
        $lastmod = substr($m['posted_at'] ?? date('c'), 0, 10);
        $xml .= "  <url>\n    <loc>$base/movie.php?slug=$slug</loc>\n    <lastmod>$lastmod</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n";
    }

    $xml .= "</urlset>\n";
    file_put_contents(__DIR__ . '/sitemap-movies.xml', $xml);
}
