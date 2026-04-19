"""Minimal test bot — just replies 'pong' to any text message.
Run this on cPanel to test if handlers work at all.
"""
import asyncio
import logging
import os
import signal

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = "8294665841:AAG-MpBou_a3FgHoi0KFMAzWH5JBPwOaqu4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("START handler called!")
    await update.message.reply_text("✅ Test bot is alive!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("ECHO handler called! text=%s", update.message.text[:50])
    await update.message.reply_text(f"pong: {update.message.text}")

async def error_handler(update, context):
    logger.error("ERROR: %s", context.error, exc_info=context.error)

def main():
    # Kill old instances
    pid_file = os.path.join(os.path.dirname(__file__), "pingbot.pid")
    if os.path.exists(pid_file):
        try:
            with open(pid_file) as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 9)
        except Exception:
            pass
        try:
            os.remove(pid_file)
        except Exception:
            pass

    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.add_error_handler(error_handler)
    logger.info("Test bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
