"""Utility to drop legacy tables that are not needed for the forwarding bot."""
from __future__ import annotations

import logging

import mysql.connector

from config import MYSQL_CONFIG

TABLES_TO_DROP = [
    "referral_codes",
    "telegram_fast_posts",
    "telegram_seen_codes",
    "telegram_seen_links",
    "referral_events",
    "referral_report_state",
    "channel_metrics",
    "latest_codes",
    "user_notification_prefs",
    "user_wallets",
    "user_wallet_requests",
    "bot_state",
]


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    try:
        for table in TABLES_TO_DROP:
            logging.info("Dropping table if exists: %s", table)
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
        logging.info("Legacy tables removed.")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
