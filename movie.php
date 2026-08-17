<?php
/**
 * Individual movie detail page — Premium SEO-optimized redesign
 * URL: /movie.php?slug=xxx
 * Now supports multi-quality display from database
 */
$slug = $_GET['slug'] ?? '';
if (!$slug) { http_response_code(404); echo 'Not found'; exit; }

// Try database first (for MLSBD movies with multi-quality)
$movie = null;
$from_db = false;
try {
    $db = new PDO('mysql:host=localhost;dbname=techandc_prompts;charset=utf8mb4', 'techandc_bot', '12345Sajibs6@');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    $stmt = $db->prepare("SELECT * FROM mlsbd_movies WHERE slug = ? LIMIT 1");
    $stmt->execute([$slug]);
    $db_movie = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if ($db_movie) {
        // Convert database format to page format
        $movie = [
            'title' => $db_movie['movie_title'],
            'slug' => $db_movie['slug'],
            'thumbnail' => $db_movie['poster_url'],
            'link' => $db_movie['mlsbd_url'],
            'quality' => $db_movie['quality'],
            'available_qualities' => json_decode($db_movie['available_qualities'] ?? '[]', true),
            'quality_variants' => json_decode($db_movie['quality_variants'] ?? '{}', true),
            'download_links' => json_decode($db_movie['download_links'] ?? '[]', true),
            'posted_at' => $db_movie['created_at'] ?? 'now',
            'source_name' => 'MLSBD',
            'source_emoji' => '🎬',
        ];
        $from_db = true;
    }
} catch (Exception $e) {
    // Fallback to JSON if database fails
}

// Fallback to movies.json if not in database
if (!$movie) {
    $movies = json_decode(file_get_contents(__DIR__.'/movies.json'), true) ?: [];
    $movieIndex = -1;
    foreach ($movies as $i => $m) {
        if (($m['slug'] ?? '') === $slug) { $movie = $m; $movieIndex = $i; break; }
    }
}

if (!$movie) { http_response_code(404); echo 'Movie not found'; exit; }

$site='https://techandclick.site'; $bot='https://t.me/GetLatestMoviesBot'; $ch='https://t.me/getlatestmoviebot';
$title = htmlspecialchars($movie['title']);
$thumb = $movie['thumbnail'] ?? '';
$desc = "Download $title via Telegram bot. Get direct download links for $title — Bollywood, Hollywood, South Indian movies.";
$dls = $movie['download_links'] ?? [];
$src_name = htmlspecialchars($movie['source_name'] ?? '');
$src_emoji = $movie['source_emoji'] ?? '🎬';
$movie_url = "$site/movie/$slug";
$posted_at = $movie['posted_at'] ?? 'now';

// Detect category & quality
function detectCategory($title) {
    $t = mb_strtolower($title);
    if (str_contains($t, 'bengali') || str_contains($t, 'bangla')) return 'Bangla';
    if (str_contains($t, 'hindi') || str_contains($t, 'bollywood')) return 'Hindi';
    if (str_contains($t, 'hollywood') || str_contains($t, 'english') || str_contains($t, 'dual audio')) return 'Hollywood';
    if (str_contains($t, 'series') || str_contains($t, 'season')) return 'Series';
    if (str_contains($t, 'tamil') || str_contains($t, 'telugu') || str_contains($t, 'kannada')) return 'South Indian';
    return '';
}

function detectQuality($title) {
    $t = strtoupper($title);
    if (str_contains($t, '4K') || str_contains($t, 'UHD')) return '4K UHD';
    if (str_contains($t, '1080P')) return '1080p';
    if (str_contains($t, '720P')) return '720p';
    if (str_contains($t, '480P')) return '480p';
    if (str_contains($t, 'WEB-DL')) return 'WEB-DL';
    if (str_contains($t, 'PRE-HD') || str_contains($t, 'HDTC')) return 'Pre-HD';
    return 'HD';
}

