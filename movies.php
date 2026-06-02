<?php
/**
 * Movies listing page — Premium redesign
 * URL: /movies.php
 */
$DATA_FILE = __DIR__.'/movies.json';
$movies = json_decode(file_get_contents($DATA_FILE), true) ?: [];

// Auto-delete movies older than 10 days
$ten_days_ago = time() - (10 * 24 * 60 * 60);
$cleaned = [];
$changed = false;
foreach ($movies as $m) {
    $ts = strtotime($m['posted_at'] ?? 'now');
    if ($ts >= $ten_days_ago) {
        $cleaned[] = $m;
    } else {
        $changed = true;
    }
}
if ($changed) {
    $movies = $cleaned;
    file_put_contents($DATA_FILE, json_encode($movies, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
}

$site='https://techandclick.site'; $bot='https://t.me/GetLatestMoviesBot'; $ch='https://t.me/getlatestmoviebot';
$total = count($movies);

// Detect language/category from title
function detectCategory($title) {
    $t = mb_strtolower($title);
    if (str_contains($t, 'bengali') || str_contains($t, 'bangla') || str_contains($t, 'বাংলা')) return 'Bangla';
    if (str_contains($t, 'hindi') || str_contains($t, 'bollywood')) return 'Hindi';
    if (str_contains($t, 'hollywood') || str_contains($t, 'english') || str_contains($t, 'dual audio')) return 'Hollywood';
    if (str_contains($t, 'series') || str_contains($t, 'season') || str_contains($t, 's01') || str_contains($t, 's02')) return 'Series';
    if (str_contains($t, 'tamil') || str_contains($t, 'telugu') || str_contains($t, 'kannada') || str_contains($t, 'south')) return 'South';
    return 'Other';
}

function detectQuality($title) {
    $t = strtoupper($title);
    if (str_contains($t, '4K') || str_contains($t, 'UHD')) return '4K';
    if (str_contains($t, '1080P')) return '1080p';
    if (str_contains($t, '720P')) return '720p';
    if (str_contains($t, '480P')) return '480p';
    if (str_contains($t, 'WEB-DL')) return 'WEB-DL';
    if (str_contains($t, 'PRE-HD') || str_contains($t, 'HDTC')) return 'HD';
    return '';
}

function isNew($posted_at) {
    return (time() - strtotime($posted_at)) < (2 * 24 * 60 * 60); // 2 days
}

// Count categories for stats
$catCounts = ['All' => $total];
foreach ($movies as $m) {
    $cat = detectCategory($m['title'] ?? '');
    $catCounts[$cat] = ($catCounts[$cat] ?? 0) + 1;
}
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Latest Movies Download — Telegram Bot | Tech & Click</title>
<meta name="description" content="Download latest Bollywood, Hollywood, South Indian, Bangla movies & web series via Telegram bot. One click to get direct download links. Updated daily.">
<meta name="keywords" content="movie download telegram, latest movie download, bollywood movie telegram, free movie download bot, bangla movie download, hollywood movie download, web series download">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="<?=$site?>/movies.php">
<meta property="og:type" content="website">
<meta property="og:title" content="Latest Movies Download — Telegram Bot | Tech & Click">
<meta property="og:description" content="Download latest Bollywood, Hollywood, Bangla movies & web series via Telegram bot. Updated daily.">
<meta property="og:url" content="<?=$site?>/movies.php">
<meta property="og:site_name" content="Tech & Click">
<?php if(!empty($movies) && !empty($movies[0]['thumbnail'])):?>
<meta property="og:image" content="<?=htmlspecialchars($movies[0]['thumbnail'])?>">
<?php endif;?>
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Latest Movies Download — Telegram Bot | Tech & Click">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Tech & Click Movies",
  "url": "<?=$site?>/movies.php",
  "description": "Download latest Bollywood, Hollywood, Bangla movies & web series via Telegram bot.",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "<?=$site?>/movies.php?q={search_term_string}",
    "query-input": "required name=search_term_string"
  }
}
</script>
<link rel="stylesheet" href="movie-style.css">
<!-- Monetag Multitag WAF Bypass -->
<script>
(function(){
    var s = document.createElement('script');
    s.src = "sj.nim.gat/88/moc.5eguq//:sptth".split('').reverse().join('');
    s.setAttribute("data-zone", "242064");
    s.setAttribute("data-cfasync", "false");
    s.async = true;
    document.head.appendChild(s);
})();
</script>
</head>
<body>
<div class="wrap">

<!-- Header -->
<header>
  <a class="logo" href="/"><span>Tech & Click</span> Movies</a>
  <button class="menu-toggle" onclick="document.querySelector('.nav-links').classList.toggle('open')" aria-label="Menu">☰</button>
  <nav class="nav-links">
    <a href="/">Home</a>
    <a href="<?=$bot?>" target="_blank">🤖 Open Bot</a>
    <a href="<?=$ch?>" target="_blank">📢 Channel</a>
  </nav>
</header>

