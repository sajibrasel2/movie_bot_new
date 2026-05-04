import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Optional

import mysql.connector
from telethon import TelegramClient
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

    # === টেক্সট ক্লিনিং ===
    # আমরা অরিজিনাল মেসেজ থেকে টেক্সট নিচ্ছি যাতে লাইনের স্পেস (newlines) ঠিক থাকে
    raw_text = ""
    if original_msg and original_msg.message:
        raw_text = original_msg.message
    else:
        raw_text = row.get("text") or ""

    # @username বা অন্য ট্যাগগুলো রিমুভ করা হচ্ছে
    clean_text = re.sub(r"@\w+", "", raw_text).strip()
    
    # প্রিফিক্স অ্যাড করা হচ্ছে (যদি থাকে)
    if MESSAGE_PREFIX:
        clean_text = f"{MESSAGE_PREFIX}\n\n{clean_text}".strip()

    # ক্যাপশন সাইজ লিমিট ঠিক রাখা
    caption_text = enforce_length(clean_text, MAX_CAPTION_LENGTH)
    full_text = enforce_length(clean_text, MAX_TEXT_LENGTH)

    from telethon.tl.types import MessageMediaWebPage

    for chat in TARGET_CHATS:
        try:
            has_real_media = (
                original_msg
                and original_msg.media
                and not isinstance(original_msg.media, MessageMediaWebPage)
            )
            if has_real_media:
                # অরিজিনাল মিডিয়া + ক্লিন করা ক্যাপশন (কোনো ফরোয়ার্ড ট্যাগ থাকবে না)
                await client.send_file(
                    entity=chat,
                    file=original_msg.media,
                    caption=caption_text
                )
            elif media_path and (BASE_DIR / media_path).exists():
                # যদি ফাইল লোকালি ডাউনলোড হয়ে থাকে
                await client.send_file(
                    entity=chat,
                    file=str(BASE_DIR / media_path),
                    caption=caption_text
                )
            else:
                if clean_text:
                    await client.send_message(entity=chat, message=full_text)
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
