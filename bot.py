"""
Telegram Movie Search Bot — Multi-Source (Generic)
Reads all sources from config.SITES and searches them in parallel.
Uses python-telegram-bot v20+ (async).
"""

import asyncio
import logging
import re
import urllib.parse
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from html import escape as html_escape

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from config import TELEGRAM_BOT, FORCE_SUB_CHANNEL, COMMON, SITES, AUTO_POSTER, RELEASE_TRACKER

# =========================
# Logging
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# =========================
# Download Link Extraction
# =========================
DOWNLOAD_KEYWORDS = (
    "download", "gdrive", "mega", "direct", "720p", "1080p",
    "480p", "link", "drive", "server", "x264", "x265",
    "hevc", "webrip", "bluray", "brrip", "watch",
)
_SKIP_HREF_PATTERNS = (
    "?cat=", "?tag=", "?page=", "?p=", "/category/", "/tag/",
    "#", "javascript:", "mailto:",
)


def _extract_download_links_from_page(page_url: str, headers: dict,
                                       verify: bool = False,
                                       whitelist_domains: tuple = (),
                                       skip_local_172: bool = False) -> List[Dict[str, str]]:
    """Scrape download links from a movie detail page."""
    try:
        resp = requests.get(page_url, headers=headers, timeout=COMMON["timeout"], verify=verify)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Page scrape error for %s: %s", page_url, exc)
        return []
    soup = BeautifulSoup(resp.text, "lxml")
    content = (
        soup.select_one("article") or soup.select_one(".entry-content")
        or soup.select_one(".post-content") or soup.body
    )
    if not content:
        return []
    download_links = []
    for a_tag in content.select("a"):
        href = (a_tag.get("href") or "").strip()
        text = a_tag.get_text(strip=True)
        if not href or not text:
            continue
        if any(pat in href.lower() for pat in _SKIP_HREF_PATTERNS):
            continue
        if href.rstrip("/") == page_url.rstrip("/"):
            continue
        combined = (text + " " + href).lower()
        if any(kw in combined for kw in DOWNLOAD_KEYWORDS):
            # Skip local-only IPs
            if skip_local_172 and href.startswith("http://172."):
                continue
            # Apply whitelist filter if specified
            if whitelist_domains:
                if not any(domain in href for domain in whitelist_domains):
                    continue
            if not any(dl["url"] == href for dl in download_links):
                download_links.append({"text": text, "url": href})
    return download_links


def _get_thumbnail_from_page(page_url: str, headers: dict,
                              base_url: str = "", verify: bool = False) -> str:
    """Get thumbnail from a detail page (og:image or first img)."""
    try:
        resp = requests.get(page_url, headers=headers, timeout=COMMON["timeout"], verify=verify)
        resp.raise_for_status()
    except Exception:
        return ""
    soup = BeautifulSoup(resp.text, "lxml")
    # Try og:image first
    og_img = soup.select_one("meta[property='og:image']")
    if og_img:
        thumb = og_img.get("content", "")
        if thumb and "logo" not in thumb.lower() and "default" not in thumb.lower():
            return thumb
    # Try article img
    img_tag = (
        soup.select_one("article img") or soup.select_one(".entry-content img")
        or soup.select_one("img.wp-post-image") or soup.select_one("img")
    )
    if img_tag:
        thumb = img_tag.get("src", "") or img_tag.get("data-src", "") or img_tag.get("data-lazy-src", "")
        if thumb and "logo" not in thumb.lower() and "default" not in thumb.lower():
            # Convert relative to absolute
            if thumb and not thumb.startswith(("http://", "https://")):
                thumb = base_url.rstrip("/") + "/" + thumb.lstrip("/")
            return thumb
    return ""


# =========================
# URL Fallback — tries primary, then aliases
# =========================

def _try_url_with_fallback(primary_url: str, aliases: list, headers: dict,
                            timeout: int = 15, verify: bool = False) -> Optional[requests.Response]:
    """Try primary URL, then each alias. Return first successful response or None."""
    urls_to_try = [primary_url] + aliases
    for url in urls_to_try:
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, verify=verify, allow_redirects=True)
            resp.raise_for_status()
            if len(resp.text) > 500:  # Valid page, not a blank/parked page
                return resp
        except requests.RequestException:
            continue
    return None


def _build_alias_urls(site: dict, url_template: str, query_encoded: str) -> list:
    """Build alias URLs by replacing base_url with each alias domain."""
    aliases = site.get("aliases", [])
    base = site.get("base_url", "")
    alias_urls = []
    for alias in aliases:
        alias_url = url_template.replace(base, alias)
        alias_urls.append(alias_url)
    return alias_urls


# =========================
# Generic Site Searchers
# =========================