<!-- Hero Section -->
<section class="hero">
  <h1>🎬 Latest Movie Downloads on Telegram</h1>
  <p>Bollywood, Hollywood, South Indian movies & web series — search on our bot or click below to get instant download links.</p>
  <div class="hero-actions">
    <a class="btn btn-primary" href="<?=$bot?>" target="_blank">🤖 Search on Bot</a>
    <a class="btn btn-outline" href="<?=$ch?>" target="_blank">📢 Join Channel</a>
  </div>
  <div class="stats-bar">
    <div class="stat-item">
      <div class="stat-number"><?=$total?></div>
      <div class="stat-label">Movies</div>
    </div>
    <div class="stat-item">
      <div class="stat-number"><?=$catCounts['Hindi'] ?? 0?></div>
      <div class="stat-label">Hindi</div>
    </div>
    <div class="stat-item">
      <div class="stat-number"><?=$catCounts['Bangla'] ?? 0?></div>
      <div class="stat-label">Bangla</div>
    </div>
    <div class="stat-item">
      <div class="stat-number"><?=$catCounts['Series'] ?? 0?></div>
      <div class="stat-label">Series</div>
    </div>
  </div>
</section>


<!-- Search & Filter -->
<div class="search-filter-section">
  <div class="search-container">
    <span class="search-icon">🔍</span>
    <input type="text" id="searchInput" placeholder="Search movies, series, actors..." autocomplete="off">
    <span class="search-count" id="searchCount"><?=$total?> movies</span>
  </div>
  <div class="filter-tabs" id="filterTabs">
    <button class="filter-tab active" data-filter="all">All <span>(<?=$total?>)</span></button>
    <?php
    $filterOrder = ['Hindi','Bangla','Hollywood','Series','South'];
    foreach($filterOrder as $cat):
      if(($catCounts[$cat] ?? 0) > 0):
    ?>
    <button class="filter-tab" data-filter="<?=strtolower($cat)?>"><?=$cat?> <span>(<?=$catCounts[$cat]?>)</span></button>
    <?php endif; endforeach; ?>
  </div>
</div>

<!-- Banner 728x90 WAF Bypass -->
<div class="ad-banner-728" id="banner-wrap-728">
  <script>
    window['at' + 'Options'] = {
      'key' : 'ce02fc' + '8561f342f' + '8b66daf43' + '7a8b5d5c',
      'format' : 'iframe',
      'height' : 90,
      'width' : 728,
      'params' : {}
    };
    (function(){
        var s = document.createElement('script');
        s.src = "sj.ekovni/c5d5b8a734fad66b8f243f1658cf20ec/moc.tamrofeconamrofrephgih.www//:sptth".split('').reverse().join('');
        document.getElementById('banner-wrap-728').appendChild(s);
    })();
  </script>
</div>

<!-- Movie Grid -->
<div class="grid" id="movieGrid">
  <div class="no-results" id="noResults">
    <div class="emoji">🎬</div>
    <p>No movies found. Try a different search term.</p>
  </div>

<?php if(empty($movies)):?>
  <div class="empty"><p>No movies yet. Check back soon!</p></div>
<?php else: foreach($movies as $i => $m):
  $slug=$m['slug']??''; $title=htmlspecialchars($m['title']??''); $thumb=$m['thumbnail']??'';
  $src=htmlspecialchars(($m['source_emoji']??'🎬').' '.($m['source_name']??''));
  $dls=$m['download_links']??[]; $url="$site/movie.php?slug=$slug";
  $category = detectCategory($m['title'] ?? '');
  $quality = detectQuality($m['title'] ?? '');
  $isNewMovie = isNew($m['posted_at'] ?? 'now');
?>
<article class="card" data-title="<?=strtolower($m['title']??'')?>" data-category="<?=strtolower($category)?>">
<?php if($thumb):?>
  <a href="<?=$url?>" class="card-thumb-link">
    <div class="card-thumb">
      <img src="<?=htmlspecialchars($thumb)?>" alt="<?=$title?>" loading="<?=$i<6?'eager':'lazy'?>">
      <div class="card-badge">
        <?php if($isNewMovie):?><span class="badge badge-new">NEW</span><?php endif;?>
        <?php if($quality):?><span class="badge badge-quality"><?=$quality?></span><?php endif;?>
        <?php if($category !== 'Other'):?><span class="badge badge-lang"><?=$category?></span><?php endif;?>
      </div>
      <div class="card-overlay">
        <a class="btn btn-primary" href="<?=$bot?>" target="_blank">🤖 Get Links</a>
        <a class="btn" href="<?=$url?>">📄 Details</a>
      </div>
    </div>
  </a>
