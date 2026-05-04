#!/bin/bash
# Watchdog: auto-restart movie bot if it's not running

BOT_DIR="/home/techandc/movie_bot_new"
BOT_SCRIPT="bot.py"
PYTHON="/home/techandc/virtualenv/movie_bot_new/3.11/bin/python"
LOG="$BOT_DIR/bot.log"
PID_FILE="$BOT_DIR/bot.pid"

cd "$BOT_DIR"

# Check if bot process is running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        # Bot is running, exit
        exit 0
    fi
fi

# Also check with ps (fallback)
RUNNING=$(pgrep -f "$PYTHON.*$BOT_SCRIPT" 2>/dev/null)
if [ -n "$RUNNING" ]; then
    echo "$RUNNING" > "$PID_FILE"
    exit 0
fi

# Bot is not running — restart it
echo "$(date): Restarting bot..." >> "$BOT_DIR/watchdog.log"
nohup "$PYTHON" "$BOT_SCRIPT" >> "$LOG" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"
echo "$(date): Bot restarted with PID $NEW_PID" >> "$BOT_DIR/watchdog.log"
