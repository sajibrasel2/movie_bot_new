"""
Configuration for BD Politics News Channel System.
Scrapes news from BD news Telegram channels → delivers to @bdwar71
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
    "bot_token": "8351737906:AAHEHy27Nk_erz1EE2H6BdUrvhHTGGaQedk",
    "bot_username": "newscombobot",

    # Target: BD Politics News Channel
    "target_channels": [
        "@bdwar71",
    ],
}

# =========================
# Priority / Source Channels
# =========================
# News sources — existing system channels + BD news channels
AWAMI_PRIORITY = [
    "@StarAbhishekCrypto",
]

# BD News Telegram Channels (public news channels)
BD_NEWS_CHANNELS = [
    "@SomoyTV",           # সময় টিভি
    "@ATNNewsOfficial",   # ATN News
    "@Independent_bd",    # Independent TV
    "@channelionline",    # Channel i
    "@jamunatelevision",  # যমুনা টেলিভিশন
    "@RTVnews24",         # RTV
    "@banglavision_news", # Banglavision
    "@NTVnewsBD",         # NTV
    "@DBC_news24",        # DBC News
    "@ekattor_tv",        # একাত্তর টিভি
    "@SARABANGLA",        # সারাবাংলা.নেট
    "@TheDailyStar",      # Daily Star
    "@DhakaPost",         # ঢাকা পোস্ট
    "@kaler_kantho_official", # কালের কণ্ঠ
    "@ProthomAloOfficial",    # প্রথম আলো
]

SOURCE_CHANNELS = [
    # Existing app/mod channels (keep as before)
    *AWAMI_PRIORITY,
    "@Modxdownload",
    "@AFRtechnology02",
    "-1001729314655",  # ApkCunk (Official)
    "@rirobincps",
    "@Getmodpcs",
    # BD News channels
    *BD_NEWS_CHANNELS,
]

# lower-case + @ remove (priority logic)
PRIORITY_CHANNELS = [
    channel.lower().lstrip("@") for channel in AWAMI_PRIORITY
]

# =========================
# Collect Settings
# =========================
COLLECT_SETTINGS = {
    "lock_path": "locks/collect_bdpolitics.lock",
    "log_file": "logs/collect_bdpolitics.log",
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
    "lock_path": "locks/deliver_bdpolitics.lock",
    "log_file": "logs/deliver_bdpolitics.log",
    "batch_limit": 20,
    "delete_media_after_send": True,
    "bot_api_timeout": 900,
    "message_prefix": "",
    "fresh_window_minutes": 780,
}
