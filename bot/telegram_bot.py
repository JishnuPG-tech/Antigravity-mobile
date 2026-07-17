"""Antigravity Telegram Bot — Live Terminal Bridge.

Provides a full live-streaming terminal experience directly inside Telegram:
  • Characters are rendered live as they arrive from the PTY
  • Full keyboard mapping: arrows, Tab, Ctrl-C/D/Z, ESC, Enter, Backspace, etc.
  • Terminal emulator: handles \\r (CR overwrite), \\x08 (backspace), ANSI stripping
  • Google OAuth flow detected and surfaced as a tap-to-open button
  • Auto-launches `agy` on first session connect
  • Cloud file upload/download support
"""

import asyncio
import os
import logging
import time
import re
import subprocess
from collections import defaultdict

from services.antigravity_manager import AntigravityManager
from telegram import (
    Update,
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.error import BadRequest, RetryAfter

from backend.app.config import settings

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

agy = AntigravityManager()

# ---------------------------------------------------------------------------
# Live-stream state per user: holds the current "virtual screen buffer"
# ---------------------------------------------------------------------------
# user_id (str) -> current terminal string buffer (post-processed)
_screen_buffer: dict[str, str] = defaultdict(str)
# user_id -> asyncio.Event, set whenever new output arrives
_output_events: dict[str, asyncio.Event] = defaultdict(asyncio.Event)
# user_id -> active background streamer task
_stream_tasks: dict[str, asyncio.Task] = {}

# How many chars of the tail we show in Telegram (Telegram max 4096 incl markdown)
SCREEN_TAIL = 3700
# Minimum interval between successive Telegram edit_message calls (Telegram rate limit ~1 edit/sec per message)
EDIT_INTERVAL = 0.35


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# ANSI / PTY terminal emulator helpers
# ---------------------------------------------------------------------------

# Compiled patterns for speed
_RE_OSC8 = re.compile(r'\x1b\]8;[^\x1b\x07]*[\x1b\x07]')
_RE_CSI = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]')
_RE_ESC = re.compile(r'\x1b.')
_RE_CSI_LEFTOVER = re.compile(r'\[[0-9;?]*[mJKhHdDL]')
_RE_GOOGLE_URL = re.compile(
    r'https://accounts\.google\.com/o/oauth2/auth\?[a-zA-Z0-9_.~\-=+%&]+'
)
_GARBAGE = {']', '', ']', ']];', ';', 'm', 'm ]8;;', '[m', '0m', '0'}


def apply_pty_chunk(buffer: str, chunk: str) -> str:
    """Apply a raw PTY chunk to the current string buffer.

    Handles:
      - \\x08 (backspace): delete last character
      - \\r   (CR): move cursor to start of current line (overwrite)
      - All other printable characters: appended
    """
    for char in chunk:
        if char == '\x08':
            if buffer:
                buffer = buffer[:-1]
        elif char == '\r':
            last_nl = buffer.rfind('\n')
            buffer = buffer[:last_nl + 1] if last_nl != -1 else ''
        else:
            buffer += char
    return buffer


def strip_ansi(text: str) -> str:
    """Strip all ANSI/VT escape sequences, returning plain text."""
    # OSC-8 hyperlinks
    text = _RE_OSC8.sub('', text)
    # CSI sequences (colours, cursor movement, etc.)
    text = _RE_CSI.sub('', text)
    # Remaining bare ESC sequences
    text = _RE_ESC.sub('', text)
    # Bracketed paste mode artifacts
    text = text.replace("[?2004l", "").replace("[?2004h", "")
    # Any leftover partial CSI
    text = _RE_CSI_LEFTOVER.sub('', text)
    # Other control chars except \\n
    text = re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text


def detect_google_url(raw_chunk: str) -> str | None:
    """Return the Google OAuth URL if present in the raw (pre-ANSI-strip) chunk."""
    # Try raw chunk first
    m = _RE_GOOGLE_URL.search(raw_chunk)
    if m:
        url = m.group(0).rstrip(']\\;').split()[0]
        return url
    return None


def process_raw_chunk(user_id: str, raw: str) -> tuple[str, str | None]:
    """Update the screen buffer for user_id with a raw PTY chunk.

    Returns:
        (new_buffer_str, auth_url_or_None)
    """
    # First detect Google OAuth URL in the raw bytes before stripping
    auth_url = detect_google_url(raw)

    # Apply CR/backspace emulation on the *stripped* text
    cleaned = strip_ansi(raw)
    if cleaned in _GARBAGE:
        cleaned = ''

    buf = _screen_buffer[user_id]
    buf = apply_pty_chunk(buf, cleaned)
    _screen_buffer[user_id] = buf
    return buf, auth_url


