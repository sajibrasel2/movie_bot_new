import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Optional

import mysql.connector
from telethon import TelegramClient, Button  # <--- Button ইম্পোর্ট করা হয়েছে
from telethon.extensions import html
from telethon.errors import RPCError
from telethon.sessions import StringSession

from config import DELIVERY_SETTINGS, MYSQL_CONFIG, PRIORITY_CHANNELS, TELEGRAM_API

# ======================
# Config / Constants
# ======================
BASE_DIR = Path(__file__).resolve().parent
LOCK_PATH = BASE_DIR / DELIVERY_SETTINGS["lock_path"]
LOG_FILE = BASE_DIR / DELIVERY_SETTINGS["log_file"]

BATCH_LIMIT = int(DELIVERY_SETTINGS.get("batch_limit", 20))
DELETE_MEDIA_AFTER_SEND = bool(DELIVERY_SETTINGS.get("delete_media_after_send", True))
BOT_TIMEOUT = int(DELIVERY_SETTINGS.get("bot_api_timeout", 30))

MESSAGE_PREFIX = DELIVERY_SETTINGS.get("message_prefix", "")
TARGET_CHATS = TELEGRAM_API["target_channels"]

MAX_TEXT_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024
MAX_MEDIA_BYTES = 500 * 1024 * 1024  # ~500MB


# ======================
# File Lock
# ======================
class FileLock:
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
        if self.fd:
            try:
                os.close(self.fd)
            except OSError:
                pass
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


def mark_post_failed(db_conn, row_id: int, reason: str):
    cur = db_conn.cursor()
    cur.execute(
        "UPDATE telegram_collected_posts SET status='failed', fail_reason=%s WHERE id=%s",
        (reason[:2000], row_id),
    )
    cur.close()


def normalize_channel_handle(handle: str):
    value = (handle or "").strip()
    if not value:
        return value
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if not value.startswith("@"):
        return f"@{value}"
    return value


# ======================
# Fetch posts
# ======================
def fetch_pending_posts(db_conn):
    cursor = db_conn.cursor(dictionary=True)
    priority_clause = ""
    params = ["pending", "failed"]

    if PRIORITY_CHANNELS:
        placeholders = ",".join(["%s"] * len(PRIORITY_CHANNELS))
        priority_clause = f"CASE WHEN source_channel IN ({placeholders}) THEN 0 ELSE 1 END, "
        params.extend(PRIORITY_CHANNELS)

    params.append(BATCH_LIMIT)

    query = f"""
        SELECT *
        FROM telegram_collected_posts
        WHERE status IN (%s, %s)
        ORDER BY
            CASE WHEN status='pending' THEN 0 ELSE 1 END,
            {priority_clause}
            created_at ASC, id ASC
        LIMIT %s
    """

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    return rows


# ======================
# Message building
# ======================
def enforce_length(message: str, limit: int) -> str:
    if len(message) <= limit:
        return message
    return message[:limit-3].rstrip() + "..."


def deliver_row(row: dict):
    # Just a placeholder to maintain structure, logic moved to forward_to_all
    return True, ""