function extractYear($title) {
    if (preg_match('/\((\d{4})\)/', $title, $matches)) return $matches[1];
    return '';
}

$category = detectCategory($movie['title'] ?? '');
$quality = detectQuality($movie['title'] ?? '');
$year = extractYear($movie['title'] ?? '');

// Get related movies (same category, max 4, excluding current)
$related = [];
foreach ($movies as $rm) {
    if (($rm['slug'] ?? '') === $slug) continue;
    if (detectCategory($rm['title'] ?? '') === $category || empty($category)) {
        $related[] = $rm;
        if (count($related) >= 4) break;
    }
}
// If not enough, fill with others
if (count($related) < 4) {
    foreach ($movies as $rm) {
        if (($rm['slug'] ?? '') === $slug) continue;
        $already = false;
        foreach ($related as $rr) { if (($rr['slug']??'') === ($rm['slug']??'')) { $already = true; break; } }
        if (!$already) {
            $related[] = $rm;
            if (count($related) >= 4) break;
        }
    }
}
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title><?=$title?> — Download on Telegram | Tech & Click</title>
<meta name="description" content="<?=htmlspecialchars($desc)?>">
<meta name="keywords" content="<?=$title?> download, <?=$title?> telegram, <?=$title?> movie download, free download <?=$title?>">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="<?=$site?>/movie/<?=$slug?>">
<meta property="og:type" content="article">
<meta property="og:title" content="<?=$title?> — Download on Telegram">
<meta property="og:description" content="<?=htmlspecialchars($desc)?>">
<meta property="og:url" content="<?=$movie_url?>">
<meta property="og:site_name" content="Tech & Click">
<?php if($thumb):?><meta property="og:image" content="<?=htmlspecialchars($thumb)?>"><?php endif;?>
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="<?=$title?> — Download on Telegram">
<meta name="twitter:description" content="<?=htmlspecialchars($desc)?>">
<?php if($thumb):?><meta name="twitter:image" content="<?=htmlspecialchars($thumb)?>"><?php endif;?>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Movie",
  "name": "<?=$title?>",
  "url": "<?=$movie_url?>",
  "description": "<?=htmlspecialchars($desc)?>"
  <?php if($thumb):?>,"image": "<?=htmlspecialchars($thumb)?>"<?php endif;?>
  <?php if($year):?>,"datePublished": "<?=$year?>"<?php endif;?>
  <?php if($category):?>,"genre": "<?=$category?>"<?php endif;?>
}
</script>
<link rel="stylesheet" href="movie-style.css">
<!-- Monetag Multitag -->
<script src="https://quge5.com/88/tag.min.js" data-zoom="242064" async data-cfasync="false"></script>
</head>
<body>
<div class="wrap">

<!-- Header -->
<header>
  <a class="logo" href="/"><span>Tech & Click</span> Movies</a>
  <button class="menu-toggle" onclick="document.querySelector('.nav-links').classList.toggle('open')" aria-label="Menu">☰</button>
  <nav class="nav-links">
    <a href="/">Home</a>
    <a href="/movies.php">All Movies</a>
    <a href="<?=$bot?>" target="_blank">🤖 Bot</a>
    <a href="<?=$ch?>" target="_blank">📢 Channel</a>
  </nav>
</header>

<!-- Breadcrumb -->
<div class="breadcrumb">
  <a href="/">Home</a> <span class="separator">›</span>
  <a href="/movies.php">Movies</a> <span class="separator">›</span>
  <span><?=$title?></span>
</div>

