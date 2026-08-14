<?php
require_once 'config.php';
require_once 'ads_helper.php';

// Pagination
$page    = isset($_GET['page']) ? max(1, intval($_GET['page'])) : 1;
$perPage = 24;
$offset  = ($page - 1) * $perPage;

// Get featured and recent movies
$featuredMovies = getFeaturedMovies(6);
$recentMovies   = getRecentMovies($perPage, $offset);
$totalMovies    = getTotalMovieCount();
$totalPages     = ceil($totalMovies / $perPage);

// Get all categories with movie count
$categories = getAllCategories();

// Get hero movie
$heroMovie = !empty($featuredMovies) ? $featuredMovies[0] : (!empty($recentMovies) ? $recentMovies[0] : null);

$showAds = shouldShowAds();

// Slider: latest 5 movies with poster
$sliderMovies = getRecentMovies(5, 0);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo SITE_NAME; ?> - Watch & Download Latest Movies</title>
    <meta name="description" content="<?php echo SITE_DESCRIPTION; ?>">
    
    <!-- Favicon -->
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎬</text></svg>">
    
    <!-- CSS -->
    <link rel="stylesheet" href="/assets/css/style.css">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Ads Styles -->
    <style>
        .ad-container {
            margin: 20px 0;
            text-align: center;
            min-height: 90px;
        }
        
        .ad-container.ad-banner {
            background: rgba(47, 47, 47, 0.3);
            border-radius: 8px;
            padding: 10px;
        }
        
        .ad-social_bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 999;
        }
    </style>
