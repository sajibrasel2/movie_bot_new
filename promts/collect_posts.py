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
# MEDIA-ONLY SOURCES (ADDED)
# ======================
MEDIA_ONLY_CHANNELS = {
    "modxpremiumchat",  # chat group → only media
}

# ======================
# SPAM / GAMBLING FILTER
# ======================
SPAM_KEYWORDS = [
    "1win", "1xbet", "99xo", "mostbet", "parimatch", "bet365",
    "betting", "casino", "গেমিং প্ল্যাটফর্ম", "বোনাস", "ডিপোজিট",
    "রেজিস্টার করুন", "ফ্রিবেট", "freebet", "বেটিং",
    "জিতে নিন", "পুরস্কার", "রেফার", "গ্র্যান্ড প্রাইজ",
    "রেড এনভেলপ", "vip এক্সক্লুসিভ",
]


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
    if not text:
        return ""
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"\s+", " ", text)
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
# MEDIA-ONLY HELPER (ADDED)
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


def is_spam_post(text: str) -> bool:
    text = text.lower()
    for keyword in SPAM_KEYWORDS:
        if keyword.lower() in text:
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

        # 🔒 MEDIA-ONLY FILTER (ADDED, NOTHING ELSE CHANGED)
        if is_media_only_source(channel_key):
            if not is_allowed_document_message(message):
                continue

        raw_text = message.message or ""

        # Skip spam / gambling / betting posts
        if is_spam_post(raw_text):
            logging.info("Skipping spam post %s from %s", message.id, channel_handle)
            continue

        text = strip_text_keep_links(raw_text)

        if contains_live_link(raw_text):
            text = "📡 LIVE স্ট্রিম লিংক:\n" + text

        media_payload = await download_media(message, channel_key)

        media_path = None
        media_type = None

        if media_payload:
            if media_payload["type"] == "too_large":
                text = (text + "\n\n⚠️ মিডিয়া ফাইলটি অনেক বড়").strip()
            else:
                media_path = media_payload["path"]
                media_type = media_payload["type"]

        if not text and not media_path:
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
            logging.info("Queued %s from %s", message.id, channel_handle)
        except MySQLError as exc:
            if exc.errno != 1062:
                logging.error("DB error %s: %s", message.id, exc)

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