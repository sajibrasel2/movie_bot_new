<?php
require_once 'config.php';
require_once 'ads_helper.php';
require_once 'direct_link_helper.php';

// Get movie slug from URL
$slug = $_GET['slug'] ?? '';

if (empty($slug)) {
    header('Location: /');
    exit;
}

// Get movie details
$movie = getMovieBySlug($slug);

if (!$movie) {
    header('HTTP/1.0 404 Not Found');
    echo '<!DOCTYPE html>
    <html>
    <head>
        <title>Movie Not Found</title>
        <link rel="stylesheet" href="' . ASSETS_URL . '/css/style.css">
    </head>
    <body>
        <div style="text-align: center; padding: 100px 20px;">
            <h1 style="font-size: 3rem; color: #E50914;">404</h1>
            <p style="font-size: 1.5rem; margin: 20px 0;">Movie Not Found</p>
            <a href="/" class="btn btn-primary">Go Home</a>
        </div>
    </body>
    </html>';
    exit;
}

// Increment view count
incrementViewCount($movie['id']);

// Parse download links
$downloadLinks = [];
if (!empty($movie['download_links'])) {
    $downloadLinks = json_decode($movie['download_links'], true) ?? [];
}

// Add GDFlix URL if available
if (!empty($movie['gdflix_url']) && !isset($downloadLinks['gdflix'])) {
    $downloadLinks['gdflix'] = $movie['gdflix_url'];
}

// Page title
$pageTitle = htmlspecialchars($movie['movie_title']) . ' - Download & Watch Online';