# ======================
# Telegram send helpers (Telethon)
# ======================
async def forward_to_all(client: TelegramClient, row: dict):
    source = normalize_channel_handle(row.get("source_channel") or "")
    msg_id = row.get("source_message_id")
    media_path = row.get("media_path")

    if not source or not msg_id:
        raise RuntimeError("Missing source_channel/source_message_id")

    original_msg = None
    try:
        msgs = await client.get_messages(source, ids=[int(msg_id)])
        if msgs:
            original_msg = msgs[0]
    except Exception:
        pass

    # === টেক্সট ক্লিনিং + ইনলাইন লিংক সংরক্ষণ ===
    use_html = False
    if original_msg and original_msg.message:
        if original_msg.entities:
            raw_text = html.unparse(original_msg.message, original_msg.entities)
            use_html = True
        else:
            raw_text = original_msg.message
    else:
        raw_text = row.get("text") or ""

    # ১. টেলিগ্রাম লিংকসহ HTML অ্যাঙ্কর ট্যাগ এবং ভেতরের টেক্সট সম্পূর্ণ রিমুভ (লাইভ লিংক বাদে)
    clean_text = re.sub(r'<a\s+href=["\'](?:https?://)?(?:t\\.me|telegram\\.me|telegram\\.dog)/(?!.*/live)[^"\']*["\']>(.*?)</a>', '', raw_text, flags=re.IGNORECASE)
    # ২. সাধারণ র (raw) টেলিগ্রাম লিংক টেক্সট থেকে রিমুভ (লাইভ লিংক বাদে)
    clean_text = re.sub(r'(?:https?://)?(?:t\\.me|telegram\\.me|telegram\\.dog)/(?!.*/live)[^\s<>]+', '', clean_text, flags=re.IGNORECASE)
    # ৩. @ইউজারনেম রিমুভ করা হচ্ছে
    clean_text = re.sub(r"@\w+", "", clean_text).strip()
    # ৪. লিংক রিমুভ করার পর তৈরি হওয়া অতিরিক্ত ফাঁকা লাইন ক্লিন করা
    clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
    
    if MESSAGE_PREFIX:
        clean_text = f"{MESSAGE_PREFIX}\n\n{clean_text}".strip()

    caption_text = enforce_length(clean_text, MAX_CAPTION_LENGTH)
    full_text = enforce_length(clean_text, MAX_TEXT_LENGTH)

    from telethon.tl.types import MessageMediaWebPage

    # ==========================================
    # 🔗 আকর্ষণীয় ইনলাইন বাটন সেটআপ (আপনার লিংক)
    # ==========================================
    ad_buttons = [
        [Button.url("📥 Download Server 1", "https://omg10.com/4/11017767")],
        [Button.url("🚀 Fast Download Server 2", "https://www.effectivecpmnetwork.com/mgtqwzbp?key=5c4003e0ae2b0ebd387daded087bc9aa")]
    ]

    for chat in TARGET_CHATS:
        try:
            pmode = 'html' if use_html else None

            has_real_media = (
                original_msg
                and original_msg.media
                and not isinstance(original_msg.media, MessageMediaWebPage)
            )
            
            # প্রতিটি মেসেজ পাঠানোর সময় buttons=ad_buttons যুক্ত করা হয়েছে
            if has_real_media:
                await client.send_file(
                    entity=chat,
                    file=original_msg.media,
                    caption=caption_text,
                    parse_mode=pmode,
                    buttons=ad_buttons  # <--- বাটন এখানে
                )
            elif media_path and (BASE_DIR / media_path).exists():
                await client.send_file(
                    entity=chat,
                    file=str(BASE_DIR / media_path),
                    caption=caption_text,
                    parse_mode=pmode,
                    buttons=ad_buttons  # <--- বাটন এখানে
                )
            else:
                if clean_text:
                    await client.send_message(
                        entity=chat,
                        message=full_text,
                        parse_mode=pmode,
                        buttons=ad_buttons  # <--- বাটন এখানে
                    )
        except RPCError as exc:
            raise RuntimeError(str(exc))


# ======================
# Cleanup helpers
# ======================
def delete_media_file(row: dict):
    if row.get("media_path"):
        try:
            (BASE_DIR / row["media_path"]).unlink()
        except OSError:
            pass


def remove_row(db_conn, row_id: int):
    cur = db_conn.cursor()
    cur.execute(
        "DELETE FROM telegram_collected_posts WHERE id=%s",
        (row_id,),
    )
    cur.close()


# ======================
# Main
# ======================
def main():
    setup_logging()
    lock = FileLock(LOCK_PATH)

    try:
        lock.acquire()
    except RuntimeError as e:
        logging.warning(e)
        return

    if hasattr(asyncio, "run"):
        asyncio.run(_run_delivery(lock))
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run_delivery(lock))
        finally:
            loop.close()


async def _run_delivery(lock: FileLock):
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

        sent = failed = 0

        while True:
            rows = fetch_pending_posts(db_conn)
            if not rows:
                if sent == 0 and failed == 0:
                    logging.info("No queued posts")
                break

            for row in rows:
                ok, reason = deliver_row(row)
                if not ok:
                    failed += 1
                    logging.error("Failed post %s: %s", row["id"], reason)
                    mark_post_failed(db_conn, row["id"], reason)
                else:
                    try:
                        await forward_to_all(client, row)
                        sent += 1
                        logging.info("Delivered post %s", row["id"])
                    except Exception as exc:
                        failed += 1
                        logging.error("Failed post %s: %s", row["id"], exc)
                        mark_post_failed(db_conn, row["id"], str(exc))

                remove_row(db_conn, row["id"])
                if DELETE_MEDIA_AFTER_SEND:
                    delete_media_file(row)

        logging.info(
            "Delivery finished. Sent=%s Failed=%s",
            sent,
            failed,
        )

    finally:
        if client:
            await client.disconnect()
        if db_conn:
            db_conn.close()
        lock.release()


if __name__ == "__main__":
    main()