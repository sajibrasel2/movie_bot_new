import argparse
import asyncio
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import mysql.connector
from mysql.connector import Error as MySQLError
from telethon import TelegramClient, functions
from telethon.errors import (
    ChatAdminRequiredError,
    ChannelPrivateError,
    FloodWaitError,
    RPCError,
    UserAlreadyParticipantError,
)
from telethon.sessions import StringSession
from telethon.tl.patched import Message

from config import COLLECT_SETTINGS, MYSQL_CONFIG, SOURCE_CHANNELS, TELEGRAM_API

# ======================
# Config / Constants
# ======================
BASE_DIR = Path(__file__).resolve().parent
LOCK_PATH = BASE_DIR / COLLECT_SETTINGS["lock_path"]
LOG_FILE = BASE_DIR / COLLECT_SETTINGS["log_file"]
MEDIA_DIR = BASE_DIR / COLLECT_SETTINGS["media_dir"]

MAX_PER_CHANNEL = int(COLLECT_SETTINGS.get("max_messages_per_channel", 40))
DEFAULT_FRESH_WINDOW_MINUTES = int(COLLECT_SETTINGS.get("fresh_window_minutes", 10))
MAX_SCAN_PER_CHANNEL = int(COLLECT_SETTINGS.get("max_scan_messages_per_channel", 2000))

MAX_DOWNLOAD_MB = int(COLLECT_SETTINGS.get("max_download_mb", 50))
MAX_DOWNLOAD_BYTES = MAX_DOWNLOAD_MB * 1024 * 1024

ALLOWED_DOCUMENT_EXTENSIONS = {
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".iso",
    ".apk",
    ".exe",
    ".msi",
    ".dmg",
    ".pkg",
    ".deb",
    ".rpm",
    ".jar",
    ".ipa",
    ".torrent",
    ".pdf",
}

# ======================
# MEDIA-ONLY SOURCES
# ======================
MEDIA_ONLY_CHANNELS = {
    "modxpremiumchat",  # chat group → only media
}

# ======================
# BETTING / GAMBLING FILTER (COMPREHENSIVE)
# ======================
BETTING_KEYWORDS = [
    # Betting platforms (English & romanized)
    "1win", "1xbet", "99xo", "mostbet", "parimatch", "bet365", 
    "tashanwin", "tashanok", "ts777", "yaarwin", "jaiclub",
    "urs account", "betting panel", "game panel", "number panel",
    "tashanai_prompts", "ai panel", "prediction apk", "tashanai",
    "tashan", "aviatormods", "tashanwin game", "tashanai panel",
    "tashangame", "aviator", "jili", "teen patti", "color trading",
    "91club", "daman", "lottery", "rummy", "color prediction",
    "xeonpals", "shopify sales", "paypal money",
    
    # Betting/gambling terms (English)
    "betting", "casino", "deposit", "withdraw", "bonus", "freebet",
    "daily profit", "profit limit", "number hack", "premium hack",
    "gift codes", "register and get", "sign-up bonus", "free bonus",
    "claim bonus", "instant claim", "prediction", "worldcup prediction",
    "100% prediction", "minimum deposit", "daily profit limit upto",
    "invitationcode", "invitation code", "referral code", "promo code",
    "unlock premium hack", "unlock this premium hack", "activated game", "game number",
    "paisa kamavo", "paise jeeto", "win money", "earn daily",
    "upto 50000", "upto 30000", "upto 20000", "profit upto",
    "daily earning", "work from home income", "facebook ad dekhenge",
    "receive paypal money", "send money to your paypal",
    
    # Betting/gambling terms (Bengali/Hindi)
    "গেমিং প্ল্যাটফর্ম", "বোনাস", "ডিপোজিট", "রেজিস্টার করুন",
    "ফ্রিবেট", "বেটিং", "জিতে নিন", "পুরস্কার", "রেফার",
    "গ্র্যান্ড প্রাইজ", "রেড এনভেলপ", "vip এক্সক্লুসিভ",
    "ইনকাম করতে পারবেন", "বিকাশ নগদ", "উইথড্র",
    "ফেসবুক অ্যাড দেখবেন", "tiktok অ্যাড দেখবেন",
    "ফেজ ফলো করবেন", "টিক টক ফলো করবেন",
    "আয় করুন", "টাকা জিতুন", "দৈনিক আয়", "প্রতিদিন আয়",
    "দৈনিক ইনকাম", "থেকে", "ইনকাম করে",
    
    # Registration/deposit phrases
    "deposit to unlock", "deposit to claim", "minimum deposit",
    "create a new account", "register?invitation", "register and get",
    "only deposit", "just deposit", "₹100 deposit", "₹200 deposit",
    
    # URLs - betting domains
    ".live/#/register", "tashanok.live", "ts777.live", "yaarwin.",
    "jaiclub.", "91club.", "daman.", "mostbet.", "1xbet.",
    "discord.gg/xeonpals",
    
    # Spam phrases (high confidence)
    "delete in a few minutes", "delete in in a few minutes",
    "due to copyright", "shifting to our main channel",
    "telegram is closing", "new channel available",
    "we just won worldcup", "copyright issues we are shifting",
    "posting mod links to a new channel", "telegram is çløsiñg",
    "only uk , spain , italy", "only 5000 entry free",
]

