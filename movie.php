<?php
/**
 * Individual movie detail page — SEO-optimized
 * URL: /movie/{slug} (rewritten by .htaccess)
 */
$slug = $_GET['slug'] ?? '';
if (!$slug) { http_response_code(404); echo 'Not found'; exit; }

$movies = json_decode(file_get_contents(__DIR__.'/movies.json'), true) ?: [];
$movie = null;
foreach ($movies as $m) {
    if (($m['slug'] ?? '') === $slug) { $movie = $m; break; }
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
?>
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title><?=$title?> — Download on Telegram | Tech & Click</title>
<meta name="description" content="<?=htmlspecialchars($desc)?>">
<meta name="keywords" content="<?=htmlspecialchars($title)?> download, <?=htmlspecialchars($title)?> telegram, <?=htmlspecialchars($title)?> movie download">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="<?=$movie_url?>">
<meta property="og:type" content="article">
<meta property="og:title" content="<?=$title?> — Download on Telegram">
<meta property="og:description" content="<?=htmlspecialchars($desc)?>">
<meta property="og:url" content="<?=$movie_url?>">
<?php if($thumb):?><meta property="og:image" content="<?=htmlspecialchars($thumb)?>"><?php endif;?>
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="<?=$title?> — Download on Telegram">
<script type="application/ld+json">
{
  "@context":"https://schema.org",
  "@type":"Movie",
  "name":<?=$title?>,
  "url":"<?=$movie_url?>",
  "description":"<?=htmlspecialchars($desc)?>"
  <?php if($thumb):?>,"image":"<?=htmlspecialchars($thumb)?>"<?php endif;?>
}
</script>
<link rel="stylesheet" href="movie-style.css">
</head><body>
<div class="wrap">
<header><a class="logo" href="/"><span>Tech & Click</span> Movies</a>
<nav class="nav-links"><a href="/">Home</a><a href="/movies">All Movies</a><a href="<?=$bot?>" target="_blank">Open Bot</a></nav></header>

<div class="breadcrumb">
<a href="/">Home</a> › <a href="/movies">Movies</a> › <?=$title?>
</div>

<section class="detail">
<div class="detail-top">
<?php if($thumb):?><img src="<?=htmlspecialchars($thumb)?>" alt="<?=$title?>" loading="lazy"><?php endif;?>
<div class="detail-info">
<h1><?=$src_emoji?> <?=$title?></h1>
<div class="source">Source: <?=$src_name?> • Posted: <?=date('M j, Y', strtotime($movie['posted_at']??'now'))?></div>
<a class="btn btn-primary" href="<?=$bot?>" target="_blank" rel="noopener">🤖 Search on Bot</a>
<a class="btn" href="<?=$ch?>" target="_blank" rel="noopener">📢 Join Channel</a>

<?php if($dls):?>
<div class="dl-section">
<h2>📥 Download Links</h2>
<div class="dl-grid">
<?php foreach($dls as $dl):
  $dt=htmlspecialchars($dl['text']??''); $du=htmlspecialchars($dl['url']??'');
  if(!$dt) continue;
?>
<div class="dl-item">
<span class="dl-text"><?=$dt?></span>
<?php if($du && (str_starts_with($du,'http://')||str_starts_with($du,'https://'))):?>
<a class="btn btn-primary" href="<?=$du?>" target="_blank" rel="nofollow">Download</a>
<?php else:?>
<code style="font-size:12px;color:var(--muted)"><?=htmlspecialchars($du)?></code>
<?php endif;?>
</div>
<?php endforeach;?></div></div><?php endif;?>

<?php if($movie['link']??''):?>
<div style="margin-top:16px"><a class="btn" href="<?=htmlspecialchars($movie['link'])?>" target="_blank" rel="noopener">🔗 Movie Page</a></div>
<?php endif;?>
</div></div>
</section>
<footer>© <?=date('Y')?> Tech & Click — <a href="<?=$ch?>" target="_blank">Telegram Channel</a></footer>
</div></body></html>
