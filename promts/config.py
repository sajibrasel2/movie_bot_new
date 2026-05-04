"""
Configuration for Telegram Auto Fetch + Queue + Delivery System.
Store all sensitive info here and keep this file outside version control.
"""

# =========================
# MySQL Configuration
# =========================
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "techandc_bot",
    "password": "12345Sajibs6@",
    "database": "techandc_prompts",
    "charset": "utf8mb4",
    "autocommit": True,
}

# =========================
# Telegram Configuration
# =========================
TELEGRAM_API = {
    "api_id": 28186143,
    "api_hash": "6073c3149388bbc06e818add0be1622d",
    "session_string": (
        "1BVtsOJ0Bu1pxJKbdngNZprbcKPoGy5JsesQEEz6Wq_KgdkeQmkcH8Lto7vokIX"
        "Jomxjy8k9uoXIBDZvr01VwNTbrZKJOjo9gMVHanqyeA-kEFWrS4QNi_S_miWc3F"
        "L9Pk7F-Rr1N28jZEbu8yGx8qN774KT1J4DtA5QWkvt4_52UlU6InRiAhyBXUB_S"
        "Ogn5Xw06xHeKDjDxrQI5A-SfwD6Yl_NA5GIeOZz4KtLc333wa_nKEXbZ2_97m0Q"
        "3CpdsgmKS9KWaXmBqCu0s97y1nqXxHaqWh5oDBJ6048QmHedO7JMr-64W83yu4D"
        "DLcOBIds19nki4tngGdFBCVyMb1KlavbW-rqU="
    ),
    "bot_token": "8261646421:AAEd1yR5sqdQYFjf51tVHoBdurT-z_aYCYg",
    "bot_username": "DailyAI_Prompts",

    # ЁЯСЙ ржПржХрж╛ржзрж┐ржХ ржЯрж╛рж░рзНржЧрзЗржЯ (ржЧрзНрж░рзБржк + ржЪрзНржпрж╛ржирзЗрж▓)
    "target_channels": [
        "@DailyAI_Prompts",
        -1003564276724,
    ],
}

# =========================
# Priority / Source Channels
# =========================
AWAMI_PRIORITY = [
    "@StarAbhishekCrypto",
]

SOURCE_CHANNELS = [
    *AWAMI_PRIORITY,
    "@Modxdownload",
    "@AFRtechnology02",
    "-1001729314655",  # ApkCunk (Official)
    "@rirobincps",
    "@quincyplayer6", # <-- শুরুতে -100 যুক্ত করে এভাবে বসান
]

# lower-case + @ remove (priority logic)
PRIORITY_CHANNELS = [
    channel.lower().lstrip("@") for channel in AWAMI_PRIORITY
]

# =========================
# Collect Settings
# =========================
COLLECT_SETTINGS = {
    "lock_path": "locks/collect.lock",
    "log_file": "logs/collect.log",
    "media_dir": "media",
    "max_download_mb": 500,
    "max_messages_per_channel": 500,
    "max_scan_messages_per_channel": 2000,
    "source_channels": SOURCE_CHANNELS,
    "fresh_window_minutes": 720,
}

# =========================
# Delivery Settings
# =========================
DELIVERY_SETTINGS = {
    "lock_path": "locks/deliver.lock",
    "log_file": "logs/deliver.log",
    "batch_limit": 20,
    "delete_media_after_send": True,
    "bot_api_timeout": 900,
    "message_prefix": "",
    "fresh_window_minutes": 780,
}