# Spam phrases that need additional betting context (lower confidence)
SPAM_PHRASES_NEED_CONTEXT = [
    "only 5000 entry", "only 3000 entry", "only 2000 entry",
    "only 1000 entry", "only free", "entry free",
]

# Whitelist: Legitimate mod app keywords that should ALWAYS pass
LEGITIMATE_MOD_APPS = [
    "capcut", "prequel", "vn editor", "vn video editor",
    "spotify", "netflix", "youtube premium", "photoroom",
    "adobe", "lightroom", "photoshop", "canva",
    "microsoft copilot", "mx player", "sonyliv", "moviebox",
    "metrolist", "cineplus", "true edge", "ampereflow",
    "backdropps", "socks5", "umagic", "mod apk",
    # Add more legitimate app names as needed
]

# URL / LINK PATTERNS
URL_REGEX = re.compile(
    r"(?:https?://|www\.)\S+|(?:t\.me|telegram\.me|telegram\.dog)/\S+",
    re.IGNORECASE
)


def is_betting_content(message: Message) -> bool:
    """
    Check if message contains betting/gambling content.
    Returns True if it should be blocked.
    Uses smart multi-indicator detection to catch sophisticated betting spam.
    """
    text = (message.message or "").lower()
    
    # Check filename
    filename = ""
    try:
        filename = getattr(getattr(message, "file", None), "name", "") or ""
        filename = str(filename).lower()
    except Exception:
        pass
    
    combined = f"{text} {filename}"
    
    # ✅ WHITELIST CHECK: Always allow legitimate mod apps
    for legit_keyword in LEGITIMATE_MOD_APPS:
        if legit_keyword in combined:
            return False
    
    # 🚫 STEP 1: Direct keyword match (high confidence keywords only)
    # Exclude spam phrases that need context
    high_confidence_keywords = [kw for kw in BETTING_KEYWORDS if kw not in SPAM_PHRASES_NEED_CONTEXT]
    for keyword in high_confidence_keywords:
        if keyword.lower() in combined:
            return True
    
    # 🚫 STEP 2: Check spam phrases that need betting context
    # These phrases alone don't mean betting, but with betting indicators they do
    has_spam_phrase = any(phrase in combined for phrase in SPAM_PHRASES_NEED_CONTEXT)
    
    if has_spam_phrase:
        # Check if there are betting indicators
        betting_context = ["deposit", "profit", "₹", "bonus", "register", "win", "earn"]
        has_betting_context = any(word in combined for word in betting_context)
        
        if has_betting_context:
            return True
    
    # 🚫 STEP 3: Smart multi-indicator detection
    # These indicators alone don't mean betting, but combinations do
    betting_indicators = {
        "money_symbols": ["₹", "$", "€", "£"],
        "deposit_terms": ["deposit", "ডিপোজিট", "জমা করুন"],
        "profit_terms": ["profit", "earn", "income", "আয়", "লাভ", "ইনকাম"],
        "bonus_terms": ["bonus", "gift", "বোনাস"],
        "registration": ["register", "রেজিস্টার", "sign up", "সাইন আপ"],
        "win_terms": ["win", "জিতুন", "winning"],
        "amount_patterns": ["upto", "থেকে", "daily limit", "per day"],
        "invitation": ["invitation", "referral", "promo code"],
    }
    
    # Count how many indicator categories are present
    category_matches = 0
    for category_keywords in betting_indicators.values():
        if any(kw in combined for kw in category_keywords):
            category_matches += 1
    
    # If 3+ betting indicator categories present, it's betting content
    if category_matches >= 3:
        return True
    
    # 🚫 STEP 4: Check for betting app file patterns
    # File must have BOTH a betting keyword AND a money/game term
    betting_file_keywords = ["tashan", "aviator", "jili", "panel", "hack", "ai pannel"]
    money_game_keywords = ["game", "win", "earn", "money", "profit", "apk"]
    
    has_betting_keyword = any(kw in filename for kw in betting_file_keywords)
    has_money_keyword = any(kw in filename for kw in money_game_keywords)
    
    if has_betting_keyword and has_money_keyword:
        return True
    
    # 🚫 STEP 5: Specific file pattern checks (known betting APKs)
    # getmodpcs files with betting context
    if "getmodpcs" in filename and any(word in text for word in ["deposit", "profit", "₹", "bonus", "register"]):
        return True
    
    # Generic pattern: any APK with betting indicators in text
    if ".apk" in filename and any(word in text for word in ["deposit", "₹100", "₹200", "daily profit", "upto"]):
        return True
    
    # 🚫 STEP 6: URL pattern check (betting registration URLs)
    betting_url_patterns = [
        r"\.live/#/register",
        r"invitationcode=\d+",
        r"referral.*code",
        r"discord\.gg/xeonpals",
    ]
    for pattern in betting_url_patterns:
        if re.search(pattern, combined, re.IGNORECASE):
            return True
    
    return False


