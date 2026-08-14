<?php
/**
 * API: Get active direct link ads for JavaScript click protection
 */

require_once 'config.php';

header('Content-Type: application/json');
header('Cache-Control: no-cache');

try {
    $conn = getDBConnection();

    // Check if direct_link_ads table exists
    $stmt = $conn->query("SHOW TABLES LIKE 'direct_link_ads'");
    if ($stmt->rowCount() === 0) {
        echo json_encode([]);
        exit;
    }

    // Check if ads are enabled in settings
    $stmt = $conn->query("SHOW TABLES LIKE 'movie_ads_settings'");
    if ($stmt->rowCount() > 0) {
        $stmt = $conn->prepare("SELECT setting_value FROM movie_ads_settings WHERE setting_key = 'direct_link_enabled'");
        $stmt->execute();
        $result = $stmt->fetch();
        if ($result && $result['setting_value'] == '0') {
            echo json_encode([]);
            exit;
        }
    }

    // Get all active ads
    $stmt = $conn->prepare("
        SELECT id, ad_name, redirect_url as url, ad_network, display_priority
        FROM direct_link_ads
        WHERE is_active = 1
        ORDER BY display_priority DESC, RAND()
    ");
    $stmt->execute();
    $ads = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($ads);

} catch (Exception $e) {
    echo json_encode([]);
}
