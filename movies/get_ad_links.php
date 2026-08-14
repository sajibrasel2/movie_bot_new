<?php
/**
 * API: Get active direct link ads for JavaScript
 */

require_once 'config.php';

header('Content-Type: application/json');

try {
    $conn = getDBConnection();
    
    // Check if direct links are enabled
    $stmt = $conn->prepare("
        SELECT setting_value 
        FROM movie_ads_settings 
        WHERE setting_key = 'direct_link_enabled'
    ");
    $stmt->execute();
    $result = $stmt->fetch();
    
    if (!$result || $result['setting_value'] != '1') {
        echo json_encode([]);
        exit;
    }
    
    // Get active ads
    $stmt = $conn->prepare("
        SELECT id, redirect_url as url, ad_name, display_priority
        FROM direct_link_ads 
        WHERE is_active = 1 
        ORDER BY display_priority DESC
    ");
    $stmt->execute();
    $ads = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($ads);
    
} catch (Exception $e) {
    echo json_encode([]);
}
