<?php
/**
 * API: Track ad click with detailed logging
 */

require_once 'config.php';

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode(['success' => false, 'message' => 'Invalid method']);
    exit;
}

$data = json_decode(file_get_contents('php://input'), true);
$adId = isset($data['ad_id']) ? intval($data['ad_id']) : 0;
$context = isset($data['context']) ? $data['context'] : 'unknown';

if ($adId <= 0) {
    echo json_encode(['success' => false, 'message' => 'Invalid ad ID']);
    exit;
}

try {
    $conn = getDBConnection();
    
    // Get user info
    $userIp = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    $userAgent = $_SERVER['HTTP_USER_AGENT'] ?? 'unknown';
    
    // Check if we need to reset today_clicks
    $stmt = $conn->prepare("
        SELECT last_reset_date FROM direct_link_ads WHERE id = :id
    ");
    $stmt->execute(['id' => $adId]);
    $ad = $stmt->fetch();
    
    $today = date('Y-m-d');
    $needsReset = !$ad || $ad['last_reset_date'] != $today;
    
    if ($needsReset) {
        // Reset today_clicks for this ad
        $stmt = $conn->prepare("
            UPDATE direct_link_ads 
            SET today_clicks = 1, 
                last_reset_date = :today,
                click_count = click_count + 1
            WHERE id = :id
        ");
        $stmt->execute(['id' => $adId, 'today' => $today]);
    } else {
        // Increment both counters
        $stmt = $conn->prepare("
            UPDATE direct_link_ads 
            SET click_count = click_count + 1,
                today_clicks = today_clicks + 1
            WHERE id = :id
        ");
        $stmt->execute(['id' => $adId]);
    }
    
    // Log detailed click
    $stmt = $conn->prepare("
        INSERT INTO ad_click_logs (ad_id, user_ip, user_agent, context)
        VALUES (:ad_id, :ip, :agent, :context)
    ");
    $stmt->execute([
        'ad_id' => $adId,
        'ip' => $userIp,
        'agent' => substr($userAgent, 0, 500),
        'context' => $context
    ]);
    
    echo json_encode(['success' => true]);
    
} catch (Exception $e) {
    echo json_encode(['success' => false, 'message' => $e->getMessage()]);
}
