<?php
// =====================================================
// Track Download API
// Tracks which download source was clicked
// =====================================================

require_once '../config.php';

header('Content-Type: application/json');

// Only accept POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['success' => false, 'message' => 'Method not allowed']);
    exit;
}

// Get JSON input
$input = json_decode(file_get_contents('php://input'), true);
$movieId = $input['movie_id'] ?? null;
$source = $input['source'] ?? null;

if (!$movieId || !$source) {
    echo json_encode(['success' => false, 'message' => 'Missing parameters']);
    exit;
}

try {
    // Log the download (this can be expanded to store in a downloads table)
    error_log("Download tracked: Movie ID {$movieId}, Source: {$source}");
    
    echo json_encode([
        'success' => true,
        'message' => 'Download tracked successfully'
    ]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'message' => 'Tracking failed'
    ]);
}
