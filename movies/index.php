<?php
require_once 'config.php';
require_once 'ads_helper.php';

// Pagination
$page    = isset($_GET['page']) ? max(1, intval($_GET['page'])) : 1;
$perPage = 24;
$offset  = ($page - 1) * $perPage;

// Data
$sliderMovies   = getRecentMovies(5, 0);
$recentMovies   = getRecentMovies($perPage, $offset);
$totalMovies    = getTotalMovieCount();
$totalPages     = ceil($totalMovies / $perPage);
$categories     = getAllCategories();
$showAds        = shouldShowAds();

// Category rows (Bengali, Hindi, English, Web Series) — 8 each
$bengaliMovies  = getMoviesByCategory('bengali-movies',  8, 0);
$hindiMovies    = getMoviesByCategory('hindi-movies',    8, 0);
$webSeries      = getMoviesByCategory('web-series',      8, 0);
$englishMovies  = getMoviesByCategory('english-movies',  8, 0);

// Helper: render a movie card
function renderCard($movie) {
    $slug   = htmlspecialchars($movie['slug']);
    $title  = htmlspecialchars($movie['movie_title']);
    $poster = htmlspecialchars($movie['poster_url']);
    $year   = $movie['year'] ?? '';
    $quality = $movie['quality'] ?? '';
    $qualities = [];
    if (!empty($movie['available_qualities'])) {
        $q = json_decode($movie['available_qualities'], true);
        if (is_array($q)) $qualities = $q;
    }
    if (empty($qualities) && $quality) $qualities = [$quality];
    echo '<div class="movie-card" data-slug="'.$slug.'">';
    echo '  <div class="movie-card-poster">';
    echo '    <img src="'.$poster.'" alt="'.$title.'" loading="lazy">';
    if (!empty($qualities)) {
        echo '<div class="quality-badges-group">';
        foreach (array_slice($qualities, 0, 2) as $q) {
            echo '<span class="quality-badge">'.htmlspecialchars($q).'</span>';
        }
        echo '</div>';
    }
    echo '  </div>';
    echo '  <div class="movie-card-info">';
    echo '    <div class="movie-title">'.$title.'</div>';
    if ($year) echo '    <div class="movie-meta"><span><i class="fas fa-calendar"></i> '.$year.'</span></div>';
    echo '  </div>';
    echo '</div>';
}

