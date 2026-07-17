"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         ANTIGRAVITY  —  Telegram Terminal Bot  (v3 — Capture-Pane)         ║
║                                                                              ║
║  ARCHITECTURE (v3):                                                          ║
║  ─────────────────                                                           ║
║  • ONE persistent terminal message per user (no new message per command)    ║
║  • tmux capture-pane is the ONLY display source — no virtual buffer,        ║
║    no ANSI emulation, no log files. tmux IS the terminal emulator.          ║
║  • Single background polling loop per user: capture → diff → edit           ║
║  • Poll every 100ms, edit Telegram only when content changed (max 1/sec)    ║
║  • Auth state persisted in SQLite, survives restarts                        ║
║  • Full keyboard: arrows, Tab, ESC, Ctrl-C/D/Z, F1-F5, PgUp/Dn, Home/End  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
import os
import re
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone

from services.antigravity_manager import AntigravityManager
from core.state_store import (
    get_auth_state, is_authenticated,
    set_auth_state, set_auth_url, get_auth_url,
    clear_auth_url, mark_authenticated, mark_logged_out,
    get_state,
)
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand,
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, MessageHandler, CallbackQueryHandler, filters,
)
from telegram.error import BadRequest, RetryAfter, NetworkError
from backend.app.config import settings

# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("agy.bot")

# ─────────────────────────────────────────────────────────────────────────────
agy = AntigravityManager()

# ─────────────────────────────────────────────────────────────────────────────
# Per-user runtime state
# ─────────────────────────────────────────────────────────────────────────────

# (chat_id, message_id) of the one persistent terminal message per user
_terminal_msg: dict[str, tuple[int, int]] = {}

# The last text we edited into the Telegram terminal message
_last_sent: dict[str, str] = {}

# Background polling task per user
_poll_tasks: dict[str, asyncio.Task] = {}

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

POLL_INTERVAL  = 0.10   # seconds between tmux capture-pane calls
MIN_EDIT_GAP   = 0.50   # minimum seconds between Telegram edits (rate limit)
CAPTURE_LINES  = 40     # lines of terminal history to capture
MAX_MSG_CHARS  = 3800   # Telegram code block limit

# ─────────────────────────────────────────────────────────────────────────────
# Authorization
# ─────────────────────────────────────────────────────────────────────────────

def _parse_users() -> set[int]:
    raw = settings.authorized_users or os.getenv("AUTHORIZED_USERS", "")
    out: set[int] = set()
    for v in [x.strip() for x in raw.split(",") if x.strip()]:
        try:
            out.add(int(v))
        except ValueError:
            pass
    return out

AUTHORIZED_USERS = _parse_users()

def is_authorized(uid: int) -> bool:
    return bool(AUTHORIZED_USERS) and int(uid) in AUTHORIZED_USERS

# ─────────────────────────────────────────────────────────────────────────────
# Pattern helpers
# ─────────────────────────────────────────────────────────────────────────────

_RE_ANSI  = re.compile(r'\x1b(?:\[[0-9;?]*[a-zA-Z]|\][^\x07\x1b]*[\x07\x1b]|.)')
_RE_CTRL  = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_RE_GURL  = re.compile(
    r'https://accounts\.google\.com/o/oauth2/(?:v2/)?auth\?[a-zA-Z0-9_.~\-=+%&]+'
)
_RE_CODE  = re.compile(
    r'^(4/[0-9A-Za-z_\-]{10,}|ya29\.[0-9A-Za-z_\-\.]{10,}|1//[0-9A-Za-z_\-]{10,})$'
)
_RE_DCODE = re.compile(r'^[A-Z0-9]{4}-[A-Z0-9]{4}$')

_CODE_PROMPTS = [
    "enter the authorization code", "enter authorization code",
    "enter code", "paste the code", "paste code",
    "verification code", "auth code",
]
_SUCCESS_KW = [
    "you are now logged in", "login successful", "authenticated successfully",
    "logged in as", "credentials saved", "token saved", "authorized",
    "authorization complete",
]


