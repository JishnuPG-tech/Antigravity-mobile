"""
OpenCode Mobile — Telegram Terminal Bot (v3, capture-pane)

ARCHITECTURE:
  - ONE persistent terminal message per user (never creates new messages per command)
  - tmux capture-pane is the ONLY display source — tmux handles all ANSI/CR/cursor
  - Single background polling loop per user: capture -> diff -> edit (100ms / 0.5s)
  - NO login / NO auth flow — OpenCode uses free models with no login required
  - Full keyboard mapping: arrows, Tab, ESC, Ctrl-C/D/Z, F1-F5, PgUp/Dn, Home/End
"""

import asyncio
import logging
import os
import re
import subprocess
import time
from datetime import datetime, timezone

from services.opencode_manager import OpencodeManager
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand,
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, MessageHandler, CallbackQueryHandler, filters,
)
from telegram.error import BadRequest, RetryAfter, NetworkError
from backend.app.config import settings

# ---------------------------------------------------------------------------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("opencode.bot")

# ---------------------------------------------------------------------------
oc = OpencodeManager()

# ---------------------------------------------------------------------------
# Per-user runtime state
# ---------------------------------------------------------------------------
_terminal_msg: dict[str, tuple[int, int]] = {}   # uid -> (chat_id, msg_id)
_last_sent:    dict[str, str]             = {}   # uid -> last text sent to Telegram
_poll_tasks:   dict[str, asyncio.Task]    = {}   # uid -> background poll task
_last_activity: dict[str, float]          = {}   # uid -> last active timestamp

def update_activity(uid: str) -> None:
    _last_activity[uid] = time.time()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
POLL_INTERVAL = 0.10    # seconds between capture-pane calls
MIN_EDIT_GAP  = 0.50    # minimum seconds between Telegram edits
CAPTURE_LINES = 40      # terminal history lines to show
MAX_MSG_CHARS = 3800    # max chars in a Telegram code block

# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------
def _parse_users() -> set[int]:
    raw = getattr(settings, "authorized_users", "") or os.getenv("AUTHORIZED_USERS", "")
    out: set[int] = set()
    for v in raw.split(","):
        v = v.strip()
        try:
            out.add(int(v))
        except ValueError:
            pass
    return out

AUTHORIZED_USERS = _parse_users()

def is_authorized(uid: int) -> bool:
    return bool(AUTHORIZED_USERS) and int(uid) in AUTHORIZED_USERS

# ---------------------------------------------------------------------------
# ANSI / terminal helpers
# ---------------------------------------------------------------------------
_RE_ANSI = re.compile(r'\x1b(?:\[[0-9;?]*[a-zA-Z]|\][^\x07\x1b]*[\x07\x1b]|.)')
_RE_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')

def strip_ansi(text: str) -> str:
    text = _RE_ANSI.sub('', text)
    text = text.replace("[?2004l", "").replace("[?2004h", "")
    text = _RE_CTRL.sub('', text)
    return text


def clean_terminal_output(text: str, keep_whitespace: bool = False) -> tuple[str, bool]:
    """Compatibility shim used by api.py WebSocket endpoint."""
    cleaned = strip_ansi(text)
    if not keep_whitespace:
        cleaned = cleaned.strip()
    return cleaned, False


