"""
Configuration for Telegram Movie Search Bot.
Store all sensitive info here and keep this file outside version control.
"""

# =========================
# Telegram Bot Configuration
# =========================
TELEGRAM_BOT = {
    "bot_token": "8294665841:AAGA0fldnAJj0dazXQsa9p67HARnqACwW0E",
    "bot_username": "@GetLatestMoviesBot",
}

# =========================
# Force Subscribe Channel
# =========================
FORCE_SUB_CHANNEL = "@newmoviesarena4u"  # Channel username

# =========================
# Common Settings
# =========================
COMMON = {
    "timeout": 15,
    "max_results": 5,
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
}

# =========================
# Auto-Poster Settings
# =========================
AUTO_POSTER = {
    "enabled": True,
    "channel": "@newmoviesarena4u",  # Channel to post new uploads
    "check_interval_minutes": 30,     # How often to check for new uploads
    "max_posts_per_check": 5,         # Max new posts per check cycle
    "posted_file": "posted_urls.txt",  # File to track already-posted URLs
}

# =========================
# Release Tracker Settings
# =========================
RELEASE_TRACKER = {
    "enabled": True,
    "channel": "@newmoviesarena4u",   # Channel to post release alerts
    "check_interval_minutes": 60,      # How often to check for new releases
    "delay_hours_after_release": 6,    # Wait 6 hours after release before searching
    "tmdb_url": "https://www.themoviedb.org/movie/upcoming",
    "tracked_file": "tracked_releases.json",  # File to track releases
}

# =========================
# Website Posting Settings
# =========================
WEBSITE = {
    "enabled": True,
    "api_url": "https://techandclick.site/api.php",
    "secret": "tc_movie_2026_secret",
}

# =========================
# Source 1: ctgmovies.com (Bangla/Hindi/South Indian)
# =========================
CTGMOVIES = {
    "name": "CTGMovies",
    "emoji": "🇧🇩",
    "base_url": "https://ctgmovies.com",
    "search_url": "https://ctgmovies.com/?s={query}",
    "verify_ssl": False,  # Expired SSL certificate
}

# =========================
# Source 2: YTS.lt (Hollywood - Torrent)
# =========================
YTS = {
    "name": "YTS",
    "emoji": "🌍",
    "api_url": "https://yts.lt/api/v2/list_movies.json",
    "base_url": "https://yts.lt",
}

# =========================
# Source 3: BitSearch.to (All types - Magnet)
# =========================
BITSEARCH = {
    "name": "BitSearch",
    "emoji": "🧲",
    "search_url": "https://bitsearch.to/search?q={query}&category=1",
    "base_url": "https://bitsearch.to",
}

# =========================
# Movie Sources — Search only from our own site
# =========================
# type: "custom" for movies.techandclick.site database search
SITES = [
    {
        "name": "TechAndClick Movies",
        "emoji": "🎬",
        "type": "custom",
        "search_url": "https://movies.techandclick.site/api/search.php?q={query}",
        "base_url": "https://movies.techandclick.site",
        "aliases": [],
    },
]