def screen_tail(user_id: str) -> str:
    """Return the last SCREEN_TAIL characters of the user's screen buffer."""
    buf = _screen_buffer[user_id]
    if len(buf) > SCREEN_TAIL:
        # Cut at a newline boundary for clean display
        cut = buf[-SCREEN_TAIL:]
        nl = cut.find('\n')
        if nl != -1:
            cut = cut[nl + 1:]
        return cut
    return buf


# ---------------------------------------------------------------------------
# Keyboard layouts
# ---------------------------------------------------------------------------

def get_control_keyboard(user_id: str) -> InlineKeyboardMarkup:
    """Full keyboard mapping matching Antigravity CLI key bindings."""
    return InlineKeyboardMarkup([
        # Row 1: Navigation
        [
            InlineKeyboardButton("⬆️", callback_data="key_Up"),
        ],
        [
            InlineKeyboardButton("⬅️", callback_data="key_Left"),
            InlineKeyboardButton("↵ Enter", callback_data="key_Enter"),
            InlineKeyboardButton("➡️", callback_data="key_Right"),
        ],
        [
            InlineKeyboardButton("⬇️", callback_data="key_Down"),
            InlineKeyboardButton("⇥ Tab", callback_data="key_Tab"),
            InlineKeyboardButton("⌫ BS", callback_data="key_BSpace"),
        ],
        # Row 2: Modifiers
        [
            InlineKeyboardButton("ESC", callback_data="key_Escape"),
            InlineKeyboardButton("Ctrl-C", callback_data="key_ctrl_c"),
            InlineKeyboardButton("Ctrl-D", callback_data="key_ctrl_d"),
            InlineKeyboardButton("Ctrl-Z", callback_data="key_ctrl_z"),
        ],
        # Row 3: Function keys used by agy/opencode TUI
        [
            InlineKeyboardButton("F1", callback_data="key_F1"),
            InlineKeyboardButton("F2", callback_data="key_F2"),
            InlineKeyboardButton("F3", callback_data="key_F3"),
            InlineKeyboardButton("F4", callback_data="key_F4"),
            InlineKeyboardButton("F5", callback_data="key_F5"),
        ],
        # Row 4: Page navigation
        [
            InlineKeyboardButton("PgUp", callback_data="key_PPage"),
            InlineKeyboardButton("PgDn", callback_data="key_NPage"),
            InlineKeyboardButton("Home", callback_data="key_Home"),
            InlineKeyboardButton("End", callback_data="key_End"),
        ],
        # Row 5: Session controls
        [
            InlineKeyboardButton("🚀 Launch agy", callback_data="ctrl_agy"),
            InlineKeyboardButton("🔄 Refresh", callback_data="ctrl_refresh"),
        ],
        [
            InlineKeyboardButton("🛑 Ctrl-C (Stop)", callback_data="ctrl_interrupt"),
            InlineKeyboardButton("📋 Clear Screen", callback_data="ctrl_clear"),
        ],
    ])


def get_auth_keyboard(auth_url: str, user_id: str) -> InlineKeyboardMarkup:
    """Keyboard shown when Google OAuth is required."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Log In with Google", url=auth_url)],
        [InlineKeyboardButton("🔄 Refresh Screen", callback_data="ctrl_refresh")],
    ])


# ---------------------------------------------------------------------------
# tmux key sending
# ---------------------------------------------------------------------------

# Map callback_data key names to tmux send-keys values
KEY_MAP = {
    "Up":       "Up",
    "Down":     "Down",
    "Left":     "Left",
    "Right":    "Right",
    "Enter":    "Enter",
    "Tab":      "Tab",
    "BSpace":   "BSpace",
    "Escape":   "Escape",
    "ctrl_c":   "C-c",
    "ctrl_d":   "C-d",
    "ctrl_z":   "C-z",
    "F1":       "F1",
    "F2":       "F2",
    "F3":       "F3",
    "F4":       "F4",
    "F5":       "F5",
    "PPage":    "PPage",
    "NPage":    "NPage",
    "Home":     "Home",
    "End":      "End",
}


def send_tmux_key(user_id: str, key: str) -> None:
    """Send a named key to the user's tmux session."""
    session = agy.sm._session_name(str(user_id))
    tmux_key = KEY_MAP.get(key, key)
    try:
        subprocess.run(["tmux", "send-keys", "-t", session, tmux_key], check=True)
    except Exception as e:
        logger.warning(f"tmux send-key {key}: {e}")