# ======================
# File Lock
# ======================
class SimpleFileLock:
    def __init__(self, path: Path):
        self.path = path
        self.fd: Optional[int] = None

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except FileExistsError:
            raise RuntimeError(f"Lock already acquired: {self.path}")

    def release(self):
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None
        try:
            if self.path.exists():
                self.path.unlink()
        except OSError:
            pass


# ======================
# Setup / DB
# ======================
def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def get_db_connection():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    conn.autocommit = True
    return conn


# ======================
# Text helpers
# ======================
def normalize_channel_handle(handle: str) -> str:
    value = (handle or "").strip()
    if not value:
        return value

    web_match = re.search(r"web\.telegram\.org/k/#(?P<id>-?\d+)", value)
    if web_match:
        return web_match.group("id")

    if value.startswith("https://t.me/"):
        value = value[len("https://t.me/") :]
    if value.startswith("t.me/"):
        value = value[len("t.me/") :]

    if re.fullmatch(r"-?\d+", value):
        return value

    if "/" in value:
        value = value.split("/", 1)[0]

    if not value.startswith("@"):
        value = f"@{value}"
    return value


def canonical_channel_key(handle: str) -> str:
    normalized = normalize_channel_handle(handle)
    if re.fullmatch(r"-?\d+", normalized or ""):
        return normalized
    return normalized.lstrip("@").lower()


