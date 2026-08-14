<?php
/**
 * Instant Search API
 * Returns JSON results for live search dropdown
 */
require_once __DIR__ . '/../config.php';

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-cache');

$q = trim($_GET['q'] ?? '');

if (strlen($q) < 2) {
    echo json_encode([]);
    exit;
}

try {
    $conn = getDBConnection();
    $stmt = $conn->prepare("
        SELECT id, movie_title, slug, poster_url, quality, year, available_qualities
        FROM mlsbd_movies
        WHERE movie_title LIKE :q1 OR base_movie_title LIKE :q2
        ORDER BY created_at DESC
        LIMIT 8
    ");
    $like = '%' . $q . '%';
    $stmt->bindValue(':q1', $like);
    $stmt->bindValue(':q2', $like);
    $stmt->execute();
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Simplify available_qualities
    foreach ($results as &$r) {
        if (!empty($r['available_qualities'])) {
            $aq = json_decode($r['available_qualities'], true);
            $r['qualities'] = is_array($aq) ? $aq : [$r['quality']];
        } else {
            $r['qualities'] = [$r['quality']];
        }
        unset($r['available_qualities']);
    }

    echo json_encode($results);
} catch (Exception $e) {
    echo json_encode(['error' => $e->getMessage(), 'results' => []]);
}