def send_tmux_text(user_id: str, text: str) -> None:
    """Send raw text (followed by Enter) to the user's tmux session."""
    session = agy.sm._session_name(str(user_id))
    try:
        subprocess.run(["tmux", "send-keys", "-t", session, text, "Enter"], check=True)
    except Exception as e:
        logger.warning(f"tmux send-text: {e}")


# ---------------------------------------------------------------------------
# Live streaming background task per user
# ---------------------------------------------------------------------------

async def _background_streamer(user_id: str) -> None:
    """Tail the PTY log file and update _screen_buffer; set _output_events."""
    try:
        async for chunk in agy.sm.stream_output(user_id):
            if not chunk:
                continue
            _screen_buffer[user_id]  # ensure key exists
            process_raw_chunk(user_id, chunk)
            _output_events[user_id].set()
    except asyncio.CancelledError:
        return
    except Exception as e:
        logger.error(f"Streamer error for user {user_id}: {e}")


def ensure_streamer(user_id: str, app) -> None:
    """Ensure a background streaming task exists for this user."""
    task = _stream_tasks.get(user_id)
    if task is None or task.done():
        t = app.create_task(_background_streamer(user_id))
        _stream_tasks[user_id] = t


# ---------------------------------------------------------------------------
# Render current terminal screen to a Telegram message
# ---------------------------------------------------------------------------

async def render_screen_to_message(
    context,
    chat_id: int,
    message_id: int,
    user_id: str,
    auth_url: str | None = None,
):
    """Edit the Telegram message to show current screen buffer."""
    tail = screen_tail(user_id)

    if auth_url:
        text = (
            "🔑 *Antigravity Login Required*\n\n"
            "Tap the button below to authorize with Google, then copy the "
            "verification code from your browser and paste it here in the chat:"
        )
        markup = get_auth_keyboard(auth_url, user_id)
        parse_mode = "Markdown"
    else:
        if not tail.strip():
            tail = "(waiting for output...)"
        # Wrap in monospace code block
        # Escape backticks inside content
        safe = tail.replace('`', '\u02cb')
        text = "```\n" + safe + "\n```"
        markup = get_control_keyboard(user_id)
        parse_mode = "Markdown"

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=markup,
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.debug(f"edit_message_text: {e}")
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after + 0.5)
    except Exception as e:
        logger.debug(f"render_screen: {e}")


# ---------------------------------------------------------------------------
# Live polling loop: drives editing the Telegram message as output arrives
# ---------------------------------------------------------------------------