def format_terminal(raw: str) -> str:
    """Convert tmux capture-pane output into a Telegram code block."""
    text = strip_ansi(raw)
    lines = [ln.rstrip() for ln in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    content = "\n".join(lines)

    if len(content) > MAX_MSG_CHARS:
        content = content[-MAX_MSG_CHARS:]
        nl = content.find("\n")
        if nl != -1:
            content = content[nl + 1:]

    if not content.strip():
        content = "(terminal output empty — type 'opencode' to launch)"

    content = content.replace("`", "\u02cb")   # replace backticks so code block doesn't break
    return "```\n" + content + "\n```"

# ---------------------------------------------------------------------------
# tmux interface
# ---------------------------------------------------------------------------
def _session(uid: str) -> str:
    return oc.sm._session_name(str(uid))


def tmux_capture(uid: str, lines: int = CAPTURE_LINES) -> str:
    """Get the current rendered terminal via tmux capture-pane (plain text, no ANSI)."""
    session = _session(uid)
    try:
        res = subprocess.run(
            ["tmux", "capture-pane", "-p", "-S", f"-{lines}", "-t", f"{session}:0.0"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3,
        )
        return res.stdout
    except FileNotFoundError:
        return "(tmux not available)"
    except subprocess.TimeoutExpired:
        return "(capture timeout)"
    except Exception as e:
        logger.warning(f"tmux_capture error: {e}")
        return ""


def tmux_send(uid: str, text: str, enter: bool = True) -> None:
    """Send text literally to the tmux pane (-l avoids tmux interpreting special chars)."""
    session = _session(uid)
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", session, "-l", text],
            capture_output=True, timeout=5,
        )
        if enter:
            subprocess.run(
                ["tmux", "send-keys", "-t", session, "Enter"],
                capture_output=True, timeout=5,
            )
    except Exception as e:
        logger.warning(f"tmux_send error: {e}")


def tmux_key(uid: str, key: str) -> None:
    """Send a named key (Up/Down/Tab/etc.) to the tmux pane."""
    KEY_MAP = {
        "Up": "Up", "Down": "Down", "Left": "Left", "Right": "Right",
        "Enter": "Enter", "Tab": "Tab", "BSpace": "BSpace", "Escape": "Escape",
        "ctrl_c": "C-c", "ctrl_d": "C-d", "ctrl_z": "C-z",
        "F1": "F1", "F2": "F2", "F3": "F3", "F4": "F4", "F5": "F5",
        "PPage": "PPage", "NPage": "NPage", "Home": "Home", "End": "End",
    }
    k = KEY_MAP.get(key, key)
    session = _session(uid)
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", session, k],
            capture_output=True, timeout=5,
        )
    except Exception as e:
        logger.warning(f"tmux_key {key} error: {e}")


def tmux_interrupt(uid: str) -> None:
    session = _session(uid)
    try:
        subprocess.run(["tmux", "send-keys", "-t", session, "C-c"],
                       capture_output=True, timeout=5)
    except Exception as e:
        logger.warning(f"tmux_interrupt error: {e}")


def tmux_resize(uid: str, cols: int = 88, rows: int = 35) -> None:
    session = _session(uid)
    try:
        subprocess.run(
            ["tmux", "resize-window", "-t", session, "-x", str(cols), "-y", str(rows)],
            capture_output=True, timeout=3,
        )
    except Exception:
        pass


def is_tmux_running_cmd(uid: str) -> bool:
    """Return True if the pane is running something other than bash (e.g. opencode)."""
    session = _session(uid)
    try:
        res = subprocess.run(
            ["tmux", "display-message", "-p", "-t", f"{session}:0.0",
             "-F", "#{pane_current_command}"],
            capture_output=True, text=True, timeout=2,
        )
        cmd = res.stdout.strip()
        return cmd not in ("", "bash", "sh")
    except Exception:
        return False


def tmux_clear(uid: str) -> None:
    session = _session(uid)
    try:
        subprocess.run(["tmux", "send-keys", "-t", session, "C-l"],
                       capture_output=True, timeout=2)
        subprocess.run(["tmux", "clear-history", "-t", session],
                       capture_output=True, timeout=2)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Safe Telegram edit
# ---------------------------------------------------------------------------
async def _edit(context, chat_id: int, msg_id: int,
                text: str, markup: InlineKeyboardMarkup = None,
                parse_mode: str = "Markdown") -> bool:
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=msg_id,
            text=text, parse_mode=parse_mode,
            reply_markup=markup,
        )
        return True
    except BadRequest as e:
        err = str(e).lower()
        if "not modified" in err or "message to edit not found" in err:
            return False
        logger.debug(f"edit BadRequest: {e}")
        return False
    except RetryAfter as e:
        logger.warning(f"Telegram rate limit: sleeping {e.retry_after}s")
        await asyncio.sleep(e.retry_after + 0.5)
        return False
    except NetworkError as e:
        logger.warning(f"NetworkError: {e}")
        return False
    except Exception as e:
        logger.debug(f"edit unexpected: {e}")
        return False

