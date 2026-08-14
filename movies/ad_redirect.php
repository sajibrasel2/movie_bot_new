<?php
/**
 * Ad Redirect Handler
 * Handles click tracking and redirects to ad or target
 */

require_once 'config.php';
require_once 'direct_link_helper.php';

// Get parameters
$adId = isset($_GET['ad']) ? intval($_GET['ad']) : 0;
$targetUrl = isset($_GET['target']) ? $_GET['target'] : '';
$isDirect = isset($_GET['direct']) && $_GET['direct'] == '1';

if ($adId <= 0) {
    // No ad, redirect to target or home
    if ($targetUrl) {
        header('Location: ' . $targetUrl);
    } else {
        header('Location: /');
    }
    exit;
}

// Get ad details
$conn = getDBConnection();
$stmt = $conn->prepare("SELECT * FROM direct_link_ads WHERE id = :id AND is_active = 1");
$stmt->execute(['id' => $adId]);
$ad = $stmt->fetch();

if (!$ad) {
    // Ad not found or inactive, redirect to target
    if ($targetUrl) {
        header('Location: ' . $targetUrl);
    } else {
        header('Location: /');
    }
    exit;
}

// Track click
trackDirectLinkClick($adId);

// Redirect to ad network
header('Location: ' . $ad['redirect_url']);
exit;
