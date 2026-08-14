<?php
// =====================================================
// Database Migration Script
// Generates slugs for existing movies without slugs
// RUN THIS ONCE to populate slugs for existing movies
// =====================================================

require_once 'config.php';

echo "<!DOCTYPE html><html><head><title>Database Migration</title>";
echo "<style>body{font-family:monospace;background:#141414;color:#fff;padding:20px;}</style></head><body>";
echo "<h2>🎬 Movie Database Migration</h2>";
echo "<p>Generating slugs for existing movies...</p><hr>";

try {
    $conn = getDBConnection();
    
    // Get all movies without slugs
    $stmt = $conn->query("
        SELECT id, movie_title 
        FROM mlsbd_movies 
        WHERE slug IS NULL OR slug = ''
    ");
    
    $movies = $stmt->fetchAll();
    $totalMovies = count($movies);
    
    echo "<p>Found {$totalMovies} movies without slugs.</p>";
    
    if ($totalMovies === 0) {
        echo "<p style='color:#10b981;'>✅ All movies already have slugs!</p>";
        echo "</body></html>";
        exit;
    }
    
    $updated = 0;
    $failed = 0;
    
    foreach ($movies as $movie) {
        $slug = generateSlug($movie['movie_title']);
        
        // Check if slug already exists
        $checkStmt = $conn->prepare("SELECT id FROM mlsbd_movies WHERE slug = :slug AND id != :id");
        $checkStmt->execute(['slug' => $slug, 'id' => $movie['id']]);
        
        // If slug exists, append movie ID
        if ($checkStmt->fetch()) {
            $slug = $slug . '-' . $movie['id'];
        }
        
        try {
            $updateStmt = $conn->prepare("UPDATE mlsbd_movies SET slug = :slug WHERE id = :id");
            $updateStmt->execute(['slug' => $slug, 'id' => $movie['id']]);
            
            echo "<div style='color:#10b981;'>✅ {$movie['id']}: {$movie['movie_title']} → {$slug}</div>";
            $updated++;
        } catch (Exception $e) {
            echo "<div style='color:#ef4444;'>❌ Failed: {$movie['movie_title']} - {$e->getMessage()}</div>";
            $failed++;
        }
    }
    
    echo "<hr>";
    echo "<p><strong>Summary:</strong></p>";
    echo "<ul>";
    echo "<li style='color:#10b981;'>✅ Updated: {$updated}</li>";
    echo "<li style='color:#ef4444;'>❌ Failed: {$failed}</li>";
    echo "</ul>";
    
    if ($updated > 0) {
        echo "<p style='color:#10b981;font-weight:bold;'>✅ Migration completed successfully!</p>";
        echo "<p><a href='/' style='color:#E50914;'>Go to Movie Website</a></p>";
    }
    
} catch (Exception $e) {
    echo "<p style='color:#ef4444;'>❌ Database error: " . $e->getMessage() . "</p>";
}

echo "</body></html>";