# ---------------------------------------------------------------------------
# Core polling loop — one per user, runs forever
# ---------------------------------------------------------------------------
async def _poll_loop(uid: str, context) -> None:
    """
    Continuously captures the tmux screen and updates the Telegram terminal message.
    - Poll every 100ms via tmux capture-pane
    - Edit Telegram only when content changed AND 500ms since last edit
    - Resetting _last_sent[uid] = "" from a callback forces immediate refresh
    """
    logger.info(f"[Poll] Started for user {uid}")
    update_activity(uid)
    last_edit_time = 0.0
    if uid not in _last_sent:
        _last_sent[uid] = ""

    try:
        while True:
            await asyncio.sleep(POLL_INTERVAL)

            # Check if idle for > 5 minutes (300 seconds)
            if time.time() - _last_activity.get(uid, 0.0) > 300:
                logger.info(f"[Poll] Stopping idle poller for user {uid}")
                if uid in _terminal_msg:
                    chat_id, msg_id = _terminal_msg[uid]
                    raw = tmux_capture(uid, lines=CAPTURE_LINES)
                    text = format_terminal(raw)
                    sleep_msg = text + "\n\n*(Terminal session paused due to inactivity. Send any message to wake it up!)*"
                    await _edit(context, chat_id, msg_id, sleep_msg, None)
                break

            if uid not in _terminal_msg:
                continue
            chat_id, msg_id = _terminal_msg[uid]

            # Get current terminal state from tmux (full terminal emulation done by tmux)
            raw = tmux_capture(uid, lines=CAPTURE_LINES)
            text = format_terminal(raw)
            markup = None

            now = time.monotonic()
            changed = (text != _last_sent.get(uid, ""))
            time_ok = (now - last_edit_time) >= MIN_EDIT_GAP

            if changed and time_ok:
                await _edit(context, chat_id, msg_id, text, markup)
                _last_sent[uid] = text
                last_edit_time = now

    except asyncio.CancelledError:
        logger.info(f"[Poll] Stopped for user {uid}")
    except Exception as e:
        logger.error(f"[Poll] Error for user {uid}: {e}", exc_info=True)


def ensure_poll_loop(uid: str, context) -> None:
    task = _poll_tasks.get(uid)
    if task is None or task.done():
        _poll_tasks[uid] = context.application.create_task(_poll_loop(uid, context))
        logger.debug(f"[Poll] Spawned for {uid}")

# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    update_activity(uid)
    name = update.effective_user.first_name or "User"

    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    # Create/ensure tmux session
    oc.start_for_user(uid)
    tmux_resize(uid, cols=88, rows=35)

    # Send the one persistent terminal message
    sent = await update.message.reply_text(
        f"*OpenCode Terminal — {name}*\n\nConnecting...",
        parse_mode="Markdown",
        reply_markup=None,
    )
    _terminal_msg[uid] = (sent.chat_id, sent.message_id)
    _last_sent[uid] = ""

    # Only launch opencode if not already running
    if not is_tmux_running_cmd(uid):
        tmux_send(uid, "opencode")

    ensure_poll_loop(uid, context)

# ---------------------------------------------------------------------------
# /status
# ---------------------------------------------------------------------------
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    name  = update.effective_user.first_name or "User"
    alive = uid in _poll_tasks and not _poll_tasks[uid].done()
    has_t = uid in _terminal_msg
    cmd   = ""
    try:
        session = _session(uid)
        res = subprocess.run(
            ["tmux", "display-message", "-p", "-t", f"{session}:0.0", "-F",
             "#{pane_current_command}"],
            capture_output=True, text=True, timeout=2,
        )
        cmd = res.stdout.strip()
    except Exception:
        pass

    await update.message.reply_text(
        f"*OpenCode — Session Status*\n\n"
        f"User: `{name}`\n"
        f"Poller: {'running' if alive else 'stopped'}\n"
        f"Terminal msg: {'active' if has_t else 'none'}\n"
        f"Running: `{cmd or 'bash'}`\n\n"
        f"/start  /cancel  /clear  /list  /download",
        parse_mode="Markdown",
    )

# ---------------------------------------------------------------------------
# /cancel
# ---------------------------------------------------------------------------
async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    update_activity(uid)
    if not is_authorized(update.effective_user.id):
        return
    tmux_interrupt(uid)
    await update.message.reply_text("Ctrl-C sent.")

# ---------------------------------------------------------------------------
# /clear
# ---------------------------------------------------------------------------
async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    update_activity(uid)
    if not is_authorized(update.effective_user.id):
        return
    tmux_clear(uid)
    _last_sent[uid] = ""
    await update.message.reply_text("Screen cleared.")