def strip_text_keep_links(text: str) -> str:
    """
    Remove all external URLs and source channel links from text.
    This prevents source channel promotion in forwarded messages.
    Preserves live stream links.
    """
    if not text:
        return ""
    
    # Check if this is a live stream post
    is_live_stream = contains_live_link(text)
    
    # Remove ALL Telegram channel/user mentions (@username)
    text = re.sub(r"@\w+", "", text)
    
    # Remove t.me links (all Telegram links)
    text = re.sub(r"(?:https?://)?(?:t\.me|telegram\.me|telegram\.dog)/[^\s]+", "", text, flags=re.IGNORECASE)
    
    # Remove web.telegram.org links
    text = re.sub(r"(?:https?://)?web\.telegram\.org/[^\s]+", "", text, flags=re.IGNORECASE)
    
    # If NOT a live stream, remove ALL HTTP/HTTPS URLs
    if not is_live_stream:
        text = re.sub(r"https?://[^\s]+", "", text, flags=re.IGNORECASE)
        text = re.sub(r"www\.[^\s]+", "", text, flags=re.IGNORECASE)
    
    # Remove phrases that promote source channels
    spam_phrases = [
        r"join\s+(?:our|my)?\s*(?:channel|group)",
        r"(?:আমাদের|আমার)?\s*চ্যানেলে\s*যোগ",
        r"follow\s+(?:us|me)",
        r"ফলো\s+করুন",
        r"due\s+to\s+copyright",
        r"shifting\s+to.*channel",
        r"new\s+channel\s+available",
        r"telegram\s+(?:is\s+)?closing",
    ]
    for phrase in spam_phrases:
        text = re.sub(phrase, "", text, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    text = re.sub(r"[ \t]+", " ", text)  # Multiple spaces/tabs to single space
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # Max 2 consecutive newlines
    text = re.sub(r"^\s+|\s+$", "", text, flags=re.MULTILINE)  # Trim lines
    
    return text.strip()


def contains_live_link(text: str) -> bool:
    if not text:
        return False

    patterns = [
        r"facebook\.com/.*/live",
        r"fb\.watch",
        r"youtube\.com/live",
        r"youtu\.be/",
        r"t\.me/.*/live",
        r"telegram\.me/.*/live",
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def ensure_media_dir(channel_key: str) -> Path:
    target = MEDIA_DIR / channel_key
    target.mkdir(parents=True, exist_ok=True)
    return target


# ======================
# MEDIA-ONLY HELPER
# ======================
def is_media_only_source(channel_key: str) -> bool:
    return channel_key in MEDIA_ONLY_CHANNELS


def is_allowed_document_message(message: Message) -> bool:
    doc = getattr(message, "document", None)
    if not doc:
        return False

    name = None
    try:
        name = getattr(getattr(message, "file", None), "name", None)
    except Exception:
        name = None

    if name:
        _, ext = os.path.splitext(str(name).lower())
        if ext in ALLOWED_DOCUMENT_EXTENSIONS:
            return True

    mime = getattr(doc, "mime_type", None)
    if mime:
        mime = str(mime).lower()
        if mime.startswith("application/"):
            return True
        if mime in {"binary/octet-stream", "application/octet-stream"}:
            return True

    return False


def contains_blocked_link(text: str) -> bool:
    """
    Check if text contains promotional/spam links.
    We want to block posts that are primarily link spam.
    """
    if not text:
        return False
    
    # Count URLs in the message
    urls = URL_REGEX.findall(text)
    
    # If message is very short but has multiple links, it's spam
    if len(urls) >= 2 and len(text.strip()) < 200:
        return True
    
    return False


def is_spam_post(text: str) -> bool:
    """
    Additional spam check for text content.
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Direct keyword check
    for keyword in BETTING_KEYWORDS:
        if keyword.lower() in text_lower:
            return True
    
    return False


# ======================
# Media handling
# ======================
async def download_media(message: Message, channel_key: str) -> Optional[dict]:
    if not message.media:
        return None

    try:
        size = None
        if getattr(message, "document", None) and getattr(message.document, "size", None):
            size = int(message.document.size)
        elif getattr(message, "video", None) and getattr(message.video, "size", None):
            size = int(message.video.size)

        if size and size > MAX_DOWNLOAD_BYTES:
            return {"path": None, "type": "too_large"}
    except Exception:
        pass

    directory = ensure_media_dir(channel_key)
    filename = f"{channel_key}_{message.id}_{int(message.date.timestamp())}"
    target_path = directory / filename

    download_path = await message.download_media(file=str(target_path))
    if not download_path:
        return None

    rel_path = os.path.relpath(download_path, BASE_DIR).replace("\\", "/")

    media_type = "document"
    if message.photo:
        media_type = "photo"
    elif message.video:
        media_type = "video"
    elif message.audio:
        media_type = "audio"
    elif message.voice:
        media_type = "voice"
    elif message.gif or getattr(message, "sticker", None):
        media_type = "animation"

    return {"path": rel_path, "type": media_type}


# ======================
# DB helpers
# ======================
def fetch_last_message_id(cursor, channel: str) -> Optional[int]:
    cursor.execute(
        "SELECT last_message_id FROM telegram_channel_state WHERE source_channel=%s",
        (channel,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def update_last_message_id(cursor, channel: str, message_id: int):
    cursor.execute(
        """
        INSERT INTO telegram_channel_state (source_channel, last_message_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE last_message_id=VALUES(last_message_id), updated_at=NOW()
        """,
        (channel, message_id),
    )


# ======================
# Collect logic
# ======================
async def ensure_channel_access(client: TelegramClient, channel: str):
    resolved = channel
    if isinstance(channel, str) and re.fullmatch(r"-?\d+", channel.strip()):
        resolved = int(channel.strip())

    entity = await client.get_entity(resolved)
    try:
        await client(functions.channels.JoinChannelRequest(entity))
    except UserAlreadyParticipantError:
        pass
    except (ChannelPrivateError, ChatAdminRequiredError):
        pass
    return entity


async def collect_from_channel(client: TelegramClient, db_conn, source: str, window_minutes: int):
    channel_handle = normalize_channel_handle(source)
    channel_key = canonical_channel_key(channel_handle)
    cursor = db_conn.cursor()

    last_id = fetch_last_message_id(cursor, channel_key) or 0
    max_seen_id = last_id

    try:
        entity = await ensure_channel_access(client, channel_handle)
    except RPCError:
        logging.error("Skipping %s – cannot access", channel_handle)
        return

    source_title = getattr(entity, "title", channel_handle)
    now = datetime.now(timezone.utc)

    fetched = []
    scanned = 0

    async for message in client.iter_messages(entity, min_id=last_id):
        if scanned >= MAX_SCAN_PER_CHANNEL:
            break
        scanned += 1
        if not message or not isinstance(message, Message):
            continue
        if not message.date:
            continue

        msg_time = message.date.replace(tzinfo=timezone.utc)
        if now - msg_time > timedelta(minutes=window_minutes):
            break

        max_seen_id = max(max_seen_id, message.id)
        fetched.append(message)

    for message in reversed(fetched[:MAX_PER_CHANNEL]):
        if message.action:
            continue

        # 🚫 Skip voice messages
        if getattr(message, "voice", None):
            logging.info("🚫 Skipping voice message %s from %s", message.id, channel_handle)
            continue

        raw_text = message.message or ""

        # 🚫 PRIMARY FILTER: Block all betting/gambling content
        if is_betting_content(message):
            logging.info("🚫 Skipping betting/gambling content %s from %s", message.id, channel_handle)
            continue

        # � Block spam posts (secondary check)
        if is_spam_post(raw_text):
            logging.info("🚫 Skipping spam post %s from %s", message.id, channel_handle)
            continue

        # 🚫 Block link spam (multiple links in short text)
        if contains_blocked_link(raw_text):
            logging.info("🚫 Skipping link spam %s from %s", message.id, channel_handle)
            continue

        # 🔒 MEDIA-ONLY FILTER (for specific channels)
        if is_media_only_source(channel_key):
            if not is_allowed_document_message(message):
                logging.info("🔒 Skipping non-document message %s from media-only source %s", message.id, channel_handle)
                continue

        # ✅ Clean text - remove all source channel links and mentions
        text = strip_text_keep_links(raw_text)

        # Add live stream indicator if applicable
        if contains_live_link(raw_text):
            text = "📡 LIVE স্ট্রিম লিংক:\n" + text

        media_payload = await download_media(message, channel_key)

        media_path = None
        media_type = None

        if media_payload:
            if media_payload["type"] == "too_large":
                text = (text + "\n\n⚠️ মিডিয়া ফাইলটি অনেক বড়").strip()
            else:
                media_path = media_payload["path"]
                media_type = media_payload["type"]

        # Skip if no content after filtering
        if not text and not media_path:
            logging.info("⏭️ Skipping empty post %s from %s after filtering", message.id, channel_handle)
            continue

        try:
            cursor.execute(
                """
                INSERT INTO telegram_collected_posts
                    (source_channel, source_message_id, source_title, text, media_path, media_type)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    channel_key,
                    message.id,
                    source_title,
                    text or None,
                    media_path,
                    media_type,
                ),
            )
            logging.info("✅ Queued %s from %s", message.id, channel_handle)
        except MySQLError as exc:
            if exc.errno != 1062:
                logging.error("❌ DB error %s: %s", message.id, exc)

    if max_seen_id > last_id:
        update_last_message_id(cursor, channel_key, max_seen_id)


# ======================
# Main
# ======================
async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--window-minutes", type=int, default=DEFAULT_FRESH_WINDOW_MINUTES)
    parser.add_argument(
        "--channels",
        type=str,
        default="",
        help="Comma-separated list of source channels to collect",
    )
    args = parser.parse_args()

    setup_logging()
    lock = SimpleFileLock(LOCK_PATH)

    try:
        lock.acquire()
    except RuntimeError as err:
        logging.warning(err)
        return

    db_conn = None
    client = None

    try:
        db_conn = get_db_connection()
        client = TelegramClient(
            StringSession(TELEGRAM_API["session_string"]),
            TELEGRAM_API["api_id"],
            TELEGRAM_API["api_hash"],
        )
        await client.connect()

        if not await client.is_user_authorized():
            raise RuntimeError("Telethon session not authorized")

        selected_channels = [c.strip() for c in (args.channels or "").split(",") if c.strip()]
        channels = selected_channels or SOURCE_CHANNELS

        for channel in channels:
            try:
                await collect_from_channel(client, db_conn, channel, args.window_minutes)
            except FloodWaitError as exc:
                logging.warning("Flood wait %s sec", exc.seconds)
                await asyncio.sleep(exc.seconds + 1)
            except Exception as exc:
                logging.exception("Error collecting %s: %s", channel, exc)

    finally:
        if client:
            await client.disconnect()
        if db_conn:
            db_conn.close()
        lock.release()


if __name__ == "__main__":
    if hasattr(asyncio, "run"):
        asyncio.run(main())
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(main())
        finally:
            loop.close()
