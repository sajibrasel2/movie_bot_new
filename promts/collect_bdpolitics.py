#!/usr/bin/env python3
"""
BD Politics News Collector
============================
Same as collect_posts.py but uses config_bdpolitics.py
Scrapes BD news Telegram channels → stores in telegram_collected_posts_bdpolitics
"""

import sys
import os

# Use bdpolitics config instead of default config
sys.path.insert(0, os.path.dirname(__file__))

# Monkey-patch the config import
import config_bdpolitics as _cfg
import types

# Create a fake 'config' module pointing to bdpolitics config
fake_config = types.ModuleType('config')
fake_config.COLLECT_SETTINGS  = _cfg.COLLECT_SETTINGS
fake_config.DELIVERY_SETTINGS = _cfg.DELIVERY_SETTINGS
fake_config.MYSQL_CONFIG       = _cfg.MYSQL_CONFIG
fake_config.TELEGRAM_API       = _cfg.TELEGRAM_API
fake_config.SOURCE_CHANNELS    = _cfg.SOURCE_CHANNELS
fake_config.PRIORITY_CHANNELS  = _cfg.PRIORITY_CHANNELS
sys.modules['config'] = fake_config

# Now import and run collect_posts with bdpolitics config
from collect_posts import main
import asyncio

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
