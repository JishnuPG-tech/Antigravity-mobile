"""Async Telegram bot bridge to Antigravity backend.

The bot forwards messages and files to the FastAPI backend and displays
streaming responses. This is a minimal, extensible implementation.
"""
import asyncio
import os
import logging
from services.antigravity_manager import AntigravityManager
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from backend.app.config import settings

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

agy = AntigravityManager()


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


def main() -> None:
    token = os.getenv("BOT_TOKEN") or settings.bot_token
    if not token:
        raise SystemExit("BOT_TOKEN not set")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Authorization helper
    def parse_authorized():
        raw = settings.authorized_users or os.getenv("AUTHORIZED_USERS", "")
        out = set()
        for p in [x.strip() for x in raw.split(",") if x.strip()]:
            try:
                out.add(int(p))
            except Exception:
                continue
        return out

    AUTHORIZED = parse_authorized()

    def is_authorized(user_id: int) -> bool:
        # allow if AUTHORIZED is empty (dangerous) or user in set
        if not AUTHORIZED:
            return False
        return int(user_id) in AUTHORIZED

    # Recommended commands
    app.bot.set_my_commands([BotCommand("start", "Start the bot"), BotCommand("cancel", "Cancel running command")])

    logger.info("Starting Telegram bot")
    app.run_polling()


if __name__ == "__main__":
    main()
