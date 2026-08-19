#!/usr/bin/env python3

import logging, re, sys, time, json
from datetime import datetime
from pathlib import Path

import mysql.connector
import requests

TELEGRAM_BOT_TOKEN = "8294665841:AAGA0fldnAJj0dazXQsa9p67HARnqACwW0E"
TELEGRAM_CHANNEL = "@newmoviesarena4u"
MOVIE_SITE_URL = "https://movies.techandclick.site"

DB_CONFIG = {
    "host": "localhost",
    "user": "techandc_bot",
    "password": "12345Sajibs6@",
    "database": "techandc_prompts",
}

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"delivery_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ── Facebook poster (safe import) ── DISABLED
FB_ENABLED = False
# try:
#     from facebook_poster import post_movie_to_facebook
#     FB_ENABLED = True
#     logger.info("📘 Facebook poster loaded")
# except ImportError:
#     FB_ENABLED = False
#     logger.warning("⚠️ facebook_poster.py not found — Facebook posting disabled")

# ── YouTube trailer (safe import) ──
try:
    from youtube_trailer import get_youtube_trailer
    YT_ENABLED = True
    logger.info("🎬 YouTube trailer fetcher loaded")
except ImportError:
    YT_ENABLED = False
    logger.warning("⚠️ youtube_trailer.py not found — trailer fetching disabled")


def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"DB error: {e}")
        return None


def get_unposted_movies(cursor, limit=5):
    try:
        cursor.execute("""
            SELECT id, movie_title, slug, poster_url, quality, year,
                   available_qualities
            FROM mlsbd_movies
            WHERE (telegram_message_ids IS NULL OR telegram_message_ids = '')
            AND status = 'completed'
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Query error: {e}")
        return []


def send_to_telegram(movie_data, trailer_url=None):
    try:
        movie_id, title, slug, poster_url, quality, year, _ = movie_data

        url = f"{MOVIE_SITE_URL}/{slug}"

        caption = f"🎬 **{title}**\n"
        caption += f"📺 Quality: {quality}\n"
        if year:
            caption += f"📅 Year: {year}\n"
        caption += f"\n🔗 [Watch & Download]({url})"

        if trailer_url:
            caption += f"\n🎥 [Watch Trailer]({trailer_url})"

        # Check if poster_url is valid
        has_poster = (
            poster_url and
            isinstance(poster_url, str) and
            poster_url.startswith('http') and
            poster_url != 'N/A'
        )

        if has_poster:
            api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            data = {
                'chat_id': TELEGRAM_CHANNEL,
                'photo': poster_url,
                'caption': caption,
                'parse_mode': 'Markdown',
            }
        else:
            api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': TELEGRAM_CHANNEL,
                'text': caption,
                'parse_mode': 'Markdown',
            }

        r = requests.post(api_url, data=data, timeout=10)
        if r.status_code == 200:
            result = r.json()
            if result.get('ok'):
                message_id = result['result']['message_id']
                logger.info(f"✅ Telegram posted: {title}")
                return message_id
        else:
            logger.error(f"Telegram error: {r.status_code} - {r.text}")
        return None

    except Exception as e:
        logger.error(f"Send error: {e}")
        return None


def mark_as_posted(cursor, movie_id, message_id):
    try:
        cursor.execute("""
            UPDATE mlsbd_movies
            SET telegram_message_ids = %s
            WHERE id = %s
        """, (str(message_id), movie_id))
    except Exception as e:
        logger.error(f"Update error: {e}")


def main():
    logger.info("📤 Starting Telegram delivery...")

    db_conn = get_db_connection()
    if not db_conn:
        return

    cursor = db_conn.cursor()
    movies = get_unposted_movies(cursor, limit=10)

    if not movies:
        logger.info("ℹ️ No new movies to post")
        db_conn.close()
        return

    logger.info(f"📋 Found {len(movies)} unposted movies")

    posted_count = 0
    fb_count = 0

    for movie_data in movies:
        movie_id = movie_data[0]
        title    = movie_data[1]
        slug     = movie_data[2]
        poster   = movie_data[3]
        quality  = movie_data[4]
        year     = movie_data[5]
        avail_q_raw = movie_data[6]

        # ── Step 1: YouTube Trailer ──
        trailer_url = None
        if YT_ENABLED:
            trailer_url = get_youtube_trailer(title, year)

        # ── Step 2: Telegram ──
        message_id = send_to_telegram(movie_data, trailer_url=trailer_url)
        if message_id:
            mark_as_posted(cursor, movie_id, message_id)
            posted_count += 1

            # ── Step 2: Facebook (runs right after Telegram) ──
            if FB_ENABLED:
                try:
                    avail_q = json.loads(avail_q_raw or '[]')
                except Exception:
                    avail_q = []

                fb_movie = {
                    "title":               title,
                    "quality":             quality,
                    "available_qualities": avail_q,
                    "year":                year,
                    "slug":                slug,
                    "poster_url":          poster,
                    "trailer_url":         trailer_url,
                }
                ok = post_movie_to_facebook(fb_movie)
                if ok:
                    fb_count += 1

            time.sleep(3)  # Delay between posts

    db_conn.close()
    logger.info(f"✅ Telegram: {posted_count} posted | 📘 Facebook: {fb_count} posted")


if __name__ == "__main__":
    main()
