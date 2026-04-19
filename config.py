"""
Configuration for Telegram Movie Search Bot.
Store all sensitive info here and keep this file outside version control.
"""

# =========================
# Telegram Bot Configuration
# =========================
TELEGRAM_BOT = {
    "bot_token": "8294665841:AAG-MpBou_a3FgHoi0KFMAzWH5JBPwOaqu4",
    "bot_username": "@GetLatestMoviesBot",
}

# =========================
# Force Subscribe Channel
# =========================
FORCE_SUB_CHANNEL = "@getlatestmoviebot"  # Change this to your channel username

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
    "channel": "@getlatestmoviebot",  # Channel to post new uploads
    "check_interval_minutes": 30,     # How often to check for new uploads
    "max_posts_per_check": 5,         # Max new posts per check cycle
    "posted_file": "posted_urls.txt",  # File to track already-posted URLs
}

# =========================
# Release Tracker Settings
# =========================
RELEASE_TRACKER = {
    "enabled": True,
    "channel": "@getlatestmoviebot",   # Channel to post release alerts
    "check_interval_minutes": 60,      # How often to check for new releases
    "delay_hours_after_release": 6,    # Wait 6 hours after release before searching
    "tmdb_url": "https://www.themoviedb.org/movie/upcoming",
    "tracked_file": "tracked_releases.json",  # File to track releases
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
# Movie Sources — All sites searched in parallel
# =========================
# type: "wp" = WordPress search (?s=), "api" = WP REST API, "custom" = site-specific
SITES = [
    # --- BD FTP / Direct Download ---
    {
        "name": "CTGMovies",
        "emoji": "🇧🇩",
        "type": "wp",
        "search_url": "https://ctgmovies.com/?s={query}",
        "base_url": "https://ctgmovies.com",
        "verify_ssl": False,
        "whitelist_domains": ("ftp.ctgfun.com",),
        "aliases": ["http://ctgmovies.com"],
    },
    {
        "name": "CrazyCTG",
        "emoji": "🎬",
        "type": "api",
        "api_url": "http://crazyctg.com/wp-json/wp/v2/posts",
        "base_url": "http://crazyctg.com",
        "whitelist_domains": ("ftp.ctgfun.com",),
        "aliases": [],
    },
    {
        "name": "Elaach",
        "emoji": "🎭",
        "type": "custom",
        "search_url": "https://elaach.com/search?q={query}",
        "base_url": "https://elaach.com",
        "aliases": [],
    },
    # --- Bangla Series / Movies (Hoichoi, Chorki, Bongo etc.) ---
    {
        "name": "NotunMovie",
        "emoji": "📺",
        "type": "wp",
        "search_url": "https://www.notunmovie.link/?s={query}",
        "base_url": "https://www.notunmovie.link",
        "aliases": ["https://notunmovie.com", "https://www.notunmovie.com"],
    },
    {
        "name": "BanglaMovies",
        "emoji": "🎞️",
        "type": "wp",
        "search_url": "https://banglamovies.vip/?s={query}",
        "base_url": "https://banglamovies.vip",
        "aliases": ["https://banglamovies.xyz", "https://banglamovies.cc"],
    },
    {
        "name": "MoviedBD",
        "emoji": "📝",
        "type": "wp",
        "search_url": "https://www.movied.link/?s={query}",
        "base_url": "https://www.movied.link",
        "aliases": ["https://movied.link", "https://www.movied.xyz"],
    },
    {
        "name": "Freedrive",
        "emoji": "💾",
        "type": "wp",
        "search_url": "https://freedrivemovie.sbs/?s={query}",
        "base_url": "https://freedrivemovie.sbs",
        "aliases": [
            "https://freedrivemovie.cfd",
            "https://freedrivemovie.xyz",
            "https://freedrivemovie.store",
            "https://freedrivemovie.com",
        ],
    },
    {
        "name": "Flixmet",
        "emoji": "🎥",
        "type": "wp",
        "search_url": "https://flixmet.net/?s={query}",
        "base_url": "https://flixmet.net",
        "aliases": ["https://flixmet.com", "https://flixmet.xyz"],
    },
    {
        "name": "Fojik",
        "emoji": "🍿",
        "type": "wp",
        "search_url": "https://fojik.site/?s={query}",
        "base_url": "https://fojik.site",
        "aliases": ["https://fojik.com", "https://fojik.xyz"],
    },
]
