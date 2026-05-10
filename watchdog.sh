#!/bin/bash
# Watchdog: auto-restart movie bot if it's not running
# Bot manages its own bot.pid file — watchdog only reads it

BOT_DIR="/home/techandc/movie_bot_new"
BOT_SCRIPT="bot.py"
PYTHON="/home/techandc/virtualenv/movie_bot_new/3.11/bin/python"
LOG="$BOT_DIR/bot.log"
PID_FILE="$BOT_DIR/bot.pid"
CRASH_FILE="$BOT_DIR/bot.crashes"
MAX_CRASHES=5          # After this many crashes, wait longer
COOLDOWN=300           # 5 min cooldown after too many crashes

cd "$BOT_DIR"

# Check if bot process is running via PID file
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        # Bot is running — reset crash counter and exit
        rm -f "$CRASH_FILE"
        exit 0
    fi
fi

# Also check with pgrep (fallback if pid file stale)
RUNNING=$(pgrep -f "$PYTHON.*$BOT_SCRIPT" 2>/dev/null)
if [ -n "$RUNNING" ]; then
    rm -f "$CRASH_FILE"
    exit 0
fi

# Bot is not running — check crash loop
CRASHES=0
if [ -f "$CRASH_FILE" ]; then
    CRASHES=$(cat "$CRASH_FILE" 2>/dev/null)
fi
CRASHES=$((CRASHES + 1))
echo "$CRASHES" > "$CRASH_FILE"

if [ "$CRASHES" -ge "$MAX_CRASHES" ]; then
    echo "$(date): Crash loop detected ($CRASHES crashes). Waiting ${COOLDOWN}s before restart." >> "$BOT_DIR/watchdog.log"
    sleep "$COOLDOWN"
    # Reset counter after cooldown
    echo "1" > "$CRASH_FILE"
fi

# Restart the bot (let bot.py write its own PID file)
echo "$(date): Restarting bot... (crash #$CRASHES)" >> "$BOT_DIR/watchdog.log"
nohup "$PYTHON" "$BOT_SCRIPT" >> "$LOG" 2>&1 &
echo "$(date): Bot started with PID $!" >> "$BOT_DIR/watchdog.log"