def strip_ansi(text: str) -> str:
    text = _RE_ANSI.sub('', text)
    text = text.replace("[?2004l", "").replace("[?2004h", "")
    text = _RE_CTRL.sub('', text)
    return text


def detect_google_url(text: str) -> str | None:
    m = _RE_GURL.search(text)
    if not m:
        return None
    url = m.group(0)
    url = re.split(r'[\s\x1b\'\"\\]', url)[0].rstrip('];\\,')
    return url if len(url) > 50 else None


def is_auth_code(text: str) -> bool:
    t = text.strip()
    return bool(_RE_CODE.match(t)) or bool(_RE_DCODE.match(t))


def has_code_prompt(text: str) -> bool:
    low = text.lower()
    return any(kw in low for kw in _CODE_PROMPTS)


def has_success(text: str) -> bool:
    low = text.lower()
    return any(kw in low for kw in _SUCCESS_KW)


# ─────────────────────────────────────────────────────────────────────────────
# tmux interface
# ─────────────────────────────────────────────────────────────────────────────

def _session(uid: str) -> str:
    return agy.sm._session_name(str(uid))


def tmux_capture(uid: str, lines: int = CAPTURE_LINES) -> str:
    """
    Get the CURRENT rendered terminal screen via tmux capture-pane.
    This is the only correct way to get terminal output — tmux already
    handles all ANSI, CR, backspace, cursor movement internally.
    Returns plain text (no ANSI codes when -e is omitted).
    """
    session = _session(uid)
    try:
        res = subprocess.run(
            ["tmux", "capture-pane", "-p", "-S", f"-{lines}",
             "-t", f"{session}:0.0"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=3,
        )
        return res.stdout
    except FileNotFoundError:
        return "(tmux not available)"
    except subprocess.TimeoutExpired:
        return "(capture timeout)"
    except Exception as e:
        logger.warning(f"tmux_capture: {e}")
        return ""


def tmux_send(uid: str, text: str, enter: bool = True) -> None:
    """Send text literally to tmux (-l avoids tmux interpreting special chars)."""
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
        logger.warning(f"tmux_send: {e}")


def tmux_key(uid: str, key: str) -> None:
    session = _session(uid)
    key_map = {
        "Up": "Up", "Down": "Down", "Left": "Left", "Right": "Right",
        "Enter": "Enter", "Tab": "Tab", "BSpace": "BSpace", "Escape": "Escape",
        "ctrl_c": "C-c", "ctrl_d": "C-d", "ctrl_z": "C-z",
        "F1": "F1", "F2": "F2", "F3": "F3", "F4": "F4", "F5": "F5",
        "PPage": "PPage", "NPage": "NPage", "Home": "Home", "End": "End",
    }
    k = key_map.get(key, key)
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", session, k],
            capture_output=True, timeout=5,
        )
    except Exception as e:
        logger.warning(f"tmux_key {key}: {e}")


def tmux_interrupt(uid: str) -> None:
    session = _session(uid)
    try:
        subprocess.run(["tmux", "send-keys", "-t", session, "C-c"],
                       capture_output=True, timeout=5)
    except Exception as e:
        logger.warning(f"tmux_interrupt: {e}")


def tmux_resize(uid: str, cols: int = 88, rows: int = 35) -> None:
    """Resize tmux window to fit nicely in Telegram code block."""
    session = _session(uid)
    try:
        subprocess.run(
            ["tmux", "resize-window", "-t", session, "-x", str(cols), "-y", str(rows)],
            capture_output=True, timeout=3,
        )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Keyboards
# ─────────────────────────────────────────────────────────────────────────────