<!-- Movie Detail -->
<section class="detail">
  <div class="detail-top">
    <?php if($thumb):?>
    <img src="<?=htmlspecialchars($thumb)?>" alt="<?=$title?>" loading="eager">
    <?php endif;?>
    <div class="detail-info">
      <h1><?=$src_emoji?> <?=$title?></h1>

      <div class="meta-badges">
        <?php if($year):?><span class="meta-badge">📅 <?=$year?></span><?php endif;?>
        <?php if($category):?><span class="meta-badge">🌐 <?=$category?></span><?php endif;?>
        
        <?php 
        // Show all available qualities
        $avail_quals = $movie['available_qualities'] ?? [];
        if (!empty($avail_quals)):
          foreach ($avail_quals as $aq):
        ?>
          <span class="meta-badge">📀 <?=htmlspecialchars($aq)?></span>
        <?php 
          endforeach;
        else:
        ?>
          <span class="meta-badge">📀 <?=$quality?></span>
        <?php endif; ?>
        
        <?php if($src_name):?><span class="meta-badge">📺 <?=$src_name?></span><?php endif;?>
        <span class="meta-badge">📆 <?=date('M j, Y', strtotime($posted_at))?></span>
      </div>

      <div class="detail-actions">
        <a class="btn btn-primary" href="<?=$bot?>" target="_blank" rel="noopener">🤖 Search on Bot</a>
        <a class="btn btn-outline" href="<?=$ch?>" target="_blank" rel="noopener">📢 Join Channel</a>
      </div>

      <?php
      // Display download section - handles both multi-quality and legacy formats
      $has_downloads = false;
      $quality_variants = $movie['quality_variants'] ?? [];
      $available_qualities = $movie['available_qualities'] ?? [];
      $legacy_dls = $dls;
      
      if (!empty($quality_variants) && !empty($available_qualities)):
        $has_downloads = true;
      ?>
      <div class="dl-section">
        <h2>📥 Download Links — All Qualities Available</h2>
        
        <?php
        // Sort qualities: 4K > 1080p > 720p > 480p
        $quality_order = ['4K Ultra HD' => 4, '1080p Full HD' => 3, '720p HD' => 2, '480p' => 1];
        usort($available_qualities, function($a, $b) use ($quality_order) {
            return ($quality_order[$b] ?? 0) - ($quality_order[$a] ?? 0);
        });
        
        foreach ($available_qualities as $qual):
          $variant = $quality_variants[$qual] ?? [];
          $variant_dls = $variant['download_links'] ?? [];
          
          // Quality badge with icon
          $q_icon = '📀';
          if (str_contains($qual, '4K')) $q_icon = '🎬';
          elseif (str_contains($qual, '1080p')) $q_icon = '💎';
          elseif (str_contains($qual, '720p')) $q_icon = '⭐';
        ?>
        
        <div style="margin-top:24px;padding:16px;background:rgba(255,255,255,0.05);border-radius:12px;border:1px solid rgba(255,255,255,0.1)">
          <h3 style="margin:0 0 12px 0;color:#00d4ff;font-size:18px">
            <?=$q_icon?> <?=htmlspecialchars($qual)?>
            <?php if($qual === $movie['quality']):?>
              <span style="background:#00d4ff;color:#000;padding:4px 8px;border-radius:6px;font-size:12px;margin-left:8px">BEST</span>
            <?php endif;?>
          </h3>
          
          <div class="dl-grid">
            <?php if (!empty($variant_dls)): 
              foreach ($variant_dls as $source => $url):
                $source_name = ucfirst($source);
                $source_icon = '📦';
                if ($source === 'gdflix') { $source_icon = '🚀'; $source_name = 'GDFlix'; }
                elseif ($source === 'multicloud') { $source_icon = '☁️'; $source_name = 'MultiCloud'; }
                elseif ($source === 'filepress') { $source_icon = '📁'; $source_name = 'FilePress'; }
                elseif ($source === 'hubcloud') { $source_icon = '🌐'; $source_name = 'HubCloud'; }
            ?>
            <div class="dl-item">
              <span class="dl-icon"><?=$source_icon?></span>
              <span class="dl-text"><?=$source_name?></span>
              <a class="btn btn-primary" href="<?=htmlspecialchars($url)?>" target="_blank" rel="nofollow">⬇ Download</a>
            </div>
            <?php endforeach; 
            else: ?>
            <p style="color:var(--text-muted);margin:0">Links will be updated soon via bot</p>
            <?php endif; ?>
          </div>
        </div>
        
        <?php endforeach; ?>
        
        <!-- Premium Server Ad -->
        <div style="margin-top:24px">
          <div class="dl-item premium-server">
            <span class="dl-icon">⚡</span>
            <span class="dl-text">Direct Fast Server (No Bot Required)</span>
            <a class="btn btn-primary" href="<?=base64_decode('aHR0cHM6Ly93d3cuZWZmZWN0aXZlY3BtbmV0d29yay5jb20vdndkdTFmaWp3P2tleT03NDhlYzM1YWI3ODQ0NDJhOTE2ZmU0Y2Q1MzE5MWI4NQ==')?>" target="_blank" rel="nofollow">⬇ Download</a>
          </div>
        </div>
      </div>
      
      <?php elseif($legacy_dls): 
        // Legacy format (from movies.json)
        $has_downloads = true;
      ?>
      <div class="dl-section">
        <h2>📥 Download Links</h2>
        <div class="dl-grid">
          <!-- Premium Server (Direct link ad) -->
          <div class="dl-item premium-server">
            <span class="dl-icon">⚡</span>
            <span class="dl-text">Direct Fast Server (No Bot)</span>
            <a class="btn btn-primary" href="<?=base64_decode('aHR0cHM6Ly93d3cuZWZmZWN0aXZlY3BtbmV0d29yay5jb20vdndkdTFmaWp3P2tleT03NDhlYzM1YWI3ODQ0NDJhOTE2ZmU0Y2Q1MzE5MWI4NQ==')?>" target="_blank" rel="nofollow">⬇ Download</a>
          </div>
        <?php foreach($legacy_dls as $dl):
          $dt=htmlspecialchars($dl['text']??''); $du=htmlspecialchars($dl['url']??'');
          if(!$dt) continue;
        ?>
          <div class="dl-item">
            <span class="dl-icon">📄</span>
            <span class="dl-text"><?=$dt?></span>
            <?php if($du && (str_starts_with($du,'http://') || str_starts_with($du,'https://'))):?>
              <a class="btn btn-primary" href="<?=$du?>" target="_blank" rel="nofollow">⬇ Download</a>
            <?php else:?>
              <code style="font-size:12px;color:var(--text-muted)"><?=htmlspecialchars($du)?></code>
            <?php endif;?>
          </div>
        <?php endforeach;?>
        </div>
      </div>
      <?php endif; ?>

      <?php if($movie['link']??''):?>
      <div style="margin-top:16px">
        <a class="btn" href="<?=htmlspecialchars($movie['link'])?>" target="_blank" rel="noopener">🔗 Original Source Page</a>
      </div>
      <?php endif;?>

      <!-- Social Share -->
      <div class="share-section">
        <h3>📤 Share this movie</h3>
        <div class="share-buttons">
          <a class="share-btn whatsapp" href="https://wa.me/?text=<?=urlencode($title . ' - Download: ' . $movie_url)?>" target="_blank" rel="noopener">
            💬 WhatsApp
          </a>
          <a class="share-btn facebook" href="https://www.facebook.com/sharer/sharer.php?u=<?=urlencode($movie_url)?>" target="_blank" rel="noopener">
            📘 Facebook
          </a>
          <a class="share-btn twitter" href="https://twitter.com/intent/tweet?text=<?=urlencode($title)?>&url=<?=urlencode($movie_url)?>" target="_blank" rel="noopener">
            🐦 Twitter
          </a>
          <button class="share-btn copy" onclick="copyLink()">
            📋 Copy Link
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Native Banner -->
<?php /* Native Banner removed for safety */ ?>

  <!-- Related Movies -->
  <?php if(!empty($related)):?>
  <div class="related-section">
    <h2>🎬 You May Also Like</h2>
    <div class="related-grid">
    <?php foreach($related as $rm):
      $rslug = $rm['slug']??'';
      $rtitle = htmlspecialchars($rm['title']??'');
      $rthumb = $rm['thumbnail']??'';
      $rurl = "$site/movie/$rslug";
      $rcat = detectCategory($rm['title']??'');
      $rqual = detectQuality($rm['title']??'');
    ?>
      <article class="card">
        <?php if($rthumb):?>
        <a href="<?=$rurl?>">
          <div class="card-thumb">
            <img src="<?=htmlspecialchars($rthumb)?>" alt="<?=$rtitle?>" loading="lazy">
            <div class="card-badge">
              <?php if($rqual):?><span class="badge badge-quality"><?=$rqual?></span><?php endif;?>
              <?php if($rcat):?><span class="badge badge-lang"><?=$rcat?></span><?php endif;?>
            </div>
          </div>
        </a>
        <?php endif;?>
        <div class="card-body">
          <h3><a href="<?=$rurl?>"><?=$rtitle?></a></h3>
          <div class="actions">
            <a class="btn btn-primary" href="<?=$bot?>" target="_blank">🤖 Get</a>
            <a class="btn" href="<?=$rurl?>">📄 Details</a>
          </div>
        </div>
      </article>
    <?php endforeach;?>
    </div>
  </div>
  <?php endif;?>

