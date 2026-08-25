#!/usr/bin/env python3
"""
Bangladesh News Scraper + Facebook Auto Poster
================================================
- Scrapes Bangladesh news from international sources via Google News RSS
- Stores in database temporarily
- Posts to Facebook Page with image
- Deletes from database immediately after posting

Cron: */30 * * * * cd /home/techandc/movie_bot_new/ftp_movie_bot && /usr/bin/python3 news_poster.py >> logs/cron_news.log 2>&1
"""

import hashlib
import logging
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import mysql.connector
import requests
from bs4 import BeautifulSoup

# =====================================================
# CONFIGURATION
# =====================================================

FB_PAGE_ID    = "1192585593947865"
FB_ACCESS_TOKEN = "EAAVC90kVmt0BSRu73j1F21qGPfxUPpwPAposPLnbU3L8fsC4esZBFOwaapXJkVLi902NmhR1xM8vZAd31vG5RTfmAVHBjQ1dthmgYj8gYacs3uBtWZBthZBKZADGqUggVLScOjZAvHSChZC0ZCZCgu1Ktb9fATOr7j0Y5zHOLIRLChcQrGX0VeBNYi5hh2si5fQU8tWs1eyQfWceUO8a9yYQtcfg8"
FB_API_BASE   = "https://graph.facebook.com/v19.0"

DB_CONFIG = {
    "host":     "localhost",
    "user":     "techandc_bot",
    "password": "12345Sajibs6@",
    "database": "techandc_prompts",
}

# How many news to post per run
POST_LIMIT = 3

# Delay between posts (seconds) — avoid FB rate limit
POST_DELAY = 10

# Google News RSS sources — Bangladesh news from international + local media
NEWS_SOURCES = [
    # ── International (English) ──
    {
        "name": "Google News - Bangladesh",
        "url": "https://news.google.com/rss/search?q=bangladesh&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "BBC Bangladesh",
        "url": "https://news.google.com/rss/search?q=bangladesh+site:bbc.com&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "Al Jazeera Bangladesh",
        "url": "https://news.google.com/rss/search?q=bangladesh+site:aljazeera.com&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "Reuters Bangladesh",
        "url": "https://news.google.com/rss/search?q=bangladesh+site:reuters.com&hl=en-US&gl=US&ceid=US:en",
    },

    # ── Bangladeshi Newspapers (Bangla) ──
    {
        "name": "Prothom Alo",
        "url": "https://www.prothomalo.com/feed",
    },
    {
        "name": "Daily Jugantor",
        "url": "https://www.jugantor.com/feed/rss.xml",
    },
    {
        "name": "Kaler Kantho",
        "url": "https://www.kalerkantho.com/feed",
    },
    {
        "name": "Samakal",
        "url": "https://samakal.com/feed",
    },
    {
        "name": "Ittefaq",
        "url": "https://www.ittefaq.com.bd/feed",
    },
    {
        "name": "Daily Manabzamin",
        "url": "https://mzamin.com/feed/",
    },

    # ── Bangladeshi Newspapers (English) ──
    {
        "name": "Daily Star BD",
        "url": "https://www.thedailystar.net/frontpage/rss.xml",
    },
    {
        "name": "Dhaka Tribune",
        "url": "https://www.dhakatribune.com/feed",
    },
    {
        "name": "New Age BD",
        "url": "https://www.newagebd.net/feed/rss",
    },

    # ── Google News Bangla ──
    {
        "name": "Google News Bangla - BD",
        "url": "https://news.google.com/rss?hl=bn&gl=BD&ceid=BD:bn",
    },
    {
        "name": "Google News Bangla - Top",
        "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZ4ZERBU0JtSnVMVWRCVWlnQVAB?hl=bn&gl=BD&ceid=BD:bn",
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# =====================================================
# LOGGING
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR  = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"news_{datetime.now().strftime('%Y%m%d')}.log"

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
# DATABASE
# =====================================================

def get_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"DB connection error: {e}")
        return None


def ensure_table(cursor):
    """Create news queue table if not exists"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_queue (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            url_hash    VARCHAR(64) UNIQUE NOT NULL,
            title       TEXT NOT NULL,
            summary     TEXT,
            source      VARCHAR(200),
            news_url    TEXT,
            image_url   TEXT,
            published   VARCHAR(100),
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


def is_already_seen(cursor, url_hash):
    """Check if this news was already processed"""
    cursor.execute(
        "SELECT id FROM news_queue WHERE url_hash = %s LIMIT 1",
        (url_hash,)
    )
    return cursor.fetchone() is not None


def insert_news(cursor, item):
    """Insert news into queue"""
    try:
        cursor.execute("""
            INSERT IGNORE INTO news_queue
                (url_hash, title, summary, source, news_url, image_url, published)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            item["url_hash"],
            item["title"],
            item["summary"],
            item["source"],
            item["url"],
            item.get("image_url", ""),
            item.get("published", ""),
        ))
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Insert error: {e}")
        return False