def kb_terminal(uid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↑", callback_data="key_Up")],
        [
            InlineKeyboardButton("←",        callback_data="key_Left"),
            InlineKeyboardButton("↵ Enter",  callback_data="key_Enter"),
            InlineKeyboardButton("→",        callback_data="key_Right"),
        ],
        [
            InlineKeyboardButton("↓",        callback_data="key_Down"),
            InlineKeyboardButton("⇥ Tab",    callback_data="key_Tab"),
            InlineKeyboardButton("⌫ BS",     callback_data="key_BSpace"),
        ],
        [
            InlineKeyboardButton("ESC",      callback_data="key_Escape"),
            InlineKeyboardButton("^C",       callback_data="key_ctrl_c"),
            InlineKeyboardButton("^D",       callback_data="key_ctrl_d"),
            InlineKeyboardButton("^Z",       callback_data="key_ctrl_z"),
        ],
        [
            InlineKeyboardButton("F1",  callback_data="key_F1"),
            InlineKeyboardButton("F2",  callback_data="key_F2"),
            InlineKeyboardButton("F3",  callback_data="key_F3"),
            InlineKeyboardButton("F4",  callback_data="key_F4"),
            InlineKeyboardButton("F5",  callback_data="key_F5"),
        ],
        [
            InlineKeyboardButton("⇞ PgUp", callback_data="key_PPage"),
            InlineKeyboardButton("⇟ PgDn", callback_data="key_NPage"),
            InlineKeyboardButton("⇤ Home",  callback_data="key_Home"),
            InlineKeyboardButton("End ⇥",   callback_data="key_End"),
        ],
        [
            InlineKeyboardButton("🚀 Launch agy",  callback_data="ctrl_agy"),
            InlineKeyboardButton("🔄 Refresh",     callback_data="ctrl_refresh"),
        ],
        [
            InlineKeyboardButton("🛑 Stop (^C)",   callback_data="ctrl_interrupt"),
            InlineKeyboardButton("🔴 Logout",      callback_data="ctrl_logout"),
        ],
    ])


def kb_auth(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Authorize with Google  ↗", url=url)],
        [
            InlineKeyboardButton("🔄 Refresh",         callback_data="ctrl_refresh"),
            InlineKeyboardButton("🛑 Cancel",           callback_data="ctrl_interrupt"),
        ],
    ])