def _search_wp(site: dict, query: str) -> List[Dict]:
    """Search a WordPress site using ?s= query parameter."""
    encoded = urllib.parse.quote_plus(query)
    url = site["search_url"].format(query=encoded)
    headers = {"User-Agent": COMMON["user_agent"]}
    verify = site.get("verify_ssl", True)
    whitelist = site.get("whitelist_domains", ())

    # Build alias search URLs
    alias_urls = _build_alias_urls(site, url, encoded)

    resp = _try_url_with_fallback(url, alias_urls, headers, timeout=COMMON["timeout"], verify=verify)
    if not resp:
        logger.error("%s: all URLs failed (primary + %d aliases)", site["name"], len(alias_urls))
        return []

    # Determine which base_url actually worked (for link resolution)
    working_base = site["base_url"]
    for alias in site.get("aliases", []):
        if alias in resp.url:
            working_base = alias
            break

    soup = BeautifulSoup(resp.text, "lxml")
    results = []
    articles = soup.select("article") or soup.select("div.post-item") or soup.select("div.post")
    for article in articles[:COMMON["max_results"]]:
        title_tag = (
            article.select_one("h2.entry-title a") or article.select_one("h3.entry-title a")
            or article.select_one("h2 a") or article.select_one("h3 a")
            or article.select_one(".entry-title a") or article.select_one("a[rel='bookmark']")
        )
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        link = title_tag.get("href", "")
        if not title or not link or "/go/" in link or "/redirect/" in link:
            continue

        # Thumbnail from search page
        img_tag = article.select_one("img")
        thumbnail = ""
        if img_tag:
            thumbnail = (
                img_tag.get("src", "") or img_tag.get("data-src", "")
                or img_tag.get("data-lazy-src", "")
            )
            if thumbnail and not thumbnail.startswith(("http://", "https://")):
                thumbnail = working_base.rstrip("/") + "/" + thumbnail.lstrip("/")
            # Fix relative links that use old base_url
            if site["base_url"] != working_base and thumbnail.startswith(site["base_url"]):
                thumbnail = thumbnail.replace(site["base_url"], working_base)

        # Fix detail page links if alias was used
        detail_link = link
        if site["base_url"] != working_base and link.startswith(site["base_url"]):
            detail_link = link.replace(site["base_url"], working_base)

        # Scrape detail page for thumbnail + download links
        download_links = []
        try:
            better_thumb = _get_thumbnail_from_page(detail_link, headers, working_base, verify)
            if better_thumb:
                thumbnail = better_thumb
            download_links = _extract_download_links_from_page(
                detail_link, headers, verify=verify, whitelist_domains=whitelist
            )
        except Exception as exc:
            logger.error("%s detail error: %s", site["name"], exc)

        # Convert https to http for ctgmovies (SSL expired)
        movie_url = detail_link
        if "ctgmovies.com" in detail_link:
            movie_url = detail_link.replace("https://ctgmovies.com", "http://ctgmovies.com")

        results.append({
            "source": site["name"],
            "emoji": site["emoji"],
            "title": title,
            "link": movie_url,
            "thumbnail": thumbnail,
            "download_links": download_links,
        })
    return results


