<?php
/**
 * Ads Helper Functions
 * Display ads from dashboard configuration
 */

// Get ads configuration from database
function getAdsByPlacement($placement, $page_type = 'homepage') {
    static $cache = [];
    $cache_key = $placement . '_' . $page_type;
    
    if (isset($cache[$cache_key])) {
        return $cache[$cache_key];
    }
    
    try {
        $conn = getDBConnection();
        
        // Check if ads are enabled globally
        $stmt = $conn->prepare("
            SELECT setting_value 
            FROM movie_ads_settings 
            WHERE setting_key = 'ads_enabled'
        ");
        $stmt->execute();
        $adsEnabled = $stmt->fetchColumn();
        
        if ($adsEnabled != '1') {
            return [];
        }
        
        // Get ads for this placement
        $pageColumn = 'display_on_' . $page_type;
        
        $stmt = $conn->prepare("
            SELECT * FROM movie_ads_config 
            WHERE placement = :placement 
            AND is_active = 1
            AND {$pageColumn} = 1
            ORDER BY priority DESC, id ASC
        ");
        $stmt->execute(['placement' => $placement]);
        $ads = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Filter by network status
        $filteredAds = [];
        foreach ($ads as $ad) {
            $networkKey = $ad['ad_network'] . '_enabled';
            $stmt = $conn->prepare("
                SELECT setting_value 
                FROM movie_ads_settings 
                WHERE setting_key = :key
            ");
            $stmt->execute(['key' => $networkKey]);
            $networkEnabled = $stmt->fetchColumn();
            
            if ($networkEnabled == '1' || $ad['ad_network'] == 'custom') {
                $filteredAds[] = $ad;
            }
        }
        
        $cache[$cache_key] = $filteredAds;
        return $filteredAds;
        
    } catch (PDOException $e) {
        error_log("Ads error: " . $e->getMessage());
        return [];
    }
}

// Display ads for a specific placement
function displayAds($placement, $page_type = 'homepage') {
    $ads = getAdsByPlacement($placement, $page_type);
    
    if (empty($ads)) {
        return '';
    }
    
    $output = '';
    foreach ($ads as $ad) {
        $output .= '<div class="ad-container ad-' . htmlspecialchars($ad['ad_type']) . '" data-ad-id="' . $ad['id'] . '">';
        $output .= $ad['ad_code'];
        $output .= '</div>';
        
        // Update impression count (async)
        updateAdImpression($ad['id']);
    }
    
    return $output;
}

// Update ad impression count
function updateAdImpression($adId) {
    // This could be done via AJAX to not slow down page load
    try {
        $conn = getDBConnection();
        $stmt = $conn->prepare("
            UPDATE movie_ads_config 
            SET impressions = impressions + 1,
                last_displayed_at = NOW()
            WHERE id = :id
        ");
        $stmt->execute(['id' => $adId]);
    } catch (PDOException $e) {
        // Silently fail, don't break page
        error_log("Ad impression update error: " . $e->getMessage());
    }
}

// Check if mobile device
function isMobileDevice() {
    return preg_match("/(android|avantgo|blackberry|bolt|boost|cricket|docomo|fone|hiptop|mini|mobi|palm|phone|pie|tablet|up\.browser|up\.link|webos|wos)/i", $_SERVER["HTTP_USER_Agent"] ?? '');
}

// Get ad settings
function getAdSettings() {
    static $settings = null;
    
    if ($settings !== null) {
        return $settings;
    }
    
    try {
        $conn = getDBConnection();
        $stmt = $conn->query("SELECT setting_key, setting_value FROM movie_ads_settings");
        $settings = [];
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            $settings[$row['setting_key']] = $row['setting_value'];
        }
        return $settings;
    } catch (PDOException $e) {
        return [];
    }
}

// Check if ads should be shown on this device
function shouldShowAds() {
    $settings = getAdSettings();
    
    // Check global toggle
    if (($settings['ads_enabled'] ?? '1') != '1') {
        return false;
    }
    
    // Check mobile setting
    if (isMobileDevice() && ($settings['ads_on_mobile'] ?? '1') != '1') {
        return false;
    }
    
    return true;
}
