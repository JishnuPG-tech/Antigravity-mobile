"""Async Telegram bot bridge to Antigravity backend.

The bot forwards messages and files to the FastAPI backend and displays
streaming responses. This is a minimal, extensible implementation.
"""
import asyncio
import os
import logging
import time
from services.antigravity_manager import AntigravityManager
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from backend.app.config import settings

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

agy = AntigravityManager()


def parse_authorized_users() -> set[int]:
    raw = settings.authorized_users or os.getenv("AUTHORIZED_USERS", "")
    users: set[int] = set()
    for value in [item.strip() for item in raw.split(",") if item.strip()]:
        try:
            users.add(int(value))
        except Exception:
            continue
    return users


AUTHORIZED_USERS = parse_authorized_users()


def is_authorized(user_id: int) -> bool:
    return bool(AUTHORIZED_USERS) and int(user_id) in AUTHORIZED_USERS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello — Antigravity bridge ready.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("Unauthorized.")
        return
    agy.sm.interrupt(str(user_id))
    await update.message.reply_text("Interrupted.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("Unauthorized.")
        return
    text = update.message.text or ""

    # Ensure session exists
    agy.start_for_user(str(user_id))

    # Send the input to the running agy CLI
    agy.send_command(str(user_id), text)

    # Create initial Telegram message and stream updates by tailing the tmux pipe-pane log
    sent = await update.message.reply_text("Running...")

    async def streamer():
        try:
            async for chunk in agy.sm.stream_output(str(user_id)):
                # update the message with the latest chunk appended
                try:
                    # keep message reasonably sized
                    display = chunk
                    if len(display) > 3500:
                        display = display[-3500:]
                    code_text = "```\n" + display + "\n```"
                    await context.bot.edit_message_text(chat_id=sent.chat_id, message_id=sent.message_id, text=code_text, parse_mode="Markdown")
                except Exception:
                    pass
        except asyncio.CancelledError:
            return

    # spawn background task
    context.application.create_task(streamer())


# Global application reference for async execution
telegram_app = None

async def run_bot_async() -> None:
    global telegram_app
    token = os.getenv("BOT_TOKEN") or settings.bot_token
    if not token:
        logger.warning("BOT_TOKEN not set; Telegram bot listener is idle")
        return

    base_url = os.getenv("TELEGRAM_BASE_URL")
    if base_url:
        logger.info(f"Using custom Telegram base URL: {base_url}")
        telegram_app = ApplicationBuilder().token(token).base_url(base_url).build()
    else:
        telegram_app = ApplicationBuilder().token(token).build()

    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("cancel", cancel))
    telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    logger.info("Initializing Telegram bot...")
    await telegram_app.initialize()
    logger.info("Starting Telegram bot...")
    await telegram_app.start()
    logger.info("Starting polling...")
    await telegram_app.updater.start_polling()


async def stop_bot_async() -> None:
    global telegram_app
    if telegram_app:
        logger.info("Stopping Telegram bot...")
        try:
            await telegram_app.updater.stop()
            await telegram_app.stop()
            await telegram_app.shutdown()
        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}")


def main() -> None:
    token = os.getenv("BOT_TOKEN") or settings.bot_token
    if not token:
        logger.error("BOT_TOKEN not set; Telegram bot will stay idle so the Space can continue starting")
        while True:
            time.sleep(60)
        return

    base_url = os.getenv("TELEGRAM_BASE_URL")
    if base_url:
        logger.info(f"Using custom Telegram base URL: {base_url}")
        app = ApplicationBuilder().token(token).base_url(base_url).build()
    else:
        app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    logger.info("Starting Telegram bot")
    try:
        app.run_polling()
    except Exception:
        logger.exception("Telegram bot crashed; sleeping before retry")
        while True:
            time.sleep(60)



if __name__ == "__main__":
    main()
