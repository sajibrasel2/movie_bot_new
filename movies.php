<?php
$movies = json_decode(file_get_contents(__DIR__.'/movies.json'), true) ?: [];
$site='https://techandclick.site'; $bot='https://t.me/GetLatestMoviesBot'; $ch='https://t.me/getlatestmoviebot';
?>
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Latest Movies Download — Telegram Bot | Tech & Click</title>
<meta name="description" content="Download latest Bollywood, Hollywood, South Indian movies & series via Telegram bot. One click to channel.">
<meta name="keywords" content="movie download telegram, latest movie download, bollywood movie telegram, free movie download bot">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="<?=$site?>/movies">
<meta property="og:title" content="Latest Movies Download — Telegram Bot"><meta property="og:url" content="<?=$site?>/movies">
<link rel="stylesheet" href="movie-style.css">
</head><body>
<div class="wrap">
<header><a class="logo" href="/"><span>Tech & Click</span> Movies</a>
<nav class="nav-links"><a href="/">Home</a><a href="<?=$bot?>" target="_blank">Open Bot</a><a href="<?=$ch?>" target="_blank">Channel</a></nav></header>
<section class="hero"><h1>🎬 Latest Movie Downloads on Telegram</h1>
<p>Bollywood, Hollywood, South Indian movies & web series — search on our bot or click below.</p>
<a class="btn btn-primary" href="<?=$bot?>" target="_blank">🤖 Search on Bot</a>
<a class="btn" href="<?=$ch?>" target="_blank">📢 Join Channel</a></section>
<div class="grid">
<?php if(empty($movies)):?><div class="empty"><p>No movies yet. Check back soon!</p></div>
<?php else: foreach($movies as $m):
  $slug=$m['slug']??''; $title=htmlspecialchars($m['title']??''); $thumb=$m['thumbnail']??'';
  $src=htmlspecialchars(($m['source_emoji']??'🎬').' '.($m['source_name']??''));
  $dls=$m['download_links']??[]; $url="$site/movie/$slug";
?>
<article class="card">
<?php if($thumb):?><a href="<?=$url?>"><img src="<?=htmlspecialchars($thumb)?>" alt="<?=htmlspecialchars($title)?>" loading="lazy"></a><?php endif;?>
<div class="card-body">
<h3><a href="<?=$url?>"><?=$title?></a></h3>
<div class="source"><?=$src?></div>
<?php if($dls):?><div class="dl-links"><?php foreach(array_slice($dls,0,3) as $dl):
  $dt=htmlspecialchars($dl['text']??''); $du=htmlspecialchars($dl['url']??'');
  if($du&&$dt):?><a href="<?=$du?>" target="_blank" rel="nofollow"><?=$dt?></a><?php endif;endforeach;?></div><?php endif;?>
<div class="actions">
<a class="btn btn-primary" href="<?=$bot?>" target="_blank">🤖 Get Links</a>
<a class="btn" href="<?=$url?>">📄 Details</a></div>
</div></article>
<?php endforeach;endif;?></div>
<footer>© <?=date('Y')?> Tech & Click — <a href="<?=$ch?>" target="_blank">Telegram Channel</a></footer>
</div></body></html>