def kb_verifying() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Check Status",  callback_data="ctrl_refresh")],
        [InlineKeyboardButton("🛑 Cancel",         callback_data="ctrl_interrupt")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Core: format terminal content for Telegram
# ─────────────────────────────────────────────────────────────────────────────

def format_terminal(raw: str) -> str:
    """
    Convert tmux capture-pane output to Telegram code block.
    capture-pane without -e returns plain text (no ANSI), but may have
    some control artifacts — clean those and trim to fit Telegram limits.
    """
    # Strip any stray ANSI that slipped through (rare but possible)
    text = strip_ansi(raw)
    # Remove trailing whitespace on each line (tmux pads lines to terminal width)
    lines = [ln.rstrip() for ln in text.splitlines()]
    # Drop leading blank lines
    while lines and not lines[0].strip():
        lines.pop(0)
    # Drop trailing blank lines
    while lines and not lines[-1].strip():
        lines.pop()

    content = "\n".join(lines)

    # Trim to fit in Telegram code block
    if len(content) > MAX_MSG_CHARS:
        # Keep the LAST MAX_MSG_CHARS chars, cut at newline
        content = content[-MAX_MSG_CHARS:]
        nl = content.find("\n")
        if nl != -1:
            content = content[nl + 1:]

    if not content.strip():
        content = "(terminal output empty)"

    # Escape backticks inside the code block
    content = content.replace("`", "\u02cb")
    return "```\n" + content + "\n```"


# ─────────────────────────────────────────────────────────────────────────────
# Telegram message editing (with error handling)
# ─────────────────────────────────────────────────────────────────────────────

async def _edit(context, chat_id: int, msg_id: int,
                text: str, markup: InlineKeyboardMarkup,
                parse_mode: str = "Markdown") -> bool:
    """Edit a Telegram message. Returns True on success."""
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=msg_id,
            text=text, parse_mode=parse_mode,
            reply_markup=markup,
        )
        return True
    except BadRequest as e:
        err = str(e).lower()
        if "not modified" in err:
            return False   # content unchanged — not an error
        if "message to edit not found" in err:
            logger.warning(f"Terminal message {msg_id} deleted by user")
            return False
        logger.debug(f"edit BadRequest: {e}")
        return False
    except RetryAfter as e:
        logger.warning(f"Telegram rate limit — sleeping {e.retry_after}s")
        await asyncio.sleep(e.retry_after + 0.5)
        return False
    except NetworkError as e:
        logger.warning(f"NetworkError editing message: {e}")
        return False
    except Exception as e:
        logger.debug(f"edit unexpected: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Auth state management helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _handle_auth_detection(uid: str, screen_text: str) -> str | None:
    """
    Scan captured terminal output for Google OAuth URL.
    Update auth state in DB. Return URL if found, else None.
    """
    url = detect_google_url(screen_text)
    if url:
        auth_st = await get_auth_state(uid)
        if auth_st not in ("authenticated", "code_sent"):
            await set_auth_url(uid, url)
            if auth_st != "url_shown":
                await set_auth_state(uid, "url_shown")
                logger.info(f"[Auth] Google URL found for {uid}")
    return url


async def _check_auth_complete(uid: str, screen_text: str) -> bool:
    """
    After code was sent (code_sent state), check if auth is now complete.
    Auth is complete when: URL is gone AND no code prompt visible.
    """
    auth_st = await get_auth_state(uid)
    if auth_st not in ("code_sent",):
        return False

    url_gone    = detect_google_url(screen_text) is None
    prompt_gone = not has_code_prompt(screen_text[-500:])
    success     = has_success(screen_text[-500:])

    if success or (url_gone and prompt_gone):
        await mark_authenticated(uid)
        logger.info(f"[Auth] User {uid} authenticated (url_gone={url_gone}, kw={success})")
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# The core polling loop — one per user, runs forever
# ─────────────────────────────────────────────────────────────────────────────

async def _poll_loop(uid: str, context) -> None:
    """
    Continuously poll tmux capture-pane and update the user's terminal message.

    This is the heart of the streaming system:
      1. Call tmux capture-pane every POLL_INTERVAL (100ms)
      2. Compare with last sent content
      3. If changed AND enough time since last edit → edit Telegram message
      4. Handle auth state transitions inline
    """
    logger.info(f"[Poll] Started for user {uid}")
    last_edit_time = 0.0
    last_content = ""

    try:
        while True:
            await asyncio.sleep(POLL_INTERVAL)

            # --- Check if we have a terminal message to update ---
            if uid not in _terminal_msg:
                continue
            chat_id, msg_id = _terminal_msg[uid]

            # --- Capture current terminal state (tmux is the emulator) ---
            raw = tmux_capture(uid, lines=CAPTURE_LINES)

            # --- Auth URL detection ---
            auth_st = await get_auth_state(uid)
            url = await _handle_auth_detection(uid, raw)
            auth_st = await get_auth_state(uid)  # refresh after possible update

            # --- Auth completion check ---
            if auth_st == "code_sent":
                just_authed = await _check_auth_complete(uid, raw)
                if just_authed:
                    auth_st = "authenticated"

            # --- Build message content based on auth state ---
            if auth_st == "url_shown" and url:
                # Show login button
                text = (
                    "🔑 *Antigravity — Authorization Required*\n\n"
                    "1\\. Tap *Authorize with Google* below\n"
                    "2\\. Complete sign\\-in in your browser\n"
                    "3\\. Copy the authorization code\n"
                    "4\\. *Paste it here* — it will be sent to the CLI automatically"
                )
                markup = kb_auth(url)
                parse_mode = "MarkdownV2"
                new_content = f"AUTH:{url}"   # sentinel for change detection
            elif auth_st == "code_sent":
                text = (
                    "⏳ *Verifying authorization code\\.\\.\\.*\n\n"
                    "Confirming with Google — please wait\\.\n"
                    "Tap *Check Status* if this takes more than 10 seconds\\."
                )
                markup = kb_verifying()
                parse_mode = "MarkdownV2"
                new_content = "VERIFYING"
            else:
                # Normal terminal output
                text = format_terminal(raw)
                markup = kb_terminal(uid)
                parse_mode = "Markdown"
                new_content = text

            # --- Rate-limited edit ---
            now = time.monotonic()
            content_changed = (new_content != last_content)
            time_ok = (now - last_edit_time) >= MIN_EDIT_GAP

            if content_changed and time_ok:
                ok = await _edit(context, chat_id, msg_id, text, markup, parse_mode)
                if ok:
                    last_content = new_content
                    last_edit_time = now

    except asyncio.CancelledError:
        logger.info(f"[Poll] Stopped for user {uid}")
    except Exception as e:
        logger.error(f"[Poll] Error for user {uid}: {e}", exc_info=True)


def ensure_poll_loop(uid: str, context) -> None:
    """Ensure a single persistent poll loop runs for this user."""
    task = _poll_tasks.get(uid)
    if task is None or task.done():
        _poll_tasks[uid] = context.application.create_task(_poll_loop(uid, context))
        logger.debug(f"[Poll] Spawned for {uid}")


# ─────────────────────────────────────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = update.effective_user.first_name or "User"

    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return

    # Ensure tmux session
    agy.start_for_user(uid)
    # Resize terminal window to fit Telegram nicely
    tmux_resize(uid, cols=88, rows=35)

    # Get auth state from DB
    auth_st = await get_auth_state(uid)

    # Create/replace the persistent terminal message
    initial_text = (
        f"✅ *Welcome back, {name}\\!* Connecting\\.\\.\\."
        if auth_st == "authenticated"
        else "🚀 *Antigravity CLI starting\\.\\.\\.*"
    )

    sent = await update.message.reply_text(
        initial_text,
        parse_mode="MarkdownV2",
        reply_markup=kb_terminal(uid),
    )

    # Store as the terminal message for this user
    _terminal_msg[uid] = (sent.chat_id, sent.message_id)
    _last_sent[uid] = ""

    # Launch agy
    tmux_send(uid, "agy")

    # Start (or restart) the polling loop
    ensure_poll_loop(uid, context)


# ─────────────────────────────────────────────────────────────────────────────
# /status
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    s = await get_state(uid)
    auth_st = s.get("auth_state", "none")
    name = update.effective_user.first_name or "User"

    if auth_st == "authenticated":
        ts = s.get("logged_in_at")
        since = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else "unknown"
        status = f"🟢 Authenticated since {since}"
    else:
        status = "🔴 Not authenticated"

    poller_alive = uid in _poll_tasks and not _poll_tasks[uid].done()
    has_terminal = uid in _terminal_msg

    await update.message.reply_text(
        f"*Antigravity — Session Status*\n\n"
        f"👤 `{name}`\n"
        f"{status}\n"
        f"📡 Poller: {'running' if poller_alive else 'stopped'}\n"
        f"🖥 Terminal: {'active' if has_terminal else 'none'}\n\n"
        f"Commands: /start /logout /cancel /clear /list /download",
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────────────────────────────────────
# /logout
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    await mark_logged_out(uid)
    tmux_send(uid, "agy logout")

    # Clear terminal message tracking
    _terminal_msg.pop(uid, None)
    _last_sent.pop(uid, None)

    await update.message.reply_text(
        "🔴 *Logged out.*\n\nSession ended. Use /start to reconnect.",
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────────────────────────────────────
# /cancel
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        return
    tmux_interrupt(uid)
    await update.message.reply_text("🛑 Ctrl-C sent.")


# ─────────────────────────────────────────────────────────────────────────────
# /clear
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        return
    # Force next poll to update
    _last_sent[uid] = ""
    await update.message.reply_text("🗑 Screen buffer reset — refreshing terminal…")


# ─────────────────────────────────────────────────────────────────────────────
# /list
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    ws = os.path.join(agy.sm.workspace_root, f"user_{uid}", "default")
    os.makedirs(ws, exist_ok=True)
    try:
        files = sorted(f for f in os.listdir(ws)
                       if os.path.isfile(os.path.join(ws, f)) and not f.startswith("."))
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")
        return

    if not files:
        await update.message.reply_text("📁 Workspace is empty.")
        return

    lines = "\n".join(f"• `{f}`" for f in files)
    await update.message.reply_text(
        f"📁 *Workspace Files ({len(files)}):*\n\n{lines}\n\n"
        f"Use `/download <filename>` to retrieve.",
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────────────────────────────────────
# /download
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: `/download <filename>`", parse_mode="Markdown")
        return

    filename = os.path.basename(" ".join(context.args))
    ws = os.path.join(agy.sm.workspace_root, f"user_{uid}", "default")
    path = os.path.join(ws, filename)

    if not os.path.exists(path):
        await update.message.reply_text(f"❌ `{filename}` not found.", parse_mode="Markdown")
        return

    await update.message.reply_text(f"📤 Uploading `{filename}`...", parse_mode="Markdown")
    try:
        with open(path, "rb") as f:
            await update.message.reply_document(document=f, filename=filename)
    except Exception as e:
        await update.message.reply_text(f"❌ Upload failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Main message handler
# ─────────────────────────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    ws = os.path.join(agy.sm.workspace_root, f"user_{uid}", "default")
    os.makedirs(ws, exist_ok=True)

    # ── File upload ───────────────────────────────────────────────────────────
    if update.message.document:
        doc = update.message.document
        fn = doc.file_name
        msg = await update.message.reply_text(f"📥 Saving `{fn}`...", parse_mode="Markdown")
        try:
            f = await context.bot.get_file(doc.file_id)
            await f.download_to_drive(os.path.join(ws, fn))
            await msg.edit_text(f"✅ Saved `{fn}` to workspace.", parse_mode="Markdown")
        except Exception as e:
            await msg.edit_text(f"❌ {e}")
        return

    if update.message.photo:
        photo = update.message.photo[-1]
        fn = f"photo_{int(time.time())}.jpg"
        msg = await update.message.reply_text("📸 Saving image...")
        try:
            f = await context.bot.get_file(photo.file_id)
            await f.download_to_drive(os.path.join(ws, fn))
            await msg.edit_text(f"✅ Saved as `{fn}`.", parse_mode="Markdown")
        except Exception as e:
            await msg.edit_text(f"❌ {e}")
        return

    # ── Text input ────────────────────────────────────────────────────────────
    text = (update.message.text or "").strip()
    if not text:
        return

    # Ensure session alive and polling
    agy.start_for_user(uid)
    ensure_poll_loop(uid, context)

    auth_st = await get_auth_state(uid)

    # ── Google auth code paste ────────────────────────────────────────────────
    if is_auth_code(text):
        logger.info(f"[Auth] Code paste from {uid} (state={auth_st})")
        await set_auth_state(uid, "code_sent")
        await clear_auth_url(uid)
        tmux_send(uid, text, enter=True)
        # Acknowledge — poll loop will automatically update the terminal message
        await update.message.reply_text(
            "✅ *Code sent to CLI.* Verifying with Google…\n"
            "The terminal will update automatically.",
            parse_mode="Markdown",
        )
        return

    # ── Any text while URL is shown but isn't a valid code ────────────────────
    if auth_st == "url_shown":
        await update.message.reply_text(
            "⚠️ Waiting for your Google authorization code.\n\n"
            "Please complete the Google sign-in flow and paste the authorization "
            "code here. It looks like: `4/0AX...`",
            parse_mode="Markdown",
        )
        return

    # ── Normal CLI input ──────────────────────────────────────────────────────
    # Send to tmux — poll loop automatically picks up the output
    tmux_send(uid, text, enter=True)
    # No need to reply — the terminal message updates automatically
    # But if there's no terminal message yet, send one
    if uid not in _terminal_msg:
        sent = await update.message.reply_text(
            "```\n...\n```",
            parse_mode="Markdown",
            reply_markup=kb_terminal(uid),
        )
        _terminal_msg[uid] = (sent.chat_id, sent.message_id)
        _last_sent[uid] = ""


# ─────────────────────────────────────────────────────────────────────────────
# Callback handler
# ─────────────────────────────────────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        return

    action = query.data
    chat_id = query.message.chat_id
    msg_id  = query.message.message_id
    logger.debug(f"[CB] {uid} → {action}")

    agy.start_for_user(uid)
    ensure_poll_loop(uid, context)

    # Set this as the terminal message if user clicks a button on it
    _terminal_msg[uid] = (chat_id, msg_id)

    if action.startswith("key_"):
        tmux_key(uid, action[4:])
        # Poll loop will update the terminal message automatically
        # But force a refresh quicker by resetting last_sent
        _last_sent[uid] = ""

    elif action == "ctrl_interrupt":
        tmux_interrupt(uid)
        auth_st = await get_auth_state(uid)
        if auth_st in ("url_shown", "code_sent"):
            await set_auth_state(uid, "none")
            await clear_auth_url(uid)
        _last_sent[uid] = ""

    elif action == "ctrl_refresh":
        # Force immediate update
        auth_st = await get_auth_state(uid)
        raw = tmux_capture(uid, lines=CAPTURE_LINES)

        if auth_st == "code_sent":
            url = detect_google_url(raw)
            if not url and not has_code_prompt(raw):
                await mark_authenticated(uid)
                logger.info(f"[Auth] Refresh confirmed auth complete for {uid}")

        # Reset sentinel so poll loop sends it fresh
        _last_sent[uid] = ""

        # Also do an immediate edit right now (don't wait for next poll)
        auth_st = await get_auth_state(uid)
        url = detect_google_url(raw)
        if auth_st == "url_shown" and url:
            text = (
                "🔑 *Antigravity — Authorization Required*\n\n"
                "1\\. Tap *Authorize with Google* below\n"
                "2\\. Complete sign\\-in in your browser\n"
                "3\\. Copy the authorization code\n"
                "4\\. *Paste it here* — it will be sent to the CLI automatically"
            )
            await _edit(context, chat_id, msg_id, text, kb_auth(url), "MarkdownV2")
        else:
            text = format_terminal(raw)
            await _edit(context, chat_id, msg_id, text, kb_terminal(uid))

    elif action == "ctrl_agy":
        tmux_send(uid, "agy")
        _last_sent[uid] = ""

    elif action == "ctrl_clear":
        _last_sent[uid] = ""
        await _edit(context, chat_id, msg_id,
                    "```\n(refreshing...)\n```",
                    kb_terminal(uid))

    elif action == "ctrl_logout":
        await mark_logged_out(uid)
        tmux_send(uid, "agy logout")
        _terminal_msg.pop(uid, None)
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=msg_id,
                text="🔴 *Logged out.*\n\nUse /start to reconnect.",
                parse_mode="Markdown",
            )
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Bot registration helpers
# ─────────────────────────────────────────────────────────────────────────────

BOT_COMMANDS = [
    BotCommand("start",    "Connect & launch Antigravity CLI"),
    BotCommand("status",   "Show session status"),
    BotCommand("logout",   "End session & clear auth"),
    BotCommand("cancel",   "Send Ctrl-C to CLI"),
    BotCommand("clear",    "Reset terminal screen"),
    BotCommand("list",     "List workspace files"),
    BotCommand("download", "Download file from workspace"),
]


def _register(app) -> None:
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("status",   cmd_status))
    app.add_handler(CommandHandler("logout",   cmd_logout))
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


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI async integration
# ─────────────────────────────────────────────────────────────────────────────

telegram_app = None


async def run_bot_async() -> None:
    global telegram_app
    logger.info("Starting Antigravity Bot (async)…")
    try:
        token = os.getenv("BOT_TOKEN") or settings.bot_token
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
        await telegram_app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
        logger.info("✅ Bot running!")
    except Exception as e:
        logger.error(f"FATAL: {e}", exc_info=True)


async def stop_bot_async() -> None:
    global telegram_app
    if telegram_app:
        try:
            await telegram_app.updater.stop()
            await telegram_app.stop()
            await telegram_app.shutdown()
        except Exception as e:
            logger.error(f"Shutdown error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Standalone entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    import asyncio as _aio
    from core.state_store import init_db, close_db

    async def _run():
        await init_db()
        token = os.getenv("BOT_TOKEN") or settings.bot_token
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
        logger.info("Starting bot (standalone polling)…")
        try:
            app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        except Exception:
            logger.exception("Bot crashed.")
        finally:
            await close_db()

    _aio.run(_run())


if __name__ == "__main__":
    main()