def _search_api(site: dict, query: str) -> List[Dict]:
    """Search a WordPress site using REST API."""
    headers = {"User-Agent": COMMON["user_agent"]}
    whitelist = site.get("whitelist_domains", ())

    # Build alias API URLs
    base = site.get("base_url", "")
    alias_api_urls = []
    for alias in site.get("aliases", []):
        alias_api = site["api_url"].replace(base, alias)
        alias_api_urls.append(alias_api)

    api_urls = [site["api_url"]] + alias_api_urls
    posts = []
    working_base = site["base_url"]

    for api_url in api_urls:
        try:
            resp = requests.get(
                api_url,
                params={"search": query, "per_page": COMMON["max_results"]},
                headers=headers,
                timeout=COMMON["timeout"],
                verify=False,
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                posts = data
                # Detect working base from URL
                for alias in site.get("aliases", []):
                    if alias in resp.url:
                        working_base = alias
                        break
                break
        except Exception:
            continue

    if not posts:
        logger.error("%s: all API URLs failed", site["name"])
        return []

    results = []
    for post in posts[:COMMON["max_results"]]:
        title_html = post.get("title", {}).get("rendered", "")
        title = BeautifulSoup(title_html, "lxml").get_text(strip=True)
        link = post.get("link", "")
        if not title or not link:
            continue

        thumbnail = ""
        download_links = []
        # Fix link if alias was used
        detail_link = link
        if site["base_url"] != working_base and link.startswith(site["base_url"]):
            detail_link = link.replace(site["base_url"], working_base)
        try:
            thumbnail = _get_thumbnail_from_page(detail_link, headers, working_base, verify=False)
            download_links = _extract_download_links_from_page(
                detail_link, headers, verify=False, whitelist_domains=whitelist
            )
        except Exception as exc:
            logger.error("%s detail error: %s", site["name"], exc)

        results.append({
            "source": site["name"],
            "emoji": site["emoji"],
            "title": title,
            "link": detail_link,
            "thumbnail": thumbnail,
            "download_links": download_links,
        })
    return results


def _search_custom_elaach(site: dict, query: str) -> List[Dict]:
    """Elaach uses a custom search URL and h3-based results."""
    encoded = urllib.parse.quote_plus(query)
    url = site["search_url"].format(query=encoded)
    headers = {"User-Agent": COMMON["user_agent"]}

    # Build alias search URLs
    alias_urls = _build_alias_urls(site, url, encoded)

    resp = _try_url_with_fallback(url, alias_urls, headers, timeout=COMMON["timeout"], verify=False)
    if not resp:
        logger.error("%s: all URLs failed", site["name"])
        return []

    # Determine working base
    working_base = site["base_url"]
    for alias in site.get("aliases", []):
        if alias in resp.url:
            working_base = alias
            break

    soup = BeautifulSoup(resp.text, "lxml")
    results = []
    seen = set()
    for h3 in soup.select("h3"):
        a = h3.select_one("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not title or not href or title in seen:
            continue
        if title.lower() in ("moviedetails", "filter movies", "filter tv series"):
            continue
        seen.add(title)

        if href.startswith("/"):
            href = working_base + href

        item_type = "Series" if "/tv-series" in href else "Movie"

        # Thumbnail from search page
        img = h3.select_one("img") or (h3.parent.select_one("img") if h3.parent else None)
        thumbnail = ""
        if img:
            thumbnail = img.get("src", "") or img.get("data-src", "") or img.get("data-lazy-src", "")
            if thumbnail and not thumbnail.startswith(("http://", "https://")):
                thumbnail = working_base + "/" + thumbnail.lstrip("/")

        # Scrape detail page
        download_links = []
        try:
            better_thumb = _get_thumbnail_from_page(href, headers, working_base, verify=False)
            if better_thumb:
                thumbnail = better_thumb
            download_links = _extract_download_links_from_page(
                href, headers, verify=False, skip_local_172=True
            )
        except Exception as exc:
            logger.error("%s detail error: %s", site["name"], exc)

        results.append({
            "source": site["name"],
            "emoji": site["emoji"],
            "title": f"{title} ({item_type})",
            "link": href,
            "thumbnail": thumbnail,
            "download_links": download_links,
        })
        if len(results) >= COMMON["max_results"]:
            break
    return results


# =========================
# Fuzzy Query Expansion — handles typos & transliteration variants
# =========================

# Common Bangla transliteration confusions
_PHONETIC_SWAPS = {
    "o": ["a", "u", "oa"],
    "a": ["o", "aa", "ah"],
    "e": ["i", "a"],
    "i": ["e", "y"],
    "u": ["o", "oo"],
    "s": ["sh", "z"],
    "sh": ["s", "zh"],
    "z": ["j", "s"],
    "j": ["z", "g"],
    "v": ["b", "w"],
    "w": ["v", "b"],
    "b": ["v", "w"],
    "c": ["k", "s"],
    "k": ["c", "q"],
    "g": ["j", "gh"],
    "t": ["th", "d"],
    "th": ["t", "d", "dh"],
    "d": ["dh", "t", "th"],
    "dh": ["d", "th"],
    "r": ["rh", "ri"],
    "n": ["nn", "m"],
    "m": ["n"],
    "y": ["i", "j"],
}

# Common whole-word replacements for Bangla movie terms
_WORD_ALIASES = {
    "nagar": ["nogor", "nagor", "nogar", "nagger"],
    "mohanagar": ["mahanagar", "mohanogor", "mahanogor", "mohonagar", "mohonogor"],
    "byomkesh": ["byomkesh", "bomkesh", "bymkesh", "byomkes", "bomkes"],
    "chorki": ["corki", "chorcki"],
    "hoichoi": ["hoichoi", "hichoi", "hoichuy"],
    "pushpa": ["puspa", "pushpa", "pooshpa"],
    "poramon": ["poramon", "paramon", "poraman", "paraman"],
    "monpura": ["manpura", "monpora", "manpora"],
    "hawa": ["hawa", "hawa", "haowa"],
    "priya": ["priya", "priyo", "prio"],
    "chandro": ["chondro", "chandor", "chondor"],
    "bondhu": ["bondhu", "bandhu", "bondho", "bandho"],
    "kotha": ["katha", "kotha", "kata"],
    "bhalo": ["bhalo", "valo", "bhalu"],
    "prem": ["prem", "prom"],
    "protibha": ["protibha", "pratibha", "protibha"],
    "shotti": ["sotti", "shotti", "sati", "shati"],
    "sotyi": ["sotti", "shotti", "sotyi"],
    "rong": ["rong", "rang", "rog"],
    "ghor": ["ghor", "ghar", "ghore"],
}


def _expand_query(query: str) -> List[str]:
    """Generate alternate spellings for a query to handle typos and transliteration variants."""
    variants = set()
    variants.add(query.lower().strip())

    # 1. Whole-word alias replacements
    words = query.lower().split()
    for i, word in enumerate(words):
        if word in _WORD_ALIASES:
            for alias in _WORD_ALIASES[word]:
                new_words = words[:i] + [alias] + words[i+1:]
                variants.add(" ".join(new_words))

    # 2. Phonetic swap variants (max 2 swaps to avoid explosion)
    q = query.lower().strip()
    single_swaps = set()
    for i, ch in enumerate(q):
        if ch in _PHONETIC_SWAPS and ch != " ":
            for replacement in _PHONETIC_SWAPS[ch]:
                variant = q[:i] + replacement + q[i+1:]
                single_swaps.add(variant)
    variants.update(single_swaps)

    # 3. Double swaps from single swaps (only for short queries)
    if len(q) <= 12:
        for s1 in list(single_swaps)[:5]:  # limit to avoid too many
            for i, ch in enumerate(s1):
                if ch in _PHONETIC_SWAPS and ch != " ":
                    for replacement in _PHONETIC_SWAPS[ch][:2]:  # limit replacements
                        variant = s1[:i] + replacement + s1[i+1:]
                        if variant != q:
                            variants.add(variant)

    # Remove original and return (limit total variants)
    variants.discard(q.lower().strip())
    return list(variants)[:8]  # max 8 alternate queries


def _title_similarity(title1: str, title2: str) -> float:
    """Simple similarity score between two titles (0.0 to 1.0)."""
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()
    if t1 == t2:
        return 1.0
    # Check if one contains the other
    if t1 in t2 or t2 in t1:
        return 0.8
    # Word overlap
    words1 = set(t1.split())
    words2 = set(t2.split())
    if not words1 or not words2:
        return 0.0
    overlap = len(words1 & words2)
    total = len(words1 | words2)
    return overlap / total if total > 0 else 0.0


# =========================
# Unified Search (parallel)
# =========================
def search_all_sites(query: str) -> List[Dict]:
    """Search all configured sites in parallel with fuzzy query expansion."""
    all_results = []
    seen_titles = {}  # title_lower -> result dict (dedup)

    # Build list of queries: original + fuzzy variants
    queries = [query]
    fuzzy_variants = _expand_query(query)
    if fuzzy_variants:
        logger.info("Fuzzy variants for '%s': %s", query, fuzzy_variants)
    queries.extend(fuzzy_variants)

    def _search_site(site, q):
        site_type = site.get("type", "wp")
        if site_type == "wp":
            return _search_wp(site, q)
        elif site_type == "api":
            return _search_api(site, q)
        elif site_type == "custom":
            return _search_custom_elaach(site, q)
        return []

    for q in queries:
        with ThreadPoolExecutor(max_workers=len(SITES)) as executor:
            futures = {executor.submit(_search_site, site, q): site["name"] for site in SITES}
            for future in futures:
                try:
                    results = future.result(timeout=COMMON["timeout"] + 5)
                    for r in results:
                        # Deduplicate by title similarity
                        title_key = r["title"].lower().strip()
                        # Check if we already have a very similar title
                        is_dup = False
                        for existing_key in list(seen_titles.keys()):
                            if _title_similarity(title_key, existing_key) >= 0.7:
                                is_dup = True
                                break
                        if not is_dup:
                            seen_titles[title_key] = r
                            all_results.append(r)
                except Exception as exc:
                    logger.error("Search error for %s: %s", futures[future], exc)

        # If we already have good results from original query, skip fuzzy variants
        if len(all_results) >= 3 and q == query:
            break

    return all_results


# =========================
# Force Subscribe Check
# =========================
async def is_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(
            chat_id=FORCE_SUB_CHANNEL,
            user_id=user_id,
        )
        return member.status in ("member", "administrator", "creator")
    except Exception as exc:
        logger.warning("Force-sub check failed for user %s: %s", user_id, exc)
        return True


# =========================
# Bot Handlers
# =========================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🎬 <b>Movie Search Bot</b>\n\n"
        "Search any movie or web series — just type the name!\n\n"
        "✅ Bangla, Hindi, South Indian, Hollywood\n"
        "✅ Hoichoi, Chorki, Bongo & more\n"
        "✅ Direct download links\n\n"
        "📌 <i>Join our channel to unlock access:</i>"
    )
    channel_link = f"https://t.me/{FORCE_SUB_CHANNEL.lstrip('@')}"
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔔 Join Channel", url=channel_link)]]
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    query = update.message.text.strip()

    if not await is_member(user_id, context):
        channel_link = f"https://t.me/{FORCE_SUB_CHANNEL.lstrip('@')}"
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔔 Join Channel to Unlock", url=channel_link)]]
        )
        await update.message.reply_text(
            "🚫 <b>Access Denied</b>\n\n"
            "Join our channel first to use this bot.",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return

    # Show typing indicator so user knows bot is working
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    search_msg = await update.message.reply_text(
        f"🔍 Searching for: <b>{html_escape(query)}</b>\n⏳ Please wait...",
        parse_mode="HTML",
    )

    loop = asyncio.get_event_loop()
    all_results = await loop.run_in_executor(None, search_all_sites, query)

    # Edit search message to show completion
    try:
        await search_msg.edit_text(
            f"🔍 Searching for: <b>{html_escape(query)}</b> ✅",
            parse_mode="HTML",
        )
    except Exception:
        pass

    if not all_results:
        await update.message.reply_text(
            "😕 No results found.\n"
            "Try a different name or check spelling.",
        )
        return

    for movie in all_results:
        title = movie["title"]
        link = movie["link"]
        thumbnail = movie["thumbnail"]
        dl_links = movie.get("download_links", [])

        caption = f"🎬 <b>{html_escape(title)}</b>"

        source_name = movie.get("source", "")
        if source_name:
            caption += f"\n📡 <i>{html_escape(source_name)}</i>"

        if dl_links:
            caption += "\n\n📥 <b>Download Links:</b>"
            for dl in dl_links[:8]:
                dl_text = dl["text"].replace("[", "(").replace("]", ")")
                if len(dl_text) > 50:
                    dl_text = dl_text[:47] + "..."
                url = dl["url"]
                if url.startswith(("http://", "https://")):
                    caption += f'\n• <a href="{url}">{html_escape(dl_text)}</a>'
                else:
                    caption += f"\n• {html_escape(dl_text)}"
                    caption += f"\n  <code>{html_escape(url)}</code>"
            if len(dl_links) > 8:
                caption += f'\n<i>...and {len(dl_links) - 8} more on the movie page</i>'

        # Build buttons
        buttons = []
        for dl in dl_links[:3]:
            url = dl["url"]
            if url.startswith(("http://", "https://")):
                dl_text = dl["text"].replace("[", "(").replace("]", ")")
                if len(dl_text) > 25:
                    dl_text = dl_text[:22] + "..."
                buttons.append([InlineKeyboardButton(f"📥 {dl_text}", url=url)])
        buttons.append([InlineKeyboardButton("🔗 Open Movie Page", url=link)])
        keyboard = InlineKeyboardMarkup(buttons)

        use_photo = thumbnail and len(caption) <= 1000
        if use_photo:
            try:
                await update.message.reply_photo(
                    photo=thumbnail, caption=caption,
                    parse_mode="HTML", reply_markup=keyboard,
                )
                continue
            except Exception:
                pass
        await update.message.reply_text(caption, parse_mode="HTML", reply_markup=keyboard)


# =========================
# Auto-Poster — posts new uploads to channel
# =========================
import json
import os
from datetime import datetime

_POSTED_FILE = os.path.join(os.path.dirname(__file__), AUTO_POSTER["posted_file"])


def _load_posted_urls() -> set:
    """Load already-posted URLs from file."""
    if not os.path.exists(_POSTED_FILE):
        return set()
    try:
        with open(_POSTED_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except Exception:
        return set()


def _save_posted_url(url: str) -> None:
    """Append a posted URL to the file."""
    try:
        with open(_POSTED_FILE, "a", encoding="utf-8") as f:
            f.write(url + "\n")
    except Exception as exc:
        logger.error("Failed to save posted URL: %s", exc)


def _fetch_latest_from_site(site: dict) -> List[Dict]:
    """Fetch latest posts from a site (first page, no search query)."""
    headers = {"User-Agent": COMMON["user_agent"]}
    verify = site.get("verify_ssl", True)
    whitelist = site.get("whitelist_domains", ())
    results = []

    if site["type"] == "api":
        try:
            resp = requests.get(
                site["api_url"],
                params={"per_page": 5, "orderby": "date", "order": "desc"},
                headers=headers, timeout=COMMON["timeout"], verify=False,
            )
            resp.raise_for_status()
            posts = resp.json()
            for post in posts[:5]:
                title_html = post.get("title", {}).get("rendered", "")
                title = BeautifulSoup(title_html, "lxml").get_text(strip=True)
                link = post.get("link", "")
                if not title or not link:
                    continue
                thumbnail = _get_thumbnail_from_page(link, headers, site["base_url"], verify=False)
                download_links = _extract_download_links_from_page(
                    link, headers, verify=False, whitelist_domains=whitelist
                )
                results.append({"title": title, "link": link, "thumbnail": thumbnail, "download_links": download_links})
        except Exception as exc:
            logger.error("AutoPost %s API error: %s", site["name"], exc)
        return results

    # For wp/custom: fetch homepage and get latest articles
    base_url = site.get("base_url", "")
    alias_urls = site.get("aliases", [])
    all_urls = [base_url] + alias_urls

    for url in all_urls:
        try:
            if site["type"] == "custom":
                # Elaach: use /movies page for latest
                resp = requests.get(url, headers=headers, timeout=COMMON["timeout"], verify=False)
            else:
                resp = requests.get(url, headers=headers, timeout=COMMON["timeout"], verify=verify)
            resp.raise_for_status()
            if len(resp.text) < 500:
                continue
            soup = BeautifulSoup(resp.text, "lxml")
            working_base = url

            if site["type"] == "custom":
                # Elaach: h3 links
                for h3 in soup.select("h3")[:5]:
                    a = h3.select_one("a")
                    if not a:
                        continue
                    title = a.get_text(strip=True)
                    href = a.get("href", "")
                    if not title or not href or title.lower() in ("moviedetails", "filter movies", "filter tv series"):
                        continue
                    if href.startswith("/"):
                        href = working_base + href
                    img = h3.select_one("img") or (h3.parent.select_one("img") if h3.parent else None)
                    thumbnail = ""
                    if img:
                        thumbnail = img.get("src", "") or img.get("data-src", "") or img.get("data-lazy-src", "")
                        if thumbnail and not thumbnail.startswith(("http://", "https://")):
                            thumbnail = working_base + "/" + thumbnail.lstrip("/")
                    download_links = _extract_download_links_from_page(
                        href, headers, verify=False, skip_local_172=True
                    )
                    results.append({"title": title, "link": href, "thumbnail": thumbnail, "download_links": download_links})
            else:
                # WordPress: articles
                articles = soup.select("article")[:5]
                for article in articles:
                    title_tag = (
                        article.select_one("h2.entry-title a") or article.select_one("h3.entry-title a")
                        or article.select_one("h2 a") or article.select_one("h3 a")
                        or article.select_one(".entry-title a")
                    )
                    if not title_tag:
                        continue
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get("href", "")
                    if not title or not link:
                        continue
                    img_tag = article.select_one("img")
                    thumbnail = ""
                    if img_tag:
                        thumbnail = img_tag.get("src", "") or img_tag.get("data-src", "") or img_tag.get("data-lazy-src", "")
                        if thumbnail and not thumbnail.startswith(("http://", "https://")):
                            thumbnail = working_base.rstrip("/") + "/" + thumbnail.lstrip("/")
                    # Scrape detail page
                    try:
                        better_thumb = _get_thumbnail_from_page(link, headers, working_base, verify)
                        if better_thumb:
                            thumbnail = better_thumb
                        download_links = _extract_download_links_from_page(
                            link, headers, verify=verify, whitelist_domains=whitelist
                        )
                    except Exception:
                        download_links = []
                    results.append({"title": title, "link": link, "thumbnail": thumbnail, "download_links": download_links})

            if results:
                break  # Found results from this URL, no need to try aliases
        except Exception:
            continue

    return results


async def _post_to_channel(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job callback: check for new uploads and post to channel."""
    if not AUTO_POSTER["enabled"]:
        return

    posted_urls = _load_posted_urls()
    new_posts = []

    logger.info("AutoPost: checking for new uploads...")

    for site in SITES:
        try:
            latest = _fetch_latest_from_site(site)
            for item in latest:
                link = item["link"]
                if link not in posted_urls:
                    new_posts.append(item)
                    posted_urls.add(link)
        except Exception as exc:
            logger.error("AutoPost %s error: %s", site["name"], exc)

    if not new_posts:
        logger.info("AutoPost: no new uploads found")
        return

    # Limit posts per check
    new_posts = new_posts[:AUTO_POSTER["max_posts_per_check"]]
    channel = AUTO_POSTER["channel"]

    for item in new_posts:
        title = item["title"]
        link = item["link"]
        thumbnail = item.get("thumbnail", "")
        dl_links = item.get("download_links", [])

        caption = f"🎬 <b>{html_escape(title)}</b>"

        if dl_links:
            caption += "\n\n📥 <b>Download Links:</b>"
            for dl in dl_links[:5]:
                dl_text = dl["text"].replace("[", "(").replace("]", ")")
                if len(dl_text) > 50:
                    dl_text = dl_text[:47] + "..."
                url = dl["url"]
                if url.startswith(("http://", "https://")):
                    caption += f'\n• <a href="{url}">{html_escape(dl_text)}</a>'
                else:
                    caption += f"\n• {html_escape(dl_text)}"
                    caption += f"\n  <code>{html_escape(url)}</code>"

        buttons = []
        for dl in dl_links[:2]:
            url = dl["url"]
            if url.startswith(("http://", "https://")):
                dl_text = dl["text"].replace("[", "(").replace("]", ")")
                if len(dl_text) > 25:
                    dl_text = dl_text[:22] + "..."
                buttons.append([InlineKeyboardButton(f"📥 {dl_text}", url=url)])
        buttons.append([InlineKeyboardButton("🔗 Movie Page", url=link)])
        keyboard = InlineKeyboardMarkup(buttons)

        try:
            use_photo = thumbnail and len(caption) <= 1000
            if use_photo:
                try:
                    await context.bot.send_photo(
                        chat_id=channel, photo=thumbnail,
                        caption=caption, parse_mode="HTML",
                        reply_markup=keyboard,
                    )
                except Exception:
                    await context.bot.send_message(
                        chat_id=channel, text=caption,
                        parse_mode="HTML", reply_markup=keyboard,
                    )
            else:
                await context.bot.send_message(
                    chat_id=channel, text=caption,
                    parse_mode="HTML", reply_markup=keyboard,
                )
            _save_posted_url(link)
            logger.info("AutoPost: posted '%s'", title[:40])
        except Exception as exc:
            logger.error("AutoPost: failed to post '%s': %s", title[:30], exc)

    logger.info("AutoPost: posted %d new items", len(new_posts))


# =========================
# Release Tracker — upcoming movies + auto-search after release
# =========================
from datetime import datetime, timedelta

_TRACKED_FILE = os.path.join(os.path.dirname(__file__), RELEASE_TRACKER["tracked_file"])


def _load_tracked_releases() -> List[Dict]:
    """Load tracked releases from JSON file."""
    if not os.path.exists(_TRACKED_FILE):
        return []
    try:
        with open(_TRACKED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_tracked_releases(releases: List[Dict]) -> None:
    """Save tracked releases to JSON file."""
    try:
        with open(_TRACKED_FILE, "w", encoding="utf-8") as f:
            json.dump(releases, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.error("Failed to save tracked releases: %s", exc)


def _fetch_upcoming_releases() -> List[Dict]:
    """Scrape Wikipedia film lists for upcoming releases with dates."""
    headers = {"User-Agent": COMMON["user_agent"]}
    year = datetime.now().year
    releases = []
    seen_titles = set()

    # Quarter-to-months mapping for Wikipedia section headings
    _QUARTER_MONTHS = {
        "january": 1, "february": 2, "march": 3,
        "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9,
        "october": 10, "november": 11, "december": 12,
    }

    wiki_urls = [
        f"https://en.wikipedia.org/wiki/List_of_American_films_of_{year}",
        f"https://en.wikipedia.org/wiki/List_of_Indian_films_of_{year}",
    ]

    for url in wiki_urls:
        try:
            resp = requests.get(url, headers=headers, timeout=COMMON["timeout"], verify=False)
            resp.raise_for_status()
        except Exception as exc:
            logger.error("Wikipedia fetch error for %s: %s", url, exc)
            continue

        soup = BeautifulSoup(resp.text, "lxml")

        # Walk through all elements in order to track which section we're in
        current_quarter_months = []  # e.g. [4, 5, 6] for "April–June"

        for element in soup.select("h2, h3, table.wikitable"):
            # Update current quarter from headings
            if element.name in ("h2", "h3"):
                heading_text = element.get_text(strip=True).lower()
                # Parse quarter headings like "April–June" or "January-March"
                months_in_heading = []
                for month_name, month_num in _QUARTER_MONTHS.items():
                    if month_name in heading_text:
                        months_in_heading.append(month_num)
                if months_in_heading:
                    current_quarter_months = sorted(months_in_heading)
                continue

            # Parse table rows
            if element.name == "table":
                # Get header to find "Opening" and "Title" columns
                header_row = element.select_one("tr")
                if not header_row:
                    continue
                header_cells = header_row.select("th")
                col_names = [th.get_text(strip=True).lower() for th in header_cells]

                opening_col = -1
                title_col = -1
                for idx, name in enumerate(col_names):
                    if "opening" in name:
                        opening_col = idx
                    if "title" in name:
                        title_col = idx

                # If no title column found, default to 0 or 1
                if title_col == -1:
                    # Skip box office tables (Rank, Title, Distributor, Gross)
                    if col_names and "rank" in col_names[0]:
                        continue
                    title_col = 1 if len(col_names) > 1 and "opening" in col_names[0] else 0

                for row in element.select("tr")[1:]:  # skip header
                    cells = row.select("td")
                    if len(cells) <= max(opening_col, title_col):
                        continue

                    # Get title
                    title_cell = cells[title_col] if title_col < len(cells) else cells[0]
                    title = title_cell.get_text(strip=True)
                    # Clean up Wikipedia artifacts
                    title = re.sub(r"[†‡]", "", title).strip()
                    # Filter out garbage entries (production companies, languages, etc.)
                    _SKIP_WORDS = {"hindi", "telugu", "malayalam", "tamil", "kannada", "bengali",
                                   "marathi", "gujarati", "punjabi", "odia", "assamese", "urdu"}
                    _SKIP_PATTERNS = ["pictures", "studios", "entertainment", "productions",
                                      "features", "animation", "universal", "paramount",
                                      "warner", "disney", "amazon", "netflix", "hulu",
                                      "lionsgate", "sony", "fox", "vertical", "neon",
                                      "bleecker", "roadside", "iconic", "mrc", "anonymous",
                                      "independent film", "apple tv", "skydance",
                                      "working title", "escape art", "saban"]
                    if (not title or title in seen_titles or len(title) < 5
                            or title.lower() in _SKIP_WORDS
                            or "/" in title  # production company paths like "Universal/Legendary"
                            or any(kw in title.lower() for kw in _SKIP_PATTERNS)):
                        continue

                    # Get opening day
                    release_date = ""
                    if opening_col >= 0 and opening_col < len(cells):
                        opening_text = cells[opening_col].get_text(strip=True)
                        # Opening column has day number like "2", "1", "3"
                        day_match = re.match(r"(\d{1,2})", opening_text)
                        if day_match and current_quarter_months:
                            day = int(day_match.group(1))
                            # Use the first month of the quarter as estimate
                            month = current_quarter_months[0]
                            try:
                                dt = datetime(year, month, day)
                                release_date = dt.strftime("%Y-%m-%d")
                            except ValueError:
                                pass

                    # Get thumbnail
                    thumbnail = ""
                    img = title_cell.select_one("img")
                    if img:
                        src = img.get("src", "")
                        if src:
                            if src.startswith("//"):
                                thumbnail = "https:" + src
                            elif not src.startswith(("http://", "https://")):
                                thumbnail = "https:" + src
                            else:
                                thumbnail = src

                    seen_titles.add(title)
                    releases.append({
                        "title": title,
                        "release_date": release_date,
                        "thumbnail": thumbnail,
                        "searched": False,
                        "posted": False,
                    })

    return releases


async def _check_releases_and_post(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job callback: post teaser on release day, then search+post download links after 6h."""
    if not RELEASE_TRACKER["enabled"]:
        return

    now = datetime.now()
    delay_hours = RELEASE_TRACKER["delay_hours_after_release"]
    channel = RELEASE_TRACKER["channel"]
    bot_username = TELEGRAM_BOT.get("bot_username", "").lstrip("@")

    logger.info("ReleaseTracker: checking upcoming releases...")

    # 1. Fetch upcoming releases from Wikipedia
    upcoming = _fetch_upcoming_releases()

    # 2. Load existing tracked releases
    tracked = _load_tracked_releases()
    tracked_titles = {r["title"] for r in tracked}

    # 3. Add new upcoming releases
    for release in upcoming:
        if release["title"] not in tracked_titles:
            tracked.append(release)
            tracked_titles.add(release["title"])
            logger.info("ReleaseTracker: tracking '%s' (release: %s)", release["title"][:30], release["release_date"])

    teasers_posted = 0
    downloads_posted = 0

    for release in tracked:
        if not release.get("release_date"):
            continue

        try:
            release_dt = datetime.strptime(release["release_date"], "%Y-%m-%d")
            hours_since_release = (now - release_dt).total_seconds() / 3600
        except ValueError:
            continue

        # --- PHASE 1: Post teaser on release day (only for releases within 7 days) ---
        if 0 <= hours_since_release <= 168 and not release.get("teaser_posted"):
            title = release["title"]
            thumbnail = release.get("thumbnail", "")

            caption = (
                f"🆕 <b>JUST RELEASED!</b>\n"
                f"🎬 <b>{html_escape(title)}</b>\n\n"
                f"📥 Download links coming soon!\n"
                f"🔍 Search <b>{html_escape(title)}</b> on our bot to get it first!"
            )

            bot_search_url = f"https://t.me/{bot_username}" if bot_username else ""
            buttons = []
            if bot_search_url:
                buttons.append([InlineKeyboardButton("🤖 Open Bot", url=bot_search_url)])
            keyboard = InlineKeyboardMarkup(buttons)

            try:
                if thumbnail:
                    try:
                        await context.bot.send_photo(
                            chat_id=channel, photo=thumbnail,
                            caption=caption, parse_mode="HTML",
                            reply_markup=keyboard,
                        )
                    except Exception:
                        await context.bot.send_message(
                            chat_id=channel, text=caption,
                            parse_mode="HTML", reply_markup=keyboard,
                        )
                else:
                    await context.bot.send_message(
                        chat_id=channel, text=caption,
                        parse_mode="HTML", reply_markup=keyboard,
                    )
                release["teaser_posted"] = True
                teasers_posted += 1
                logger.info("ReleaseTracker: TEASER posted '%s'", title[:30])
            except Exception as exc:
                logger.error("ReleaseTracker: teaser failed for '%s': %s", title[:30], exc)

        # --- PHASE 2: Post download links after delay (only releases within 7 days)
        if delay_hours <= hours_since_release <= 168 and not release.get("searched"):
            logger.info("ReleaseTracker: searching for '%s' (%.1f hours after release)",
                       release["title"][:30], hours_since_release)
            release["searched"] = True

            # Use direct search (no fuzzy) for speed in release tracker
            results = []
            for site in SITES:
                site_type = site.get("type", "wp")
                try:
                    if site_type == "wp":
                        results.extend(_search_wp(site, release["title"]))
                    elif site_type == "api":
                        results.extend(_search_api(site, release["title"]))
                    elif site_type == "custom":
                        results.extend(_search_custom_elaach(site, release["title"]))
                except Exception:
                    continue
                if results:
                    break  # Found results, no need to search more sites

            if results:
                best = results[0]
                title = best["title"]
                link = best["link"]
                thumbnail = best.get("thumbnail", "") or release.get("thumbnail", "")
                dl_links = best.get("download_links", [])

                caption = f"🆕 <b>DOWNLOAD AVAILABLE!</b>\n🎬 <b>{html_escape(title)}</b>\n📡 <i>Release</i>"

                if dl_links:
                    caption += "\n\n📥 <b>Download Links:</b>"
                    for dl in dl_links[:5]:
                        dl_text = dl["text"].replace("[", "(").replace("]", ")")
                        if len(dl_text) > 50:
                            dl_text = dl_text[:47] + "..."
                        url = dl["url"]
                        if url.startswith(("http://", "https://")):
                            caption += f'\n• <a href="{url}">{html_escape(dl_text)}</a>'
                        else:
                            caption += f"\n• {html_escape(dl_text)}"
                            caption += f"\n  <code>{html_escape(url)}</code>"

                buttons = []
                for dl in dl_links[:2]:
                    url = dl["url"]
                    if url.startswith(("http://", "https://")):
                        dl_text = dl["text"].replace("[", "(").replace("]", ")")
                        if len(dl_text) > 25:
                            dl_text = dl_text[:22] + "..."
                        buttons.append([InlineKeyboardButton(f"📥 {dl_text}", url=url)])
                buttons.append([InlineKeyboardButton("🔗 Movie Page", url=link)])
                keyboard = InlineKeyboardMarkup(buttons)

                try:
                    if thumbnail and len(caption) <= 1000:
                        try:
                            await context.bot.send_photo(
                                chat_id=channel, photo=thumbnail,
                                caption=caption, parse_mode="HTML",
                                reply_markup=keyboard,
                            )
                        except Exception:
                            await context.bot.send_message(
                                chat_id=channel, text=caption,
                                parse_mode="HTML", reply_markup=keyboard,
                            )
                    else:
                        await context.bot.send_message(
                            chat_id=channel, text=caption,
                            parse_mode="HTML", reply_markup=keyboard,
                        )
                    release["posted"] = True
                    _save_posted_url(link)
                    downloads_posted += 1
                    logger.info("ReleaseTracker: DOWNLOADS posted '%s'", title[:30])
                except Exception as exc:
                    logger.error("ReleaseTracker: download post failed '%s': %s", title[:30], exc)
            else:
                logger.info("ReleaseTracker: no download links yet for '%s'", release["title"][:30])
                release["searched"] = False  # retry next cycle

    # Save and clean up
    _save_tracked_releases(tracked)

    cutoff = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    tracked = [r for r in tracked if r.get("release_date", "") >= cutoff]
    _save_tracked_releases(tracked)

    logger.info("ReleaseTracker: done - %d teasers, %d download posts", teasers_posted, downloads_posted)


# =========================
# Main
# =========================
def main() -> None:
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT["bot_token"])
        .build()
    )
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Auto-poster scheduler
    if AUTO_POSTER["enabled"]:
        interval = AUTO_POSTER["check_interval_minutes"] * 60
        job_queue = application.job_queue
        job_queue.run_repeating(
            _post_to_channel,
            interval=interval,
            first=10,  # Start checking 10 seconds after bot starts
        )
        logger.info("AutoPost: enabled, checking every %d min", AUTO_POSTER["check_interval_minutes"])

    # Release tracker scheduler
    if RELEASE_TRACKER["enabled"]:
        rt_interval = RELEASE_TRACKER["check_interval_minutes"] * 60
        job_queue = application.job_queue
        job_queue.run_repeating(
            _check_releases_and_post,
            interval=rt_interval,
            first=300,  # Start 5 min after bot starts (after auto-poster finishes)
        )
        logger.info("ReleaseTracker: enabled, checking every %d min", RELEASE_TRACKER["check_interval_minutes"])

    logger.info("Bot starting with %d sources...", len(SITES))
    application.run_polling()


if __name__ == "__main__":
    main()
