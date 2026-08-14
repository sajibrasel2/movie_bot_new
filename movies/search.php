<?php
require_once 'config.php';

// Get search query
$query = $_GET['q'] ?? '';
$searchResults = [];

if (!empty($query)) {
    $searchResults = searchMovies($query, 50);
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search: <?php echo htmlspecialchars($query); ?> - <?php echo SITE_NAME; ?></title>
    <meta name="description" content="Search results for <?php echo htmlspecialchars($query); ?>">
    
    <!-- Favicon -->
    <link rel="icon" type="image/png" href="/assets/images/favicon.png">
    
    <!-- CSS -->
    <link rel="stylesheet" href="/assets/css/style.css">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>

    <!-- Navbar -->
    <nav class="navbar scrolled">
        <a href="/" class="logo">
            <i class="fas fa-film"></i> MOVIES
        </a>
        
        <form id="searchForm" class="search-box">
            <input type="text" 
                   id="searchInput" 
                   placeholder="Search movies..." 
                   autocomplete="off"
                   value="<?php echo htmlspecialchars($query); ?>">
            <button type="submit"><i class="fas fa-search"></i></button>
        </form>
    </nav>

    <!-- Search Results Section -->
    <section class="movie-section" style="margin-top: 100px;">
        <h2 class="section-title">
            <i class="fas fa-search"></i> 
            Search Results for "<?php echo htmlspecialchars($query); ?>"
            <?php if (!empty($searchResults)): ?>
                <span style="font-size: 1rem; color: #B3B3B3; font-weight: normal;">
                    (<?php echo count($searchResults); ?> found)
                </span>
            <?php endif; ?>
        </h2>
        
        <?php if (!empty($searchResults)): ?>
            <div class="movie-grid">
                <?php foreach ($searchResults as $movie): ?>
                    <div class="movie-card" data-slug="<?php echo htmlspecialchars($movie['slug']); ?>">
                        <img src="<?php echo htmlspecialchars($movie['poster_url']); ?>" 
                             alt="<?php echo htmlspecialchars($movie['movie_title']); ?>"
                             loading="lazy">
                        
                        <div class="overlay">
                            <div class="title"><?php echo htmlspecialchars($movie['movie_title']); ?></div>
                            <div class="meta">
                                <?php if ($movie['quality']): ?>
                                    <span class="quality-badge"><?php echo htmlspecialchars($movie['quality']); ?></span>
                                <?php endif; ?>
                                
                                <?php if ($movie['movie_size_readable']): ?>
                                    <span><?php echo htmlspecialchars($movie['movie_size_readable']); ?></span>
                                <?php endif; ?>
                            </div>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>
        <?php elseif (!empty($query)): ?>
            <div style="text-align: center; padding: 60px 20px;">
                <i class="fas fa-search" style="font-size: 4rem; color: #2F2F2F; margin-bottom: 20px;"></i>
                <h3 style="font-size: 1.5rem; margin-bottom: 10px;">No results found</h3>
                <p style="color: #B3B3B3; font-size: 1rem;">
                    We couldn't find any movies matching "<?php echo htmlspecialchars($query); ?>".
                    <br>Try searching with different keywords.
                </p>
                <a href="/" class="btn btn-primary" style="margin-top: 30px;">
                    <i class="fas fa-home"></i> Go to Homepage
                </a>
            </div>
        <?php else: ?>
            <div style="text-align: center; padding: 60px 20px;">
                <i class="fas fa-keyboard" style="font-size: 4rem; color: #2F2F2F; margin-bottom: 20px;"></i>
                <h3 style="font-size: 1.5rem; margin-bottom: 10px;">Start Searching</h3>
                <p style="color: #B3B3B3; font-size: 1rem;">
                    Enter a movie name in the search box above.
                </p>
            </div>
        <?php endif; ?>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <p>&copy; <?php echo date('Y'); ?> <?php echo SITE_NAME; ?>. All rights reserved.</p>
        <p style="margin-top: 10px; font-size: 0.85rem;">
            <a href="https://techandclick.site" style="color: #E50914; text-decoration: none;">TechAndClick.site</a>
        </p>
    </footer>

    <!-- JavaScript -->
    <script src="/assets/js/main.js"></script>
</body>
</html>
