<?php
// =====================================================
// Get Movie API
// Returns movie details by ID or slug
// =====================================================

require_once '../config.php';

header('Content-Type: application/json');

$slug = $_GET['slug'] ?? '';
$id = $_GET['id'] ?? '';

if (empty($slug) && empty($id)) {
    http_response_code(400);
    echo json_encode(['success' => false, 'message' => 'Missing slug or id parameter']);
    exit;
}

try {
    $conn = getDBConnection();
    
    if (!empty($slug)) {
        $stmt = $conn->prepare("
            SELECT * FROM mlsbd_movies 
            WHERE slug = :slug AND status = 'completed'
            LIMIT 1
        ");
        $stmt->execute(['slug' => $slug]);
    } else {
        $stmt = $conn->prepare("
            SELECT * FROM mlsbd_movies 
            WHERE id = :id AND status = 'completed'
            LIMIT 1
        ");
        $stmt->execute(['id' => $id]);
    }
    
    $movie = $stmt->fetch();
    
    if ($movie) {
        // Parse download links
        if (!empty($movie['download_links'])) {
            $movie['download_links'] = json_decode($movie['download_links'], true);
        }
        
        // Parse telegram message IDs
        if (!empty($movie['telegram_message_ids'])) {
            $movie['telegram_message_ids'] = json_decode($movie['telegram_message_ids'], true);
        }
        
        echo json_encode([
            'success' => true,
            'data' => $movie
        ]);
    } else {
        http_response_code(404);
        echo json_encode([
            'success' => false,
            'message' => 'Movie not found'
        ]);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'message' => 'Database error'
    ]);
}