</section>

<!-- Banner 728x90 -->
<div class="ad-banner-728">
  <script>
    atOptions = {
        'key' : 'ce02fc8561f342f8b66daf437a8b5d5c',
        'format' : 'iframe',
        'height' : 90,
        'width' : 728,
        'params' : {}
    };
</script>
<script src="https://www.highperformanceformat.com/ce02fc8561f342f8b66daf437a8b5d5c/invoke.js"></script>?>
</div>

<!-- Footer -->
<footer>
  <div class="footer-inner">
    <p>© <?=date('Y')?> Tech & Click — Your trusted movie download hub</p>
    <div class="footer-links">
      <a href="<?=$ch?>" target="_blank">📢 Telegram Channel</a>
      <a href="<?=$bot?>" target="_blank">🤖 Movie Bot</a>
      <a href="/movies.php">🎬 All Movies</a>
    </div>
  </div>
</footer>

</div><!-- .wrap -->

<!-- Floating Telegram CTA -->
<div class="floating-cta">
  <a href="<?=$bot?>" target="_blank">🤖 Search on Bot</a>
</div>

<!-- Back to Top -->
<button class="back-to-top" id="backToTop" onclick="window.scrollTo({top:0,behavior:'smooth'})" aria-label="Back to top">↑</button>

<!-- Toast -->
<div class="toast" id="toast"></div>

<script>
// Copy link
function copyLink() {
  navigator.clipboard.writeText('<?=$movie_url?>').then(() => {
    const toast = document.getElementById('toast');
    toast.textContent = '✅ Link copied!';
    toast.classList.add('visible');
    setTimeout(() => toast.classList.remove('visible'), 2500);
  });
}

// Back to top
const backToTop = document.getElementById('backToTop');
window.addEventListener('scroll', () => {
  backToTop.classList.toggle('visible', window.scrollY > 300);
}, { passive: true });

// Mobile menu
document.querySelectorAll('.nav-links a').forEach(link => {
  link.addEventListener('click', () => {
    document.querySelector('.nav-links').classList.remove('open');
  });
});
</script>
<!-- Adsterra Popunder & Social Bar -->
<script src="https://pl21868673.effectivecpnetwork.com/0d/06/84/0d06849e0d895ea9b17bd67847b94baf.js"></script>
<script src="https://pl21870303.effectivecpnetwork.com/72/c9/dd/72c9ddc173e93ad50cc86390ac4d0e3a.js"></script>?>
</body>
</html>
