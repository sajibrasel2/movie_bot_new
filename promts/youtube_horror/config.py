"""
EpisodeBD Horror Story Audio Bot Configuration
episodebd.com থেকে Odvootoore, Bhoot.com, Afnan Vai এর অডিও কালেক্ট করে Telegram-এ পাঠানোর জন্য
"""

import sys
from pathlib import Path

# Parent folder থেকে config import করুন
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Main config থেকে import
try:
    from config import TELEGRAM_API, MYSQL_CONFIG as PARENT_MYSQL_CONFIG
    
    # Telegram configuration
    TELEGRAM_BOT_TOKEN = TELEGRAM_API.get("bot_token")
    TARGET_CHANNEL = TELEGRAM_API.get("target_channels", [])[0] if TELEGRAM_API.get("target_channels") else -1004296636853
    
    # MySQL configuration (parent থেকে)
    MYSQL_CONFIG = PARENT_MYSQL_CONFIG.copy()
    
    print(f"✅ Config loaded from parent")
    print(f"   Bot Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    print(f"   Target Channel: {TARGET_CHANNEL}")
    print(f"   Database: {MYSQL_CONFIG.get('database')}")
    
except ImportError as e:
    print(f"⚠️  Could not import from parent config: {e}")
    print("   Using default configuration")
    
    # Default fallback configuration
    TELEGRAM_BOT_TOKEN = "8261646421:AAEd1yR5sqdQYFjf51tVHoBdurT-z_aYCYg"
    TARGET_CHANNEL = -1004296636853
    MYSQL_CONFIG = {
        "host": "localhost",
        "user": "techandc_bot",
        "password": "12345Sajibs6@",
        "database": "techandc_prompts",
        "charset": "utf8mb4",
        "autocommit": True,
    }

# EpisodeBD Configuration
EPISODEBD_CONFIG = {
    "base_url": "https://episodebd.com",
    "check_interval_hours": 12,  # প্রতি 12 ঘণ্টায় চেক করবে
    "max_pages_to_check": 3,  # প্রথম 3 পেজ চেক করবে
    "max_episodes_per_run": 10,  # একবারে সর্বোচ্চ 10টি episode
    
    # Target categories to collect
    "categories": [
        "odvootoore",    # Odvootoore by Babu Vai
        "bhoot_com",     # Bhoot.com by RJ Russell
        "afnan",         # Afnan The Horror World
    ],
}

# Audio Download Settings
AUDIO_SETTINGS = {
    "max_filesize_mb": 50,  # Telegram limit
    "download_dir": "audio",
    "timeout_seconds": 60,
}

# Message Templates (Bengali) - Different for each category
MESSAGE_TEMPLATES = {
    'odvootoore': """
{emoji} **অদ্ভুতুড়ে - Babu Vai** {emoji}

🎧 {title}

📦 ফাইল সাইজ: {file_size}
📅 তারিখ: {date}

🔊 ভৌতিক গল্প শুনুন এখনই!

#অদ্ভুতুড়ে #Odvootoore #BabuVai #HorrorStory #BengaliHorror
""",
    
    'bhoot_com': """
{emoji} **Bhoot.Com - RJ Russell** {emoji}

🎧 {title}

📦 ফাইল সাইজ: {file_size}
📅 তারিখ: {date}

🔊 ভয়ংকর গল্প শুনুন এখনই!

#BhootDotCom #RJRussell #HorrorStory #BengaliHorror
""",
    
    'afnan': """
{emoji} **Horror Night with Afnan Vai** {emoji}

🎧 {title}

📦 ফাইল সাইজ: {file_size}
📅 তারিখ: {date}

🔊 রহস্যময় গল্প শুনুন এখনই!

#AfnanVai #HorrorWorld #HorrorStory #BengaliHorror
""",
    
    'default': """
{emoji} **ভূতের গল্প** {emoji}

🎧 {title}

📦 ফাইল সাইজ: {file_size}
📅 তারিখ: {date}

🔊 অডিও গল্প শুনুন এখনই!

#HorrorStory #BengaliHorror #BhootKahini
""",
}

# Logging
LOG_FILE = "logs/episodebd_horror.log"
LOCK_FILE = "locks/episodebd_horror.lock"