# ---------------------------------------------------------------------------
# /run
# ---------------------------------------------------------------------------
async def cmd_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    update_activity(uid)
    if not is_authorized(update.effective_user.id):
        return
    cmd = " ".join(context.args) if context.args else "opencode"
    oc.start_for_user(uid)
    ensure_poll_loop(uid, context)
    tmux_send(uid, cmd)
    _last_sent[uid] = ""
    if uid not in _terminal_msg:
        sent = await update.message.reply_text("```\n...\n```",
                                                parse_mode="Markdown",
                                                reply_markup=None)
        _terminal_msg[uid] = (sent.chat_id, sent.message_id)

# ---------------------------------------------------------------------------
# /list
# ---------------------------------------------------------------------------
async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    ws = os.path.join(oc.sm.workspace_root, f"user_{uid}", "default")
    os.makedirs(ws, exist_ok=True)
    try:
        files = sorted(f for f in os.listdir(ws)
                       if os.path.isfile(os.path.join(ws, f)) and not f.startswith("."))
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return

    if not files:
        await update.message.reply_text("Workspace is empty.")
        return

    lines = "\n".join(f"• `{f}`" for f in files)
    await update.message.reply_text(
        f"*Workspace Files ({len(files)}):*\n\n{lines}\n\n"
        f"Use `/download <filename>` to retrieve.",
        parse_mode="Markdown",
    )

# ---------------------------------------------------------------------------
# /download
# ---------------------------------------------------------------------------
async def cmd_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    update_activity(uid)
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: `/download <filename>`", parse_mode="Markdown")
        return

    filename = os.path.basename(" ".join(context.args))
    ws = os.path.join(oc.sm.workspace_root, f"user_{uid}", "default")
    path = os.path.join(ws, filename)

    if not os.path.exists(path):
        await update.message.reply_text(f"`{filename}` not found.", parse_mode="Markdown")
        return

    await update.message.reply_text(f"Uploading `{filename}`...", parse_mode="Markdown")
    try:
        with open(path, "rb") as f:
            await update.message.reply_document(document=f, filename=filename)
    except Exception as e:
        await update.message.reply_text(f"Upload failed: {e}")

# ---------------------------------------------------------------------------
# Message handler
# ---------------------------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    update_activity(uid)
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    ws = os.path.join(oc.sm.workspace_root, f"user_{uid}", "default")
    os.makedirs(ws, exist_ok=True)

    # File upload
    if update.message.document:
        doc = update.message.document
        fn  = doc.file_name
        msg = await update.message.reply_text(f"Saving `{fn}`...", parse_mode="Markdown")
        try:
            f = await context.bot.get_file(doc.file_id)
            await f.download_to_drive(os.path.join(ws, fn))
            await msg.edit_text(f"Saved `{fn}` to workspace.", parse_mode="Markdown")
        except Exception as e:
            await msg.edit_text(f"Error: {e}")
        return

    if update.message.photo:
        photo = update.message.photo[-1]
        fn = f"photo_{int(time.time())}.jpg"
        msg = await update.message.reply_text("Saving image...")
        try:
            f = await context.bot.get_file(photo.file_id)
            await f.download_to_drive(os.path.join(ws, fn))
            await msg.edit_text(f"Saved as `{fn}`.", parse_mode="Markdown")
        except Exception as e:
            await msg.edit_text(f"Error: {e}")
        return

    # Text input — send to tmux
    text = (update.message.text or "").strip()
    if not text:
        return

    oc.start_for_user(uid)
    ensure_poll_loop(uid, context)
    tmux_send(uid, text, enter=True)
    _last_sent[uid] = ""

    # Create a terminal message if none exists
    if uid not in _terminal_msg:
        sent = await update.message.reply_text(
            "```\n...\n```", parse_mode="Markdown", reply_markup=None
        )
        _terminal_msg[uid] = (sent.chat_id, sent.message_id)

