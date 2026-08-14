<?php
/**
 * Direct Link Ads Helper
 * Handles redirect ads on clickable buttons
 */

// Only load movies config if not already loaded (dashboard has its own config)
if (!function_exists('getDBConnection')) {
    require_once __DIR__ . '/config.php';
}

/**
 * Get a random active direct link ad
 * 
 * @return array|null Ad details or null if none active
 */
function getDirectLinkAd() {
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
        return null;
    }
    
    // Get rotation strategy
    $stmt = $conn->prepare("
        SELECT setting_value 
        FROM movie_ads_settings 
        WHERE setting_key = 'direct_link_rotation'
    ");
    $stmt->execute();
    $rotation = $stmt->fetch();
    $strategy = $rotation ? $rotation['setting_value'] : 'random';
    
    // Get active ads based on strategy
    if ($strategy === 'priority') {
        // Weighted random by priority
        $stmt = $conn->prepare("
            SELECT * FROM direct_link_ads 
            WHERE is_active = 1 
            ORDER BY display_priority DESC, RAND() 
            LIMIT 1
        ");
    } else {
        // Pure random
        $stmt = $conn->prepare("
            SELECT * FROM direct_link_ads 
            WHERE is_active = 1 
            ORDER BY RAND() 
            LIMIT 1
        ");
    }
    
    $stmt->execute();
    return $stmt->fetch();
}

/**
 * Get all direct link ads (for management)
 * 
 * @return array All ads
 */
function getAllDirectLinkAds() {
    $conn = getDBConnection();
    $stmt = $conn->prepare("
        SELECT * FROM direct_link_ads 
        ORDER BY display_priority DESC, created_at DESC
    ");
    $stmt->execute();
    return $stmt->fetchAll();
}

/**
 * Track ad click
 * 
 * @param int $adId Ad ID
 */
function trackDirectLinkClick($adId) {
    $conn = getDBConnection();
    $stmt = $conn->prepare("
        UPDATE direct_link_ads 
        SET click_count = click_count + 1 
        WHERE id = :id
    ");
    $stmt->execute(['id' => $adId]);
}

/**
 * Wrap URL with ad redirect
 * 
 * @param string $targetUrl Final destination URL
 * @param string $context Context (download, poster_click, etc)
 * @return string URL to use (either direct or via redirect)
 */
function wrapWithAdRedirect($targetUrl, $context = 'download') {
    $ad = getDirectLinkAd();
    
    if (!$ad) {
        return $targetUrl;
    }
    
    // Return redirect URL with target encoded
    return '/ad_redirect.php?ad=' . $ad['id'] . '&target=' . urlencode($targetUrl) . '&ctx=' . urlencode($context);
}

/**
 * Get direct ad link (for direct redirect buttons)
 * 
 * @return string|null Ad redirect URL or null
 */
function getDirectAdLink() {
    $ad = getDirectLinkAd();
    
    if (!$ad) {
        return null;
    }
    
    return '/ad_redirect.php?ad=' . $ad['id'] . '&direct=1';
}

/**
 * Check if direct links are enabled
 * 
 * @return bool
 */
function directLinksEnabled() {
    $conn = getDBConnection();
    $stmt = $conn->prepare("
        SELECT setting_value 
        FROM movie_ads_settings 
        WHERE setting_key = 'direct_link_enabled'
    ");
    $stmt->execute();
    $result = $stmt->fetch();
    
    return $result && $result['setting_value'] == '1';
}
