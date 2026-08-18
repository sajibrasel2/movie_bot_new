#!/usr/bin/env python3
"""
Facebook Page Auto Poster
==========================
Posts movie updates to Facebook Page simultaneously with Telegram delivery.
Uses Facebook Graph API v19.0.

Usage:
  - Called automatically from send_movie_to_telegram.py after Telegram post
  - Can also run standalone: python3 facebook_poster.py
  - Error in Facebook post will NOT stop Telegram delivery
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import mysql.connector
import requests

# =====================================================
# CONFIGURATION
# =====================================================

FB_PAGE_ID = "1180939241780131"
FB_ACCESS_TOKEN = "EAAWORJ63XloBSW4o0kUPHNiYykw2Y09n1ZC7girCAZAmjRqDcAQvTdX7cD6sBB2gZBu26ZBjwg9E7LZAh0oYvRayyZCbXlKhsG8tZAAzmZAikX46RxzzMCx7KIRamxfF30lam5ysXdiLvZBI729Par7TVZAFQk3xzV9soRI3UYZBgul1wPpt093QZBAD2aBtcJFAbjZC4mP45lFiZAp03AzWqQZCM5O"
FB_API_VERSION = "v19.0"
FB_API_BASE = f"https://graph.facebook.com/{FB_API_VERSION}"

# Telegram channel/bot link for download CTA
TELEGRAM_CHANNEL = "https://t.me/getlatestmoviebot"
MOVIE_SITE_URL = "https://movies.techandclick.site"

DB_CONFIG = {
    "host": "localhost",
    "user": "techandc_bot",
    "password": "12345Sajibs6@",
    "database": "techandc_prompts",
}

# =====================================================
# LOGGING
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"facebook_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# =====================================================
# FACEBOOK API FUNCTIONS
# =====================================================

def post_photo_to_facebook(poster_url: str, message: str) -> dict:
    """
    Post a photo with caption to Facebook Page.
    Uses /photos endpoint which supports image URL + caption.
    Returns dict with 'id' on success, or raises exception.
    """
    url = f"{FB_API_BASE}/{FB_PAGE_ID}/photos"
    payload = {
        "url": poster_url,
        "caption": message,
        "access_token": FB_ACCESS_TOKEN,
    }
    resp = requests.post(url, data=payload, timeout=30)
    data = resp.json()

    if resp.status_code != 200 or "error" in data:
        error_msg = data.get("error", {}).get("message", resp.text)
        raise Exception(f"Facebook API error: {error_msg}")

    return data


def post_text_to_facebook(message: str, link: str = None) -> dict:
    """
    Post text (+ optional link) to Facebook Page feed.
    Fallback when no poster image is available.
    """
    url = f"{FB_API_BASE}/{FB_PAGE_ID}/feed"
    payload = {
        "message": message,
        "access_token": FB_ACCESS_TOKEN,
    }
    if link:
        payload["link"] = link

    resp = requests.post(url, data=payload, timeout=30)
    data = resp.json()

    if resp.status_code != 200 or "error" in data:
        error_msg = data.get("error", {}).get("message", resp.text)
        raise Exception(f"Facebook API error: {error_msg}")

    return data


# =====================================================
# MESSAGE FORMATTER
# =====================================================

def build_facebook_message(movie: dict) -> str:
    """
    Build a nicely formatted Facebook post message.
    movie dict keys: title, quality, available_qualities, year, slug, poster_url
    """
    title    = movie.get("title", "Unknown Movie")
    quality  = movie.get("quality", "")
    avail_q  = movie.get("available_qualities", [])
    year     = movie.get("year", "")
    slug     = movie.get("slug", "")

    movie_url = f"{MOVIE_SITE_URL}/{slug}" if slug else MOVIE_SITE_URL

    # Quality display
    if avail_q and len(avail_q) > 1:
        quality_line = " | ".join(avail_q)
    elif quality:
        quality_line = quality
    else:
        quality_line = "HD"

    msg = f"🎬 {title}\n\n"

    if year:
        msg += f"📅 Year: {year}\n"

    msg += f"📀 Quality: {quality_line}\n\n"
    msg += f"📥 Download Links Available!\n"
    msg += f"👉 {movie_url}\n\n"
    msg += f"🤖 Get via Telegram Bot:\n"
    msg += f"👉 {TELEGRAM_CHANNEL}\n\n"
    msg += f"#Movie #Download #FreMovies #BollywoodMovies #HollywoodMovies"

    return msg


# =====================================================
# MAIN POST FUNCTION (called from send_movie_to_telegram.py)
# =====================================================

def post_movie_to_facebook(movie: dict) -> bool:
    """
    Post a single movie to Facebook Page.
    This is the main entry point called after Telegram delivery.

    Args:
        movie: dict with keys: title, quality, available_qualities,
               year, slug, poster_url

    Returns:
        True on success, False on failure (does NOT raise)
    """
    title = movie.get("title", "Unknown")
    try:
        message = build_facebook_message(movie)
        poster_url = movie.get("poster_url", "")

        if poster_url and poster_url.startswith("http"):
            logger.info(f"  📘 Posting to Facebook with photo: {title}")
            result = post_photo_to_facebook(poster_url, message)
        else:
            logger.info(f"  📘 Posting to Facebook (text only): {title}")
            movie_url = f"{MOVIE_SITE_URL}/{movie.get('slug', '')}"
            result = post_text_to_facebook(message, link=movie_url)

        post_id = result.get("post_id") or result.get("id", "unknown")
        logger.info(f"  ✅ Facebook posted successfully! Post ID: {post_id}")
        return True

    except Exception as e:
        # Log error but do NOT crash — Telegram delivery must continue
        logger.error(f"  ❌ Facebook post failed for '{title}': {e}")
        return False


# =====================================================
# STANDALONE MODE — post unposted movies from DB
# =====================================================

def get_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"DB error: {e}")
        return None


def run_standalone():
    """
    Standalone mode: finds Telegram-posted movies not yet on Facebook,
    and posts them. Run via cron or manually.
    """
    logger.info("=" * 60)
    logger.info("📘 FACEBOOK POSTER — Standalone Mode")
    logger.info("=" * 60)

    conn = get_db()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)

    # Get movies posted to Telegram but not yet to Facebook
    cursor.execute("""
        SELECT id, movie_title, slug, poster_url, quality,
               available_qualities, year
        FROM mlsbd_movies
        WHERE telegram_message_ids IS NOT NULL
          AND (facebook_post_id IS NULL OR facebook_post_id = '')
          AND status = 'completed'
          AND poster_url IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 10
    """)
    movies = cursor.fetchall()

    if not movies:
        logger.info("No new movies to post to Facebook.")
        conn.close()
        return

    logger.info(f"Found {len(movies)} movies to post to Facebook")
    success = 0
    failed = 0

    for row in movies:
        # Parse available_qualities JSON
        try:
            avail_q = json.loads(row.get("available_qualities") or "[]")
        except Exception:
            avail_q = []

        movie = {
            "title": row["movie_title"],
            "quality": row["quality"],
            "available_qualities": avail_q,
            "year": row.get("year"),
            "slug": row["slug"],
            "poster_url": row["poster_url"],
        }

        ok = post_movie_to_facebook(movie)

        if ok:
            # Try to save post ID (optional — column may not exist)
            try:
                cursor.execute(
                    "UPDATE mlsbd_movies SET facebook_post_id = %s WHERE id = %s",
                    ("posted", row["id"])
                )
            except Exception:
                pass  # Column may not exist yet, that's fine
            success += 1
        else:
            failed += 1

        time.sleep(2)  # Respect Facebook rate limits

    logger.info(f"✅ Posted: {success}  ❌ Failed: {failed}")
    conn.close()


if __name__ == "__main__":
    run_standalone()
