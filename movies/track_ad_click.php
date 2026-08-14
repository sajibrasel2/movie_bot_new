<?php
/**
 * Track ad click — increments click_count and logs the click
 */

require_once 'config.php';

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode(['ok' => false]);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
$adId   = isset($input['ad_id'])  ? intval($input['ad_id'])  : 0;
$context = isset($input['context']) ? substr(trim($input['context']), 0, 100) : 'download';

try {
    $conn = getDBConnection();

    if ($adId > 0) {
        // Increment total click count
        $stmt = $conn->prepare("UPDATE direct_link_ads SET click_count = click_count + 1 WHERE id = :id");
        $stmt->execute(['id' => $adId]);

        // Reset today_clicks if date changed
        $stmt = $conn->prepare("
            UPDATE direct_link_ads
            SET today_clicks = 0, last_reset_date = CURDATE()
            WHERE id = :id AND (last_reset_date IS NULL OR last_reset_date < CURDATE())
        ");
        $stmt->execute(['id' => $adId]);

        // Increment today_clicks
        $stmt = $conn->prepare("UPDATE direct_link_ads SET today_clicks = today_clicks + 1 WHERE id = :id");
        $stmt->execute(['id' => $adId]);

        // Log click detail (if table exists)
        $chk = $conn->query("SHOW TABLES LIKE 'ad_click_logs'");
        if ($chk->rowCount() > 0) {
            $stmt = $conn->prepare("
                INSERT INTO ad_click_logs (ad_id, user_ip, user_agent, context)
                VALUES (:ad_id, :ip, :ua, :ctx)
            ");
            $stmt->execute([
                'ad_id' => $adId,
                'ip'    => $_SERVER['REMOTE_ADDR'] ?? '',
                'ua'    => substr($_SERVER['HTTP_USER_AGENT'] ?? '', 0, 255),
                'ctx'   => $context,
            ]);
        }
    }

    echo json_encode(['ok' => true]);

} catch (Exception $e) {
    echo json_encode(['ok' => false]);
}