</head>
<body>

    <?php if ($showAds): ?>
    <!-- PopUnder / Header Ads -->
    <?php echo displayAds('header', 'homepage'); ?>
    <?php endif; ?>

    <!-- Navbar -->
    <nav class="navbar">
        <div style="display:flex;align-items:center;">
            <a href="/" class="logo"><i class="fas fa-film"></i> MOVIES</a>
            <!-- Hamburger -->
            <button class="nav-toggle" id="navToggle" aria-label="Menu">
                <span></span><span></span><span></span>
            </button>
            
            <div class="nav-links" id="navLinks">
                <a href="/" class="active no-ad-protection">Home</a>
                <a href="/browse.php?filter=featured" class="no-ad-protection">Featured</a>
                <a href="/browse.php?filter=latest" class="no-ad-protection">Latest</a>
                
                <!-- Categories Dropdown -->
                <div class="nav-dropdown">
                    <a href="#" class="dropdown-toggle no-ad-protection">
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

    <?php if (!empty($sliderMovies)): ?>
    <!-- Hero Slider -->
    <div class="hero-slider" id="heroSlider">
        <?php foreach ($sliderMovies as $i => $slide): ?>
        <div class="hero-slide <?php echo $i === 0 ? 'active' : ''; ?>"
             style="background-image: linear-gradient(to right, rgba(0,0,0,0.88) 35%, rgba(0,0,0,0.25) 100%), url('<?php echo htmlspecialchars($slide['poster_url']); ?>');">
            <div class="hero-content">
                <h1><?php echo htmlspecialchars($slide['movie_title']); ?></h1>
                <div class="meta">
                    <?php if ($slide['quality']): ?>
                        <span class="quality"><?php echo htmlspecialchars($slide['quality']); ?></span>
                    <?php endif; ?>
                    <?php if ($slide['year']): ?>
                        <span><?php echo $slide['year']; ?></span>
                    <?php endif; ?>
                </div>
                <div class="buttons">
                    <a href="/movie.php?slug=<?php echo htmlspecialchars($slide['slug']); ?>" class="btn btn-primary">
                        <i class="fas fa-play"></i> Watch Now
                    </a>
                    <a href="/movie.php?slug=<?php echo htmlspecialchars($slide['slug']); ?>#download" class="btn btn-secondary">
                        <i class="fas fa-download"></i> Download
                    </a>
                </div>
            </div>
        </div>
        <?php endforeach; ?>

        <!-- Dots -->
        <div class="slider-dots">
            <?php foreach ($sliderMovies as $i => $slide): ?>
                <span class="slider-dot <?php echo $i === 0 ? 'active' : ''; ?>" data-index="<?php echo $i; ?>"></span>
            <?php endforeach; ?>
        </div>

        <!-- Arrows -->
        <button class="slider-arrow slider-prev" id="sliderPrev">&#10094;</button>
        <button class="slider-arrow slider-next" id="sliderNext">&#10095;</button>
    </div>
    <?php endif; ?>

    <!-- Main Content with Sidebar -->
    <div class="main-wrapper">
        <!-- Left: Movies Content -->
        <div class="content-area">
            <?php if (!empty($featuredMovies)): ?>
            <!-- Featured Movies Section -->
            <section class="movie-section">
                <?php if ($showAds): ?>
                <!-- Ad before featured section -->
                <?php echo displayAds('before_content', 'homepage'); ?>
                <?php endif; ?>
                
                <h2 class="section-title">
                    <i class="fas fa-star"></i> Featured Movies
                </h2>
                
                <div class="movie-grid">
            <?php foreach ($featuredMovies as $movie): ?>
                <div class="movie-card" data-slug="<?php echo htmlspecialchars($movie['slug']); ?>">
                    <div class="movie-card-poster">
                        <img src="<?php echo htmlspecialchars($movie['poster_url']); ?>" 
                             alt="<?php echo htmlspecialchars($movie['movie_title']); ?>"
                             loading="lazy">
                        
                        <?php 
                        // Quality badges - always visible on poster
                        $qualities = [];
                        if (!empty($movie['available_qualities'])) {
                            $qualities = json_decode($movie['available_qualities'], true);
                        }
                        
                        if (!empty($qualities) && is_array($qualities)):
                        ?>
                            <div class="quality-badges-group">
                                <?php foreach ($qualities as $q): ?>
                                    <span class="quality-badge"><?php echo htmlspecialchars($q); ?></span>
                                <?php endforeach; ?>
                            </div>
                        <?php elseif ($movie['quality']): ?>
                            <span class="quality-badge"><?php echo htmlspecialchars($movie['quality']); ?></span>
                        <?php endif; ?>
                    </div>
                    
                    <div class="movie-card-info">
                        <div class="movie-title"><?php echo htmlspecialchars($movie['movie_title']); ?></div>
                        <div class="movie-meta">
                            <?php if ($movie['year']): ?>
                                <span><i class="fas fa-calendar"></i> <?php echo htmlspecialchars($movie['year']); ?></span>
                            <?php endif; ?>
                            <?php if ($movie['movie_size_readable']): ?>
                                <span><i class="fas fa-hdd"></i> <?php echo htmlspecialchars($movie['movie_size_readable']); ?></span>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
    </section>
    <?php endif; ?>

    <!-- Recent Movies Section -->
    <section class="movie-section">
        <h2 class="section-title">
            <i class="fas fa-clock"></i> Latest Movies
        </h2>
        
        <?php if (!empty($recentMovies)): ?>
            <div class="movie-grid">
                <?php foreach ($recentMovies as $movie): ?>
                    <div class="movie-card" data-slug="<?php echo htmlspecialchars($movie['slug']); ?>">
                        <div class="movie-card-poster">
                            <img src="<?php echo htmlspecialchars($movie['poster_url']); ?>" 
                                 alt="<?php echo htmlspecialchars($movie['movie_title']); ?>"
                                 loading="lazy">
                            
                            <?php 
                            // Quality badges - always visible on poster
                            $qualities = [];
                            if (!empty($movie['available_qualities'])) {
                                $qualities = json_decode($movie['available_qualities'], true);
                            }
                            
                            if (!empty($qualities) && is_array($qualities)):
                            ?>
                                <div class="quality-badges-group">
                                    <?php foreach ($qualities as $q): ?>
                                        <span class="quality-badge"><?php echo htmlspecialchars($q); ?></span>
                                    <?php endforeach; ?>
                                </div>
                            <?php elseif ($movie['quality']): ?>
                                <span class="quality-badge"><?php echo htmlspecialchars($movie['quality']); ?></span>
                            <?php endif; ?>
                        </div>
                        
                        <div class="movie-card-info">
                            <div class="movie-title"><?php echo htmlspecialchars($movie['movie_title']); ?></div>
                            <div class="movie-meta">
                                <?php if ($movie['year']): ?>
                                    <span><i class="fas fa-calendar"></i> <?php echo htmlspecialchars($movie['year']); ?></span>
                                <?php endif; ?>
                                <?php if ($movie['movie_size_readable']): ?>
                                    <span><i class="fas fa-hdd"></i> <?php echo htmlspecialchars($movie['movie_size_readable']); ?></span>
                                <?php endif; ?>
                            </div>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>
        <?php else: ?>
            <p class="text-center" style="color: #B3B3B3; padding: 40px;">
                No movies available yet. Check back soon!
            </p>
        <?php endif; ?>

        <!-- Pagination -->
        <?php if ($totalPages > 1): ?>
        <div class="pagination">
            <?php if ($page > 1): ?>
                <a href="?page=<?php echo $page - 1; ?>" class="page-btn">
                    <i class="fas fa-chevron-left"></i> Prev
                </a>
            <?php endif; ?>

            <?php
            $start = max(1, $page - 2);
            $end   = min($totalPages, $page + 2);
            if ($start > 1): ?>
                <a href="?page=1" class="page-btn">1</a>
                <?php if ($start > 2): ?><span class="page-btn" style="cursor:default;">…</span><?php endif; ?>
            <?php endif; ?>

            <?php for ($i = $start; $i <= $end; $i++): ?>
                <a href="?page=<?php echo $i; ?>"
                   class="page-btn <?php echo $i == $page ? 'active' : ''; ?>">
                    <?php echo $i; ?>
                </a>
            <?php endfor; ?>

            <?php if ($end < $totalPages): ?>
                <?php if ($end < $totalPages - 1): ?><span class="page-btn" style="cursor:default;">…</span><?php endif; ?>
                <a href="?page=<?php echo $totalPages; ?>" class="page-btn"><?php echo $totalPages; ?></a>
            <?php endif; ?>

            <?php if ($page < $totalPages): ?>
                <a href="?page=<?php echo $page + 1; ?>" class="page-btn">
                    Next <i class="fas fa-chevron-right"></i>
                </a>
            <?php endif; ?>
        </div>
        <?php endif; ?>
    </section>
        </div>
        
        <!-- Right: Sidebar with Categories -->
        <aside class="sidebar">
            <?php if (!empty($categories)): ?>
            <div class="sidebar-section">
                <h3 class="sidebar-title">
                    <i class="fas fa-th-large"></i> Browse by Category
                </h3>
                
                <div class="sidebar-categories">
                    <?php foreach ($categories as $category): ?>
                        <?php if ($category['movie_count'] > 0): ?>
                            <a href="/category.php?slug=<?php echo urlencode($category['category_slug']); ?>" 
                               class="sidebar-category-item">
                                <i class="fas <?php echo htmlspecialchars($category['icon']); ?>"></i>
                                <span class="cat-name"><?php echo htmlspecialchars($category['category_name']); ?></span>
                                <span class="cat-count"><?php echo $category['movie_count']; ?></span>
                            </a>
                        <?php endif; ?>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endif; ?>
        </aside>
    </div>

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
    
    <!-- Click Protection System -->
    <script src="/assets/js/click-protection.js"></script>

    <!-- Hero Slider Script -->
    <script>
    (function(){
        var slides = document.querySelectorAll('.hero-slide');
        var dots   = document.querySelectorAll('.slider-dot');
        if (!slides.length) return;

        var current = 0;
        var timer;

        function goTo(n) {
            slides[current].classList.remove('active');
            dots[current].classList.remove('active');
            current = (n + slides.length) % slides.length;
            slides[current].classList.add('active');
            dots[current].classList.add('active');
        }

        function next() { goTo(current + 1); }
        function prev() { goTo(current - 1); }

        function startAuto() {
            timer = setInterval(next, 4000);
        }
        function resetAuto() {
            clearInterval(timer);
            startAuto();
        }

        document.getElementById('sliderNext').addEventListener('click', function(){ next(); resetAuto(); });
        document.getElementById('sliderPrev').addEventListener('click', function(){ prev(); resetAuto(); });

        dots.forEach(function(dot, i){
            dot.addEventListener('click', function(){ goTo(i); resetAuto(); });
        });

        // Touch swipe support
        var touchStartX = 0;
        var slider = document.getElementById('heroSlider');
        slider.addEventListener('touchstart', function(e){ touchStartX = e.touches[0].clientX; }, {passive:true});
        slider.addEventListener('touchend', function(e){
            var diff = touchStartX - e.changedTouches[0].clientX;
            if (Math.abs(diff) > 50) { diff > 0 ? next() : prev(); resetAuto(); }
        }, {passive:true});

        startAuto();
    })();
    </script>
    
    <?php if ($showAds): ?>
    <!-- Social Bar / Footer Ads -->
    <?php echo displayAds('footer', 'homepage'); ?>
    <?php endif; ?>
</body>
</html>
