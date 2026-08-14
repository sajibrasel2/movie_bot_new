<?php
require_once 'config.php';
require_once 'ads_helper.php';

// Get category slug from URL
$categorySlug = $_GET['slug'] ?? '';

if (empty($categorySlug)) {
    header('Location: /');
    exit;
}

// Get category details
$category = getCategoryBySlug($categorySlug);

if (!$category) {
    header('HTTP/1.0 404 Not Found');
    echo '<!DOCTYPE html>
    <html>
    <head>
        <title>Category Not Found</title>
        <link rel="stylesheet" href="' . ASSETS_URL . '/css/style.css">
    </head>
    <body>
        <div style="text-align: center; padding: 100px 20px;">
            <h1 style="font-size: 3rem; color: #E50914;">404</h1>
            <p style="font-size: 1.5rem; margin: 20px 0;">Category Not Found</p>
            <a href="/" class="btn btn-primary">Go Home</a>
        </div>
    </body>
    </html>';
    exit;
}

// Pagination
$page = isset($_GET['page']) ? max(1, intval($_GET['page'])) : 1;
$perPage = 24;
$offset = ($page - 1) * $perPage;

// Get movies in this category
$movies = getMoviesByCategory($categorySlug, $perPage, $offset);
$totalMovies = getMovieCategoryCount($categorySlug);
$totalPages = ceil($totalMovies / $perPage);

// Page title
$pageTitle = htmlspecialchars($category['category_name']) . ' - ' . SITE_NAME;

// Check if ads should be displayed
$showAds = shouldShowAds();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo $pageTitle; ?></title>
    <meta name="description" content="<?php echo htmlspecialchars($category['description']); ?>">
    
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

    <!-- Category Header -->
    <section class="page-header">
        <div class="container">
            <h1>
                <i class="fas <?php echo htmlspecialchars($category['icon']); ?>"></i>
                <?php echo htmlspecialchars($category['category_name']); ?>
            </h1>
            <p><?php echo htmlspecialchars($category['description']); ?></p>
            <p style="color: #999; font-size: 0.9rem; margin-top: 10px;">
                <?php echo number_format($totalMovies); ?> movies found
            </p>
        </div>
    </section>

    <?php if ($showAds): ?>
    <!-- Ad before content -->
    <?php echo displayAds('header', 'category_page'); ?>
    <?php endif; ?>

    <!-- Movies Grid -->
    <section class="movies-section">
        <div class="container">
            <?php if (!empty($movies)): ?>
                <div class="movies-grid">
                    <?php foreach ($movies as $movie): ?>
                        <div class="movie-card" data-slug="<?php echo htmlspecialchars($movie['slug']); ?>">
                            <div class="movie-poster">
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
                                
                                <div class="movie-overlay">
                                    <button class="play-btn">
                                        <i class="fas fa-play"></i> Watch Now
                                    </button>
                                </div>
                            </div>
                            <div class="movie-info">
                                <h3><?php echo htmlspecialchars($movie['movie_title']); ?></h3>
                                <div class="movie-meta">
                                    <?php if ($movie['year']): ?>
                                        <span><i class="fas fa-calendar"></i> <?php echo $movie['year']; ?></span>
                                    <?php endif; ?>
                                    <?php if ($movie['movie_size_readable']): ?>
                                        <span><i class="fas fa-hdd"></i> <?php echo $movie['movie_size_readable']; ?></span>
                                    <?php endif; ?>
                                </div>
                            </div>
                        </div>
                    <?php endforeach; ?>
                </div>

                <?php if ($totalPages > 1): ?>
                <!-- Pagination -->
                <div class="pagination">
                    <?php if ($page > 1): ?>
                        <a href="?slug=<?php echo urlencode($categorySlug); ?>&page=<?php echo ($page - 1); ?>" class="page-btn">
                            <i class="fas fa-chevron-left"></i> Previous
                        </a>
                    <?php endif; ?>

                    <?php for ($i = max(1, $page - 2); $i <= min($totalPages, $page + 2); $i++): ?>
                        <a href="?slug=<?php echo urlencode($categorySlug); ?>&page=<?php echo $i; ?>" 
                           class="page-btn <?php echo $i == $page ? 'active' : ''; ?>">
                            <?php echo $i; ?>
                        </a>
                    <?php endfor; ?>

                    <?php if ($page < $totalPages): ?>
                        <a href="?slug=<?php echo urlencode($categorySlug); ?>&page=<?php echo ($page + 1); ?>" class="page-btn">
                            Next <i class="fas fa-chevron-right"></i>
                        </a>
                    <?php endif; ?>
                </div>
                <?php endif; ?>

            <?php else: ?>
                <div style="text-align: center; padding: 60px 20px;">
                    <i class="fas fa-film" style="font-size: 4rem; color: #E50914; margin-bottom: 20px;"></i>
                    <h2 style="color: #fff;">No Movies Found</h2>
                    <p style="color: #999; margin-top: 10px;">Check back later for new movies in this category.</p>
                    <a href="/" class="btn btn-primary" style="margin-top: 20px;">Browse All Movies</a>
                </div>
            <?php endif; ?>
        </div>
    </section>

    <?php if ($showAds): ?>
    <!-- Ad after content -->
    <?php echo displayAds('footer', 'category_page'); ?>
    <?php endif; ?>

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
                    <?php 
                    $footerCats = [
                        ['slug' => 'bengali-movies', 'name' => 'Bengali Movies', 'icon' => 'fa-language'],
                        ['slug' => 'hindi-movies', 'name' => 'Hindi Movies', 'icon' => 'fa-film'],
                        ['slug' => 'english-movies', 'name' => 'English Movies', 'icon' => 'fa-video'],
                        ['slug' => 'web-series', 'name' => 'Web Series', 'icon' => 'fa-tv']
                    ];
                    foreach ($footerCats as $cat): 
                    ?>
                        <li>
                            <a href="/category.php?slug=<?php echo $cat['slug']; ?>">
                                <i class="fas <?php echo $cat['icon']; ?>"></i> 
                                <?php echo $cat['name']; ?>
                            </a>
                        </li>
                    <?php endforeach; ?>
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
</body>
</html>