def get_pending_news(cursor, limit=5):
    """Get news items to post"""
    cursor.execute("""
        SELECT id, title, summary, source, news_url, image_url, published
        FROM news_queue
        ORDER BY created_at ASC
        LIMIT %s
    """, (limit,))
    return cursor.fetchall()


def delete_news(cursor, news_id):
    """Delete news after posting"""
    cursor.execute("DELETE FROM news_queue WHERE id = %s", (news_id,))


# =====================================================
# NEWS SCRAPER
# =====================================================

def make_hash(url):
    return hashlib.md5(url.encode()).hexdigest()


def fetch_og_image(url):
    """Try to get og:image from news article page"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]
        og = soup.find("meta", attrs={"name": "twitter:image"})
        if og and og.get("content"):
            return og["content"]
    except Exception:
        pass
    return None


def scrape_google_news_rss(source):
    """Scrape news items from a Google News RSS feed"""
    items = []
    try:
        r = requests.get(source["url"], headers=HEADERS, timeout=15)
        if r.status_code != 200:
            logger.warning(f"  ⚠️ {source['name']}: HTTP {r.status_code}")
            return items

        root = ET.fromstring(r.content)
        channel = root.find("channel")
        if not channel:
            return items

        for item in channel.findall("item")[:10]:
            title = item.findtext("title", "").strip()
            url   = item.findtext("link", "").strip()
            pub   = item.findtext("pubDate", "").strip()
            desc  = item.findtext("description", "").strip()

            if not title or not url:
                continue

            # Clean description (remove HTML tags)
            summary = BeautifulSoup(desc, "html.parser").get_text(separator=" ").strip()
            summary = summary[:300] if len(summary) > 300 else summary

            # Try to get image from media:content or enclosure
            image_url = ""
            media = item.find("{http://search.yahoo.com/mrss/}content")
            if media is not None:
                image_url = media.get("url", "")
            if not image_url:
                enc = item.find("enclosure")
                if enc is not None:
                    image_url = enc.get("url", "")

            items.append({
                "url_hash":  make_hash(url),
                "title":     title,
                "summary":   summary,
                "source":    source["name"],
                "url":       url,
                "image_url": image_url,
                "published": pub,
            })

        logger.info(f"  📰 {source['name']}: {len(items)} items found")
    except Exception as e:
        logger.error(f"  ❌ {source['name']} error: {e}")

    return items


# =====================================================
# FACEBOOK POSTER
# =====================================================

def build_fb_message(news):
    """Build Facebook post message"""
    title   = news[1]
    summary = news[2] or ""
    source  = news[3] or ""
    url     = news[4]
    pub     = news[6] or ""

    msg  = f"📰 {title}\n\n"

    if summary:
        msg += f"{summary}\n\n"

    if pub:
        msg += f"🕐 {pub}\n"

    if source:
        msg += f"📡 Source: {source}\n"

    msg += f"\n🔗 Read Full Story:\n{url}\n\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📢 Stay updated with the latest Bangladesh & world news!\n"
    msg += f"👍 Like & Follow our page for more updates.\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"#Bangladesh #News #BreakingNews #WorldNews #BangladeshNews"

    return msg


def post_with_photo(message, image_url):
    """Post to Facebook with photo"""
    url = f"{FB_API_BASE}/{FB_PAGE_ID}/photos"
    payload = {
        "url":          image_url,
        "caption":      message,
        "access_token": FB_ACCESS_TOKEN,
    }
    resp = requests.post(url, data=payload, timeout=30)
    data = resp.json()
    if "error" in data:
        raise Exception(data["error"].get("message", str(data)))
    return data


def post_text_only(message, link=None):
    """Post to Facebook as text"""
    url = f"{FB_API_BASE}/{FB_PAGE_ID}/feed"
    payload = {
        "message":      message,
        "access_token": FB_ACCESS_TOKEN,
    }
    if link:
        payload["link"] = link
    resp = requests.post(url, data=payload, timeout=30)
    data = resp.json()
    if "error" in data:
        raise Exception(data["error"].get("message", str(data)))
    return data


def post_news_to_facebook(news, cursor):
    """
    Post a single news item to Facebook.
    Deletes from DB immediately after posting.
    """
    news_id   = news[0]
    title     = news[1]
    image_url = news[5] or ""
    news_url  = news[4] or ""

    try:
        message = build_fb_message(news)

        # Try to get image if not in RSS
        if not image_url and news_url:
            image_url = fetch_og_image(news_url) or ""

        if image_url and image_url.startswith("http"):
            logger.info(f"  📸 Posting with photo: {title[:60]}")
            result = post_with_photo(message, image_url)
        else:
            logger.info(f"  📝 Posting text only: {title[:60]}")
            result = post_text_only(message, link=news_url)

        post_id = result.get("post_id") or result.get("id", "unknown")
        logger.info(f"  ✅ Facebook posted! Post ID: {post_id}")

        # ── Delete immediately after posting ──
        delete_news(cursor, news_id)
        logger.info(f"  🗑️ Deleted from DB (ID: {news_id})")
        return True

    except Exception as e:
        logger.error(f"  ❌ Facebook post failed: {e}")
        # Still delete to avoid re-posting failed items repeatedly
        delete_news(cursor, news_id)
        return False


# =====================================================
# MAIN
# =====================================================

def main():
    logger.info("=" * 60)
    logger.info("📰 BANGLADESH NEWS POSTER — Starting")
    logger.info("=" * 60)

    conn = get_db()
    if not conn:
        return

    cursor = conn.cursor()
    ensure_table(cursor)

    # ── Step 1: Scrape news from all sources ──
    logger.info("\n🔍 Scraping news sources...")
    total_new = 0

    for source in NEWS_SOURCES:
        items = scrape_google_news_rss(source)
        for item in items:
            if not is_already_seen(cursor, item["url_hash"]):
                if insert_news(cursor, item):
                    total_new += 1
        time.sleep(1)

    logger.info(f"✅ Collected {total_new} new news items")

    # ── Step 2: Post to Facebook ──
    pending = get_pending_news(cursor, limit=POST_LIMIT)

    if not pending:
        logger.info("ℹ️ No news to post right now")
        conn.close()
        return

    logger.info(f"\n📤 Posting {len(pending)} news to Facebook...")
    posted = 0
    failed = 0

    for news in pending:
        success = post_news_to_facebook(news, cursor)
        if success:
            posted += 1
        else:
            failed += 1
        time.sleep(POST_DELAY)

    logger.info("\n" + "=" * 60)
    logger.info(f"✅ Posted: {posted}  ❌ Failed: {failed}")
    logger.info("=" * 60)
    conn.close()


if __name__ == "__main__":
    main()