# ---------------------------------------------------------------------------
# Callback handler
# ---------------------------------------------------------------------------
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        return

    action  = query.data
    chat_id = query.message.chat_id
    msg_id  = query.message.message_id

    logger.debug(f"[CB] {uid} -> {action}")

    oc.start_for_user(uid)
    ensure_poll_loop(uid, context)
    _terminal_msg[uid] = (chat_id, msg_id)

    if action.startswith("key_"):
        tmux_key(uid, action[4:])
        _last_sent[uid] = ""   # force immediate refresh on next poll

    elif action == "ctrl_interrupt":
        tmux_interrupt(uid)
        _last_sent[uid] = ""

    elif action == "ctrl_refresh":
        _last_sent[uid] = ""
        raw  = tmux_capture(uid, lines=CAPTURE_LINES)
        text = format_terminal(raw)
        await _edit(context, chat_id, msg_id, text, None)

    elif action == "ctrl_launch":
        if not is_tmux_running_cmd(uid):
            tmux_send(uid, "opencode")
        _last_sent[uid] = ""

    elif action == "ctrl_clear":
        tmux_clear(uid)
        _last_sent[uid] = ""
        await _edit(context, chat_id, msg_id,
                    "```\n(screen cleared)\n```", None)

# ---------------------------------------------------------------------------
# Bot registration
# ---------------------------------------------------------------------------
BOT_COMMANDS = [
    BotCommand("start",    "Connect & launch OpenCode terminal"),
    BotCommand("status",   "Show session status"),
    BotCommand("run",      "Run a shell command"),
    BotCommand("cancel",   "Send Ctrl-C to terminal"),
    BotCommand("clear",    "Clear terminal screen"),
    BotCommand("list",     "List workspace files"),
    BotCommand("download", "Download file from workspace"),
]


def _register(app) -> None:
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("status",   cmd_status))
    app.add_handler(CommandHandler("run",      cmd_run))
    app.add_handler(CommandHandler("cancel",   cmd_cancel))
    app.add_handler(CommandHandler("clear",    cmd_clear))
    app.add_handler(CommandHandler("list",     cmd_list))
    app.add_handler(CommandHandler("download", cmd_download))
    app.add_handler(CommandHandler("get",      cmd_download))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.Document.ALL | filters.PHOTO) & (~filters.COMMAND),
            handle_message,
        )
    )

# ---------------------------------------------------------------------------
# FastAPI async integration
# ---------------------------------------------------------------------------
telegram_app = None


async def run_bot_async() -> None:
    global telegram_app
    logger.info("Starting OpenCode Telegram Bot...")
    try:
        token = os.getenv("BOT_TOKEN") or getattr(settings, "bot_token", None)
        if not token:
            logger.warning("BOT_TOKEN not set — bot will not start.")
            return

        base_url = os.getenv("TELEGRAM_BASE_URL")
        builder = ApplicationBuilder().token(token)
        if base_url:
            builder = builder.base_url(base_url)

        telegram_app = builder.build()
        _register(telegram_app)

        await telegram_app.initialize()
        try:
            await telegram_app.bot.set_my_commands(BOT_COMMANDS)
        except Exception:
            pass
        await telegram_app.start()
        
        public_url = os.getenv("RENDER_EXTERNAL_URL")
        if public_url:
            webhook_url = f"{public_url.rstrip('/')}/api/telegram-webhook"
            logger.info(f"Setting Telegram webhook to: {webhook_url}")
            await telegram_app.bot.set_webhook(
                url=webhook_url,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )
        else:
            logger.info("No RENDER_EXTERNAL_URL found — starting polling mode.")
            await telegram_app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )
        logger.info("OpenCode Bot is running!")
    except Exception as e:
        logger.error(f"FATAL: {e}", exc_info=True)


async def stop_bot_async() -> None:
    global telegram_app
    if telegram_app:
        logger.info("Stopping OpenCode Bot...")
        try:
            if telegram_app.updater and telegram_app.updater.running:
                await telegram_app.updater.stop()
            await telegram_app.stop()
            await telegram_app.shutdown()
        except Exception as e:
            logger.error(f"Shutdown error: {e}")


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------
def main() -> None:
    import asyncio as _aio

    async def _run():
        token = os.getenv("BOT_TOKEN") or getattr(settings, "bot_token", None)
        if not token:
            logger.error("BOT_TOKEN not set.")
            return
        base_url = os.getenv("TELEGRAM_BASE_URL")
        builder = ApplicationBuilder().token(token)
        if base_url:
            builder = builder.base_url(base_url)
        app = builder.build()
        _register(app)
        try:
            await app.bot.set_my_commands(BOT_COMMANDS)
        except Exception:
            pass
        logger.info("Starting bot (standalone)...")
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

    _aio.run(_run())


if __name__ == "__main__":
    main()