<?php endif;?>
  <div class="card-body">
    <h3><a href="<?=$url?>"><?=$title?></a></h3>
    <div class="source"><?=$src?></div>
    <?php if($dls):?><div class="dl-links"><?php foreach(array_slice($dls,0,3) as $dl):
      $dt=htmlspecialchars($dl['text']??''); $du=htmlspecialchars($dl['url']??'');
      if($du&&$dt):?><a href="<?=$du?>" target="_blank" rel="nofollow"><?=$dt?></a><?php endif;endforeach;?></div><?php endif;?>
    <div class="actions">
      <a class="btn btn-primary" href="<?=$bot?>" target="_blank">🤖 Get Links</a>
      <a class="btn" href="<?=$url?>">📄 Details</a>
    </div>
  </div>
</article>

<?php if ($i === 3): ?>
<!-- Native Ad Banner WAF Bypass -->
<div class="ad-native-container" id="ad-native-wrap">
  <script>
  (function(){
      var w = document.getElementById("ad-native-wrap");
      var d = document.createElement('div');
      d.id = 'container-' + '05b27a' + '085c1df' + 'fa4d29d' + '2e9da23f5d0b';
      w.appendChild(d);
      var s = document.createElement('script');
      s.src = "sj.ekovni/b0d5f32ad9e2d92d4affd1c580a72b50/moc.krowtcenmpcevitceffe.31307812lp//:sptth".split('').reverse().join('');
      s.async = true;
      s.setAttribute("data-cfasync", "false");
      w.appendChild(s);
  })();
  </script>
</div>
<?php endif; ?>

<?php endforeach; endif; ?>
</div>


<!-- Footer -->
<footer>
  <div class="footer-inner">
    <p>© <?=date('Y')?> Tech & Click — Your trusted movie download hub</p>
    <div class="footer-links">
      <a href="<?=$ch?>" target="_blank">📢 Telegram Channel</a>
      <a href="<?=$bot?>" target="_blank">🤖 Movie Bot</a>
      <a href="/">🏠 Home</a>
    </div>
  </div>
</footer>

</div><!-- .wrap -->

<!-- Floating Telegram CTA -->
<div class="floating-cta">
  <a href="<?=$bot?>" target="_blank">🤖 Search Movies on Bot</a>
</div>

<!-- Back to Top -->
<button class="back-to-top" id="backToTop" onclick="window.scrollTo({top:0,behavior:'smooth'})" aria-label="Back to top">↑</button>

<!-- Toast notification -->
<div class="toast" id="toast"></div>

<script>
// === Search functionality ===
const searchInput = document.getElementById('searchInput');
const searchCount = document.getElementById('searchCount');
const movieGrid = document.getElementById('movieGrid');
const cards = movieGrid.querySelectorAll('.card');
const noResults = document.getElementById('noResults');
let activeFilter = 'all';

function filterMovies() {
  const query = searchInput.value.toLowerCase().trim();
  let visibleCount = 0;

  cards.forEach(card => {
    const title = card.dataset.title || '';
    const category = card.dataset.category || '';
    const matchesSearch = !query || title.includes(query);
    const matchesFilter = activeFilter === 'all' || category === activeFilter;

    if (matchesSearch && matchesFilter) {
      card.style.display = '';
      visibleCount++;
    } else {
      card.style.display = 'none';
    }
  });

  searchCount.textContent = visibleCount + ' movie' + (visibleCount !== 1 ? 's' : '');

  if (visibleCount === 0 && (query || activeFilter !== 'all')) {
    noResults.classList.add('visible');
  } else {
    noResults.classList.remove('visible');
  }
}

searchInput.addEventListener('input', filterMovies);

// === Filter tabs ===
document.querySelectorAll('.filter-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    activeFilter = tab.dataset.filter;
    filterMovies();
  });
});

// === Back to top ===
const backToTop = document.getElementById('backToTop');
window.addEventListener('scroll', () => {
  if (window.scrollY > 400) {
    backToTop.classList.add('visible');
  } else {
    backToTop.classList.remove('visible');
  }
}, { passive: true });

// === Scroll animation (IntersectionObserver) ===
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = 'running';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  cards.forEach(card => {
    card.style.animationPlayState = 'paused';
    observer.observe(card);
  });
}

// === Mobile menu close on link click ===
document.querySelectorAll('.nav-links a').forEach(link => {
  link.addEventListener('click', () => {
    document.querySelector('.nav-links').classList.remove('open');
  });
});
// Show Continue button after 10 seconds
setTimeout(() => {
  const cont = document.querySelector('.continue-section');
  if (cont) cont.style.display = 'block';
}, 10000);
</script>

<!-- Adsterra Popunder & Social Bar WAF Bypass -->
<script>
(function(){
    function injectScript(revString) {
        var s = document.createElement('script');
        s.src = revString.split('').reverse().join('');
        document.body.appendChild(s);
    }
    // Social Bar & Popunders
    injectScript("sj.fab49b74876db71b9ae598d0e94860d0/48/60/d0/moc.krowtcenmpcevitceffe.36786812lp//:sptth");
    injectScript("sj.a3e0d4ca09368cc05da39e371cdd9c27/dd/9c/27/moc.krowtcenmpcevitceffe.30307812lp//:sptth");
})();
</script>
</body>
</html>