async def _live_update_loop(
    context,
    user_id: str,
    chat_id: int,
    message_id: int,
    timeout: float = 60.0,
):
    """Drive edit_message_text calls while output is arriving.

    Polls _output_events[user_id] and edits the message as fast as Telegram
    allows (rate-limited to EDIT_INTERVAL). Stops after `timeout` seconds
    of no new output.
    """
    event = _output_events[user_id]
    deadline = time.monotonic() + timeout
    last_edit = 0.0
    last_auth_url: str | None = None

    while time.monotonic() < deadline:
        # Wait for new output (up to 1s to check deadline)
        try:
            await asyncio.wait_for(asyncio.shield(event.wait()), timeout=1.0)
        except asyncio.TimeoutError:
            continue

        event.clear()
        deadline = time.monotonic() + timeout  # reset on new output

        # Rate limit edits
        now = time.monotonic()
        gap = now - last_edit
        if gap < EDIT_INTERVAL:
            await asyncio.sleep(EDIT_INTERVAL - gap)

        # Detect auth URL in current buffer
        buf = _screen_buffer[user_id]
        auth_m = _RE_GOOGLE_URL.search(buf)
        auth_url = auth_m.group(0).rstrip(']\\;').split()[0] if auth_m else None

        await render_screen_to_message(
            context, chat_id, message_id, user_id, auth_url
        )
        last_edit = time.monotonic()

    # Final update after loop ends
    buf = _screen_buffer[user_id]
    auth_m = _RE_GOOGLE_URL.search(buf)
    auth_url = auth_m.group(0).rstrip(']\\;').split()[0] if auth_m else None
    await render_screen_to_message(
        context, chat_id, message_id, user_id, auth_url
    )


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    # Ensure session and streamer
    agy.start_for_user(str(user_id))
    ensure_streamer(str(user_id), context.application)

    # Auto-launch agy
    send_tmux_text(user_id, "agy")

    sent = await update.message.reply_text(
        "```\nAntigravity CLI starting...\n```",
        parse_mode="Markdown",
        reply_markup=get_control_keyboard(str(user_id)),
    )

    context.application.create_task(
        _live_update_loop(
            context, str(user_id),
            sent.chat_id, sent.message_id,
            timeout=120.0,
        )
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Unauthorized.")
        return
    agy.sm.interrupt(str(user_id))
    await update.message.reply_text("🛑 Sent Ctrl-C to session.")


async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    ws = os.path.join(agy.sm.workspace_root, f"user_{user_id}", "default")
    os.makedirs(ws, exist_ok=True)

    files = [f for f in os.listdir(ws) if os.path.isfile(os.path.join(ws, f)) and not f.startswith(".")]
    if not files:
        await update.message.reply_text("📁 Workspace is empty.")
        return

    file_list = "\n".join([f"• `{name}`" for name in sorted(files)])
    await update.message.reply_text(
        f"📁 *Workspace Files:*\n\n{file_list}\n\nUse `/download <filename>` to retrieve.",
        parse_mode="Markdown",
    )


async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: `/download <filename>`", parse_mode="Markdown")
        return

    filename = os.path.basename(" ".join(context.args))
    ws = os.path.join(agy.sm.workspace_root, f"user_{user_id}", "default")
    file_path = os.path.join(ws, filename)

    if not os.path.exists(file_path):
        await update.message.reply_text(f"❌ `{filename}` not found.", parse_mode="Markdown")
        return

    await update.message.reply_text(f"📤 Uploading `{filename}`...", parse_mode="Markdown")
    try:
        with open(file_path, "rb") as f:
            await update.message.reply_document(document=f, filename=filename)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def clear_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear the local screen buffer for a fresh view."""
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return
    _screen_buffer[str(user_id)] = ""
    await update.message.reply_text(
        "```\n(screen cleared)\n```",
        parse_mode="Markdown",
        reply_markup=get_control_keyboard(str(user_id)),
    )


# ---------------------------------------------------------------------------
# Main message handler
# ---------------------------------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    ws = os.path.join(agy.sm.workspace_root, f"user_{user_id}", "default")
    os.makedirs(ws, exist_ok=True)

    # --- File uploads ---
    if update.message.document:
        doc = update.message.document
        file_name = doc.file_name
        file_path = os.path.join(ws, file_name)
        sent_msg = await update.message.reply_text(f"📥 Saving `{file_name}` to workspace...", parse_mode="Markdown")
        try:
            tg_file = await context.bot.get_file(doc.file_id)
            await tg_file.download_to_drive(file_path)
            await sent_msg.edit_text(f"✅ Saved `{file_name}` to workspace.", parse_mode="Markdown")
        except Exception as e:
            await sent_msg.edit_text(f"❌ Failed: {e}")
        return

    if update.message.photo:
        photo = update.message.photo[-1]
        file_name = f"photo_{int(time.time())}.jpg"
        file_path = os.path.join(ws, file_name)
        sent_msg = await update.message.reply_text("📸 Saving image...", parse_mode="Markdown")
        try:
            tg_file = await context.bot.get_file(photo.file_id)
            await tg_file.download_to_drive(file_path)
            await sent_msg.edit_text(f"✅ Saved as `{file_name}`.", parse_mode="Markdown")
        except Exception as e:
            await sent_msg.edit_text(f"❌ Failed: {e}")
        return

    # --- Text command: send to CLI ---
    text = (update.message.text or "").strip()
    if not text:
        return

    # Ensure session exists and streamer is running
    agy.start_for_user(str(user_id))
    ensure_streamer(str(user_id), context.application)

    # Send text to tmux (with Enter)
    send_tmux_text(user_id, text)

    # Show a live-updating message
    sent = await update.message.reply_text(
        "```\nSending...\n```",
        parse_mode="Markdown",
        reply_markup=get_control_keyboard(str(user_id)),
    )

    context.application.create_task(
        _live_update_loop(
            context, str(user_id),
            sent.chat_id, sent.message_id,
            timeout=60.0,
        )
    )


# ---------------------------------------------------------------------------
# Callback query handler (button presses)
# ---------------------------------------------------------------------------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    action = query.data
    logger.info(f"Callback: user={user_id} action={action}")

    # Ensure session & streamer alive
    agy.start_for_user(str(user_id))
    ensure_streamer(str(user_id), context.application)

    if action.startswith("key_"):
        # e.g. "key_Up", "key_ctrl_c", "key_Enter"
        key_name = action[4:]  # strip "key_"
        send_tmux_key(user_id, key_name)
        await asyncio.sleep(0.2)
        await render_screen_to_message(
            context, query.message.chat_id, query.message.message_id,
            str(user_id)
        )

    elif action == "ctrl_interrupt":
        agy.sm.interrupt(str(user_id))
        await asyncio.sleep(0.3)
        await render_screen_to_message(
            context, query.message.chat_id, query.message.message_id,
            str(user_id)
        )

    elif action == "ctrl_refresh":
        # Force a tmux capture into screen buffer then re-render
        raw = agy.read(str(user_id), lines=50)
        _screen_buffer[str(user_id)] = strip_ansi(raw)
        await render_screen_to_message(
            context, query.message.chat_id, query.message.message_id,
            str(user_id)
        )

    elif action == "ctrl_agy":
        send_tmux_text(user_id, "agy")
        sent = await query.message.reply_text(
            "```\nLaunching agy...\n```",
            parse_mode="Markdown",
            reply_markup=get_control_keyboard(str(user_id)),
        )
        context.application.create_task(
            _live_update_loop(
                context, str(user_id),
                sent.chat_id, sent.message_id,
                timeout=90.0,
            )
        )

    elif action == "ctrl_clear":
        _screen_buffer[str(user_id)] = ""
        await render_screen_to_message(
            context, query.message.chat_id, query.message.message_id,
            str(user_id)
        )


# ---------------------------------------------------------------------------
# Bot startup / shutdown
# ---------------------------------------------------------------------------

telegram_app = None


async def run_bot_async() -> None:
    global telegram_app
    logger.info("Starting Telegram bot...")
    try:
        token = os.getenv("BOT_TOKEN") or settings.bot_token
        if not token:
            logger.warning("BOT_TOKEN not set. Telegram bot will not start.")
            return

        base_url = os.getenv("TELEGRAM_BASE_URL")
        if base_url:
            telegram_app = ApplicationBuilder().token(token).base_url(base_url).build()
        else:
            telegram_app = ApplicationBuilder().token(token).build()

        # Register commands
        telegram_app.add_handler(CommandHandler("start", start))
        telegram_app.add_handler(CommandHandler("cancel", cancel))
        telegram_app.add_handler(CommandHandler("list", list_files))
        telegram_app.add_handler(CommandHandler("download", download_file))
        telegram_app.add_handler(CommandHandler("get", download_file))
        telegram_app.add_handler(CommandHandler("clear", clear_screen))
        telegram_app.add_handler(CallbackQueryHandler(handle_callback))
        telegram_app.add_handler(
            MessageHandler(
                (filters.TEXT | filters.Document.ALL | filters.PHOTO) & (~filters.COMMAND),
                handle_message,
            )
        )

        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        logger.info("Telegram bot is running!")
    except Exception as e:
        logger.error(f"FATAL: Telegram bot failed to start: {e}", exc_info=True)


async def stop_bot_async() -> None:
    global telegram_app
    if telegram_app:
        try:
            await telegram_app.updater.stop()
            await telegram_app.stop()
            await telegram_app.shutdown()
        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}")


def main() -> None:
    token = os.getenv("BOT_TOKEN") or settings.bot_token
    if not token:
        logger.error("BOT_TOKEN not set; sleeping.")
        while True:
            time.sleep(60)

    base_url = os.getenv("TELEGRAM_BASE_URL")
    if base_url:
        app = ApplicationBuilder().token(token).base_url(base_url).build()
    else:
        app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("list", list_files))
    app.add_handler(CommandHandler("download", download_file))
    app.add_handler(CommandHandler("get", download_file))
    app.add_handler(CommandHandler("clear", clear_screen))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.Document.ALL | filters.PHOTO) & (~filters.COMMAND),
            handle_message,
        )
    )

    logger.info("Starting Telegram bot (polling)")
    try:
        app.run_polling()
    except Exception:
        logger.exception("Telegram bot crashed.")
        while True:
            time.sleep(60)


if __name__ == "__main__":
    main()