// Check if ads should be displayed
$showAds = shouldShowAds();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo $pageTitle; ?></title>
    <meta name="description" content="Download <?php echo htmlspecialchars($movie['movie_title']); ?> in <?php echo htmlspecialchars($movie['quality']); ?> quality. Size: <?php echo htmlspecialchars($movie['movie_size_readable']); ?>">
    
    <!-- Open Graph Meta Tags -->
    <meta property="og:title" content="<?php echo $pageTitle; ?>">
    <meta property="og:description" content="Download <?php echo htmlspecialchars($movie['movie_title']); ?> in high quality">
    <meta property="og:image" content="<?php echo htmlspecialchars($movie['poster_url']); ?>">
    <meta property="og:url" content="<?php echo SITE_URL . '/movie.php?slug=' . htmlspecialchars($slug); ?>">
    <meta property="og:type" content="video.movie">
    
    <!-- Favicon -->
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎬</text></svg>">
    
    <!-- CSS -->
    <link rel="stylesheet" href="/assets/css/style.css">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>

    <!-- Navbar -->
    <nav class="navbar scrolled">
        <div style="display: flex; align-items: center;">
            <a href="/" class="logo">
                <i class="fas fa-film"></i> MOVIES
            </a>
            
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/browse.php?filter=featured">Featured</a>
                <a href="/browse.php?filter=latest">Latest</a>
                
                <!-- Categories Dropdown -->
                <div class="nav-dropdown">
                    <a href="#" class="dropdown-toggle">
                        Categories <i class="fas fa-chevron-down"></i>
                    </a>
                    <div class="dropdown-menu">
                        <?php 
                        $navCategories = getAllCategories();
                        foreach ($navCategories as $cat): 
                            if ($cat['movie_count'] > 0):
                        ?>
                            <a href="/category.php?slug=<?php echo urlencode($cat['category_slug']); ?>">
                                <i class="fas <?php echo htmlspecialchars($cat['icon']); ?>"></i>
                                <?php echo htmlspecialchars($cat['category_name']); ?>
                                <span class="count">(<?php echo $cat['movie_count']; ?>)</span>
                            </a>
                        <?php 
                            endif;
                        endforeach; 
                        ?>
                    </div>
                </div>
                
                <a href="/browse.php?quality=1080p">HD Movies</a>
                <a href="/browse.php?year=2026">2026 Movies</a>
            </div>
        </div>
        
        <form id="searchForm" class="search-box">
            <input type="text" id="searchInput" placeholder="Search movies..." autocomplete="off">
            <button type="submit"><i class="fas fa-search"></i></button>
        </form>
    </nav>

    <!-- Movie Detail Section -->
    <section class="movie-detail">
        <?php if ($showAds): ?>
        <!-- Ad before movie content -->
        <?php echo displayAds('before_poster', 'movie_page'); ?>
        <?php endif; ?>
        
        <div class="movie-header">
            <!-- Movie Poster -->
            <div class="movie-poster-large">
                <img src="<?php echo htmlspecialchars($movie['poster_url']); ?>" 
                     alt="<?php echo htmlspecialchars($movie['movie_title']); ?>">
            </div>
            
            <!-- Movie Info -->
            <div class="movie-info">
                <h1><?php echo htmlspecialchars($movie['movie_title']); ?></h1>
                
                <div class="meta-info">
                    <?php 
                    // Check if multiple qualities available
                    $availableQualities = [];
                    if (!empty($movie['available_qualities'])) {
                        $availableQualities = json_decode($movie['available_qualities'], true);
                    }
                    
                    if (!empty($availableQualities) && is_array($availableQualities)):
                        // Show all available qualities
                        foreach ($availableQualities as $q):
                    ?>
                        <span class="quality"><?php echo htmlspecialchars($q); ?></span>
                    <?php 
                        endforeach;
                    elseif ($movie['quality']): 
                    ?>
                        <span class="quality"><?php echo htmlspecialchars($movie['quality']); ?></span>
                    <?php endif; ?>
                    
                    <?php if ($movie['year']): ?>
                        <span><i class="fas fa-calendar"></i> <?php echo htmlspecialchars($movie['year']); ?></span>
                    <?php endif; ?>
                    
                    <?php if ($movie['movie_size_readable']): ?>
                        <span><i class="fas fa-hdd"></i> <?php echo htmlspecialchars($movie['movie_size_readable']); ?></span>
                    <?php endif; ?>
                </div>
                
                <div class="stats">
                    <div>
                        <i class="fas fa-eye"></i>
                        <span><?php echo number_format($movie['view_count']); ?> views</span>
                    </div>
                    
                    <div>
                        <i class="fas fa-clock"></i>
                        <span><?php echo timeAgo($movie['created_at']); ?></span>
                    </div>
                    
                    <?php if ($movie['is_split']): ?>
                    <div>
                        <i class="fas fa-file-archive"></i>
                        <span><?php echo $movie['total_parts']; ?> parts</span>
                    </div>
                    <?php endif; ?>
                </div>
                
                <div class="description">
                    <p style="color: #B3B3B3; line-height: 1.8;">
                        Download <?php echo htmlspecialchars($movie['movie_title']); ?>
                        <?php 
                        if (!empty($availableQualities) && is_array($availableQualities)):
                            echo ' in ' . implode(', ', array_map('htmlspecialchars', $availableQualities)) . ' quality.';
                        elseif ($movie['quality']):
                            echo ' in ' . htmlspecialchars($movie['quality']) . ' quality.';
                        endif;
                        ?>
                        This movie is available for direct download with high-speed servers.
                        <?php if ($movie['movie_size_readable']): ?>
                        File size: <?php echo htmlspecialchars($movie['movie_size_readable']); ?>.
                        <?php endif; ?>
                    </p>
                </div>
            </div>
        </div>
        
        <?php if ($showAds): ?>
        <!-- Ad after movie details -->
        <?php echo displayAds('after_details', 'movie_page'); ?>
        <?php endif; ?>
        
        <!-- Download Section -->
        <div class="download-section" id="download">
            <h2><i class="fas fa-download"></i> Download Links</h2>
            
            <?php if (!empty($downloadLinks)): ?>
                <?php
                // Check if quality_variants exists (multi-quality movie)
                $qualityVariants = null;
                if (!empty($movie['quality_variants'])) {
                    $qualityVariants = json_decode($movie['quality_variants'], true);
                }
                
                if ($qualityVariants && is_array($qualityVariants) && count($qualityVariants) > 1):
                    // Multi-quality movie - show quality tabs
                ?>
                    <!-- Quality Selector Tabs -->
                    <div class="quality-tabs">
                        <?php 
                        $qualityOrder = ['4K', '1080p', '720p', '480p'];
                        $sortedQualities = [];
                        foreach ($qualityOrder as $q) {
                            if (isset($qualityVariants[$q])) {
                                $sortedQualities[] = $q;
                            }
                        }
                        
                        foreach ($sortedQualities as $index => $quality): 
                            $isActive = $index === 0 ? 'active' : '';
                        ?>
                            <button class="quality-tab <?php echo $isActive; ?>" 
                                    data-quality="<?php echo htmlspecialchars($quality); ?>">
                                <i class="fas fa-hd-video"></i>
                                <?php echo htmlspecialchars($quality); ?>
                                <span class="size"><?php echo htmlspecialchars($qualityVariants[$quality]['size'] ?? ''); ?></span>
                            </button>
                        <?php endforeach; ?>
                    </div>
                    
                    <!-- Quality-specific download links -->
                    <?php foreach ($sortedQualities as $index => $quality): 
                        $qualityData = $qualityVariants[$quality];
                        $qualityLinks = $qualityData['download_links'] ?? [];
                        $isActive = $index === 0 ? 'active' : '';
                    ?>
                        <div class="quality-content <?php echo $isActive; ?>" 
                             data-quality="<?php echo htmlspecialchars($quality); ?>">
                            
                            <?php if (!empty($qualityLinks)): ?>
                                <div class="download-links">
                                    <?php foreach ($qualityLinks as $source => $url): ?>
                                        <?php 
                                        $sourceNames = [
                                            'gdflix' => 'GDFlix',
                                            'hubcloud' => 'HubCloud',
                                            'filepress' => 'FilePress',
                                            'multicloud' => 'MultiCloud'
                                        ];
                                        $sourceName = $sourceNames[$source] ?? ucfirst($source);
                                        $sourceClass = strtolower($source);
                                        
                                        // Wrap download URL with ad redirect
                                        $downloadUrl = wrapWithAdRedirect($url, 'download_' . $quality . '_' . $source);
                                        ?>
                                        <a href="<?php echo htmlspecialchars($downloadUrl); ?>" 
                                           target="_blank" 
                                           class="download-btn <?php echo $sourceClass; ?>">
                                            <i class="fas fa-download"></i>
                                            Download <?php echo htmlspecialchars($quality); ?> via <?php echo $sourceName; ?>
                                        </a>
                                    <?php endforeach; ?>
                                </div>
                            <?php else: ?>
                                <p style="color: #B3B3B3; text-align: center; padding: 20px;">
                                    <i class="fas fa-exclamation-circle"></i> 
                                    Download links for <?php echo htmlspecialchars($quality); ?> are currently unavailable.
                                </p>
                            <?php endif; ?>
                        </div>
                    <?php endforeach; ?>
                    
                <?php else: ?>
                    <!-- Single quality movie - show as before -->
                    <div class="download-links">
                        <?php foreach ($downloadLinks as $source => $url): ?>
                            <?php 
                            $sourceNames = [
                                'gdflix' => 'GDFlix',
                                'hubcloud' => 'HubCloud',
                                'filepress' => 'FilePress',
                                'multicloud' => 'MultiCloud'
                            ];
                            $sourceName = $sourceNames[$source] ?? ucfirst($source);
                            $sourceClass = strtolower($source);
                            
                            // Wrap download URL with ad redirect
                            $downloadUrl = wrapWithAdRedirect($url, 'download_' . $source);
                            ?>
                            <a href="<?php echo htmlspecialchars($downloadUrl); ?>" 
                               target="_blank" 
                               class="download-btn <?php echo $sourceClass; ?>">
                                <i class="fas fa-download"></i>
                                Download via <?php echo $sourceName; ?>
                            </a>
                        <?php endforeach; ?>
                    </div>
                <?php endif; ?>
                
            <?php else: ?>
                <p style="color: #B3B3B3; text-align: center; padding: 20px;">
                    <i class="fas fa-exclamation-circle"></i> 
                    Download links are currently unavailable. Please check back later.
                </p>
            <?php endif; ?>
            
            <div style="margin-top: 30px; padding: 20px; background: rgba(229, 9, 20, 0.1); border-radius: 8px; border-left: 4px solid #E50914;">
                <p style="color: #B3B3B3; font-size: 0.95rem; line-height: 1.6;">
                    <i class="fas fa-info-circle"></i> 
                    <strong>Note:</strong> Click on any download button above to download the movie. 
                    If one link doesn't work, try another source. All links are working and verified.
                </p>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="footer-content">
            <div class="footer-section">
                <h3><i class="fas fa-film"></i> TechAndClick Movies</h3>
                <p>
                    Your ultimate destination for downloading the latest movies in HD quality. 
                    Watch and download Bengali, Hindi, English, Tamil, and dubbed movies.
                </p>
            </div>
            
            <div class="footer-section">
                <h3>Quick Links</h3>
                <ul>
                    <li><a href="/"><i class="fas fa-home"></i> Home</a></li>
                    <li><a href="/browse.php?filter=featured"><i class="fas fa-star"></i> Featured Movies</a></li>
                    <li><a href="/browse.php?filter=latest"><i class="fas fa-clock"></i> Latest Movies</a></li>
                    <li><a href="/browse.php?quality=1080p"><i class="fas fa-hd-video"></i> HD Movies</a></li>
                </ul>
            </div>
            
            <div class="footer-section">
                <h3>Categories</h3>
                <ul>
                    <li><a href="/category.php?slug=bengali-movies"><i class="fas fa-language"></i> Bengali Movies</a></li>
                    <li><a href="/category.php?slug=hindi-movies"><i class="fas fa-film"></i> Hindi Movies</a></li>
                    <li><a href="/category.php?slug=english-movies"><i class="fas fa-video"></i> English Movies</a></li>
                    <li><a href="/category.php?slug=web-series"><i class="fas fa-tv"></i> Web Series</a></li>
                </ul>
            </div>
            
            <div class="footer-section">
                <h3>Download Quality</h3>
                <ul>
                    <li><a href="/category.php?slug=480p"><i class="fas fa-check-circle"></i> 480p Movies</a></li>
                    <li><a href="/category.php?slug=720p-hd"><i class="fas fa-check-circle"></i> 720p HD Movies</a></li>
                    <li><a href="/category.php?slug=1080p-full-hd"><i class="fas fa-check-circle"></i> 1080p Full HD</a></li>
                    <li><a href="/category.php?slug=4k-ultra-hd"><i class="fas fa-check-circle"></i> 4K Ultra HD</a></li>
                </ul>
            </div>
        </div>
        
        <div class="footer-bottom">
            <div class="social-links">
                <a href="https://t.me/getlatestmovienewgroup" target="_blank" title="Telegram">
                    <i class="fab fa-telegram"></i>
                </a>
                <a href="https://techandclick.site" target="_blank" title="Website">
                    <i class="fas fa-globe"></i>
                </a>
                <a href="#" title="YouTube">
                    <i class="fab fa-youtube"></i>
                </a>
            </div>
            
            <p style="margin-top: 20px;">&copy; <?php echo date('Y'); ?> <?php echo SITE_NAME; ?>. All rights reserved.</p>
            <p>
                Powered by <a href="https://techandclick.site" style="color: #E50914; text-decoration: none; font-weight: bold;">TechAndClick.site</a>
            </p>
            <p style="font-size: 0.75rem; margin-top: 15px; color: #666;">
                Disclaimer: This site does not host any files. All content is provided by third-party services.
            </p>
        </div>
    </footer>

    <!-- JavaScript -->
    <script src="/assets/js/main.js"></script>
    
    <!-- Load ad links for click protection -->
    <script>
    fetch('/get_ad_links.php')
        .then(response => response.json())
        .then(adLinks => {
            window.DIRECT_AD_LINKS = adLinks;
        })
        .catch(err => {
            console.error('Failed to load ad links:', err);
            window.DIRECT_AD_LINKS = [];
        });
    </script>
    
    <!-- Click Protection System -->
    <script src="/assets/js/click-protection.js"></script>
</body>
</html>