// Helper: render a horizontal scroll section row
function renderSection($title, $icon, $movies, $browseUrl = '') {
    if (empty($movies)) return;
    $id = 'row_' . md5($title);
    echo '<section class="movie-section">';
    echo '<div class="section-header">';
    echo '<h2 class="section-title"><i class="fas '.$icon.'"></i> '.$title.'</h2>';
    if ($browseUrl) echo '<a href="'.$browseUrl.'" class="see-all">See All <i class="fas fa-chevron-right"></i></a>';
    echo '</div>';
    echo '<div class="scroll-section-wrapper">';
    echo '  <button class="scroll-arrow-btn scroll-arrow-left" onclick="scrollRow(\''.$id.'\',-1)">&#10094;</button>';
    echo '  <div class="movie-scroll-row" id="'.$id.'">';
    foreach ($movies as $m) renderCard($m);
    echo '  </div>';
    echo '  <button class="scroll-arrow-btn scroll-arrow-right" onclick="scrollRow(\''.$id.'\',1)">&#10095;</button>';
    echo '</div>';
    echo '</section>';
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo SITE_NAME; ?> - Watch & Download Latest Movies</title>
    <meta name="description" content="<?php echo SITE_DESCRIPTION; ?>">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎬</text></svg>">
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Adsterra Popunder -->
    <script data-cfasync="false">(function(d,s){var js=d.createElement(s);js.src='https://pl31123316.profitableratecpmnetwork.com/2e/a6/35/2ea63559996b1cbedb3c11f36fd88a6e.js';js.async=true;d.head.appendChild(js);})(document,'script');</script>
</head>
<body>

    <?php if ($showAds): echo displayAds('header', 'homepage'); endif; ?>

    <!-- Navbar -->
    <nav class="navbar" id="navbar">
        <div style="display:flex;align-items:center;">
            <a href="/" class="logo"><i class="fas fa-film"></i> MOVIES</a>
            <button class="nav-toggle" id="navToggle" aria-label="Menu">
                <span></span><span></span><span></span>
            </button>
            <div class="nav-links" id="navLinks">
                <a href="/" class="active">Home</a>
                <a href="/browse.php?filter=latest">Latest</a>
                <div class="nav-dropdown">
                    <a href="#" class="dropdown-toggle">Categories <i class="fas fa-chevron-down"></i></a>
                    <div class="dropdown-menu">
                        <?php foreach ($categories as $cat): if ($cat['movie_count'] > 0): ?>
                            <a href="/category.php?slug=<?php echo urlencode($cat['category_slug']); ?>">
                                <i class="fas <?php echo htmlspecialchars($cat['icon']); ?>"></i>
                                <?php echo htmlspecialchars($cat['category_name']); ?>
                                <span class="count">(<?php echo $cat['movie_count']; ?>)</span>
                            </a>
                        <?php endif; endforeach; ?>
                    </div>
                </div>
                <a href="/browse.php?quality=1080p">HD Movies</a>
                <a href="/browse.php?year=<?php echo date('Y'); ?>"><?php echo date('Y'); ?> Movies</a>
            </div>
        </div>
        <form id="searchForm" class="search-box">
            <input type="text" id="searchInput" placeholder="Search movies..." autocomplete="off">
            <button type="submit"><i class="fas fa-search"></i></button>
        </form>
    </nav>

    <!-- ── HERO SLIDER ────────────────────────────── -->
    <?php if (!empty($sliderMovies)): ?>
    <div class="hero-slider" id="heroSlider">
        <?php foreach ($sliderMovies as $i => $slide): ?>
        <div class="hero-slide <?php echo $i === 0 ? 'active' : ''; ?>"
             style="background-image:linear-gradient(to right,rgba(0,0,0,.88) 38%,rgba(0,0,0,.2) 100%),url('<?php echo htmlspecialchars($slide['poster_url']); ?>');">
            <div class="hero-content">
                <h1><?php echo htmlspecialchars($slide['movie_title']); ?></h1>
                <div class="meta">
                    <?php if ($slide['quality']): ?><span class="quality"><?php echo htmlspecialchars($slide['quality']); ?></span><?php endif; ?>
                    <?php if ($slide['year']): ?><span><?php echo $slide['year']; ?></span><?php endif; ?>
                </div>
                <div class="buttons">
                    <a href="/movie.php?slug=<?php echo htmlspecialchars($slide['slug']); ?>" class="btn btn-primary"><i class="fas fa-play"></i> Watch Now</a>
                    <a href="/movie.php?slug=<?php echo htmlspecialchars($slide['slug']); ?>#download" class="btn btn-secondary"><i class="fas fa-download"></i> Download</a>
                </div>
            </div>
        </div>
        <?php endforeach; ?>
        <div class="slider-dots">
            <?php foreach ($sliderMovies as $i => $s): ?>
                <span class="slider-dot <?php echo $i===0?'active':''; ?>" data-index="<?php echo $i; ?>"></span>
            <?php endforeach; ?>
        </div>
        <button class="slider-arrow slider-prev" id="sliderPrev">&#10094;</button>
        <button class="slider-arrow slider-next" id="sliderNext">&#10095;</button>
    </div>
    <?php endif; ?>

    <!-- ── CATEGORY QUICK LINKS BAR ─────────────── -->
    <div class="category-bar">
        <div class="category-bar-inner">
            <?php 
            $catIcons = ['bengali-movies'=>'fa-language','hindi-movies'=>'fa-film','english-movies'=>'fa-video',
                         'tamil-movies'=>'fa-film','telugu-movies'=>'fa-film','web-series'=>'fa-tv',
                         '4k-ultra-hd'=>'fa-star','1080p-full-hd'=>'fa-hd-video','720p-hd'=>'fa-hd-video'];
            foreach ($categories as $cat):
                if ($cat['movie_count'] < 1) continue;
                $icon = $catIcons[$cat['category_slug']] ?? 'fa-folder';
            ?>
            <a href="/category.php?slug=<?php echo urlencode($cat['category_slug']); ?>" class="cat-chip">
                <i class="fas <?php echo $icon; ?>"></i>
                <?php echo htmlspecialchars($cat['category_name']); ?>
                <span><?php echo $cat['movie_count']; ?></span>
            </a>
            <?php endforeach; ?>
        </div>
    </div>

    <!-- ── MAIN CONTENT ───────────────────────────── -->
    <div class="page-container">

        <!-- Latest Movies (paginated) -->
        <section class="movie-section">
            <div class="section-header">
                <h2 class="section-title"><i class="fas fa-clock"></i> Latest Movies</h2>
                <span class="movie-count-badge"><?php echo number_format($totalMovies); ?> Movies</span>
            </div>
            <?php if (!empty($recentMovies)): ?>
            <div class="movie-grid">
                <?php foreach ($recentMovies as $m) renderCard($m); ?>
            </div>
            <!-- Pagination -->
            <?php if ($totalPages > 1): ?>
            <div class="pagination">
                <?php if ($page > 1): ?><a href="?page=<?php echo $page-1; ?>" class="page-btn"><i class="fas fa-chevron-left"></i> Prev</a><?php endif; ?>
                <?php
                $s = max(1, $page-2); $e = min($totalPages, $page+2);
                if ($s > 1) { echo '<a href="?page=1" class="page-btn">1</a>'; if ($s>2) echo '<span class="page-btn" style="cursor:default">…</span>'; }
                for ($i=$s; $i<=$e; $i++) echo '<a href="?page='.$i.'" class="page-btn'.($i==$page?' active':'').'">'.$i.'</a>';
                if ($e < $totalPages) { if ($e<$totalPages-1) echo '<span class="page-btn" style="cursor:default">…</span>'; echo '<a href="?page='.$totalPages.'" class="page-btn">'.$totalPages.'</a>'; }
                ?>
                <?php if ($page < $totalPages): ?><a href="?page=<?php echo $page+1; ?>" class="page-btn">Next <i class="fas fa-chevron-right"></i></a><?php endif; ?>
            </div>
            <?php endif; ?>
            <?php endif; ?>
        </section>

        <?php if ($showAds): echo displayAds('mid_content', 'homepage'); endif; ?>

        <!-- Bengali Movies Row -->
        <?php renderSection('Bengali Movies', 'fa-language', $bengaliMovies, '/category.php?slug=bengali-movies'); ?>

        <!-- Hindi Movies Row -->
        <?php renderSection('Hindi Movies', 'fa-film', $hindiMovies, '/category.php?slug=hindi-movies'); ?>

        <!-- Web Series Row -->
        <?php renderSection('Web Series', 'fa-tv', $webSeries, '/category.php?slug=web-series'); ?>

        <!-- English Movies Row -->
        <?php renderSection('English Movies', 'fa-video', $englishMovies, '/category.php?slug=english-movies'); ?>

        <!-- Quality Links Section -->
        <section class="quality-section">
            <h2 class="section-title"><i class="fas fa-hd-video"></i> Browse by Quality</h2>
            <div class="quality-cards">
                <a href="/category.php?slug=4k-ultra-hd" class="quality-card q4k">
                    <i class="fas fa-star"></i>
                    <span>4K Ultra HD</span>
                    <small>Best Quality</small>
                </a>
                <a href="/category.php?slug=1080p-full-hd" class="quality-card q1080">
                    <i class="fas fa-hd-video"></i>
                    <span>1080p Full HD</span>
                    <small>High Quality</small>
                </a>
                <a href="/category.php?slug=720p-hd" class="quality-card q720">
                    <i class="fas fa-hd-video"></i>
                    <span>720p HD</span>
                    <small>Good Quality</small>
                </a>
                <a href="/category.php?slug=480p" class="quality-card q480">
                    <i class="fas fa-check-circle"></i>
                    <span>480p</span>
                    <small>Low Size</small>
                </a>
            </div>
        </section>

    </div><!-- /page-container -->

    <!-- ── FOOTER ─────────────────────────────────── -->
    <footer class="footer">
        <div class="footer-content">
            <div class="footer-section">
                <h3><i class="fas fa-film"></i> TechAndClick Movies</h3>
                <p>Your ultimate destination for downloading the latest movies in HD quality. Bengali, Hindi, English, Tamil, and dubbed movies.</p>
                <div class="social-links" style="margin-top:14px;">
                    <a href="https://t.me/newmoviesarena4u" target="_blank" title="Telegram"><i class="fab fa-telegram"></i></a>
                    <a href="https://techandclick.site" target="_blank" title="Website"><i class="fas fa-globe"></i></a>
                </div>
            </div>
            <div class="footer-section">
                <h3>Quick Links</h3>
                <ul>
                    <li><a href="/"><i class="fas fa-home"></i> Home</a></li>
                    <li><a href="/browse.php?filter=latest"><i class="fas fa-clock"></i> Latest Movies</a></li>
                    <li><a href="/browse.php?quality=1080p"><i class="fas fa-hd-video"></i> HD Movies</a></li>
                    <li><a href="/browse.php?year=<?php echo date('Y'); ?>"><i class="fas fa-calendar"></i> <?php echo date('Y'); ?> Movies</a></li>
                </ul>
            </div>
            <div class="footer-section">
                <h3>Categories</h3>
                <ul>
                    <li><a href="/category.php?slug=bengali-movies"><i class="fas fa-language"></i> Bengali Movies</a></li>
                    <li><a href="/category.php?slug=hindi-movies"><i class="fas fa-film"></i> Hindi Movies</a></li>
                    <li><a href="/category.php?slug=english-movies"><i class="fas fa-video"></i> English Movies</a></li>
                    <li><a href="/category.php?slug=web-series"><i class="fas fa-tv"></i> Web Series</a></li>
                    <li><a href="/category.php?slug=tamil-movies"><i class="fas fa-film"></i> Tamil Movies</a></li>
                </ul>
            </div>
            <div class="footer-section">
                <h3>Download Quality</h3>
                <ul>
                    <li><a href="/category.php?slug=4k-ultra-hd"><i class="fas fa-star"></i> 4K Ultra HD</a></li>
                    <li><a href="/category.php?slug=1080p-full-hd"><i class="fas fa-hd-video"></i> 1080p Full HD</a></li>
                    <li><a href="/category.php?slug=720p-hd"><i class="fas fa-hd-video"></i> 720p HD</a></li>
                    <li><a href="/category.php?slug=480p"><i class="fas fa-check-circle"></i> 480p</a></li>
                </ul>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; <?php echo date('Y'); ?> <?php echo SITE_NAME; ?>. All rights reserved.</p>
            <p style="font-size:0.75rem;color:#555;margin-top:8px;">Disclaimer: This site does not host any files. All content is provided by third-party services.</p>
        </div>
    </footer>

    <script src="/assets/js/main.js"></script>
    <script src="/assets/js/click-protection.js"></script>

    <!-- Row Scroll Script -->
    <script>
    function scrollRow(id, dir) {
        var el = document.getElementById(id);
        if (el) el.scrollBy({ left: dir * 320, behavior: 'smooth' });
    }
    </script>

    <!-- Slider Script -->
    <script>
    (function(){
        var slides  = document.querySelectorAll('.hero-slide');
        var dots    = document.querySelectorAll('.slider-dot');
        var current = 0, timer;
        if (!slides.length) return;

        function goTo(n) {
            slides[current].classList.remove('active');
            dots[current].classList.remove('active');
            current = (n + slides.length) % slides.length;
            slides[current].classList.add('active');
            dots[current].classList.add('active');
        }
        function next(){ goTo(current+1); }
        function prev(){ goTo(current-1); }
        function startAuto(){ timer = setInterval(next, 4500); }
        function resetAuto(){ clearInterval(timer); startAuto(); }

        document.getElementById('sliderNext').onclick = function(){ next(); resetAuto(); };
        document.getElementById('sliderPrev').onclick = function(){ prev(); resetAuto(); };
        dots.forEach(function(d,i){ d.onclick = function(){ goTo(i); resetAuto(); }; });

        var tx=0, slider=document.getElementById('heroSlider');
        slider.addEventListener('touchstart',function(e){tx=e.touches[0].clientX;},{passive:true});
        slider.addEventListener('touchend',function(e){
            var d=tx-e.changedTouches[0].clientX;
            if(Math.abs(d)>50){d>0?next():prev(); resetAuto();}
        },{passive:true});
        startAuto();
    })();
    </script>

    <?php if ($showAds): echo displayAds('footer', 'homepage'); endif; ?>
    <!-- Adsterra Social Bar -->
    <script data-cfasync="false">(function(d,s){var js=d.createElement(s);js.src='https://pl31123318.profitableratecpmnetwork.com/51/77/86/517786261e02f312302cad8f15271421.js';d.body.appendChild(js);})(document,'script');</script>
</body>
</html>
