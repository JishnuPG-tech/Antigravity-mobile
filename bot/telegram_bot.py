"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         ANTIGRAVITY  —  Professional Telegram Terminal Bot                 ║
║                                                                              ║
║  • Live PTY streaming with terminal emulator (CR, backspace, ANSI strip)    ║
║  • Full keyboard mapping: arrows, Tab, ESC, Ctrl-C/D/Z, F1-F5, PgUp/Dn    ║
║  • Persistent auth state via SQLite  (survives restarts until /logout)      ║
║  • Smart Google OAuth flow: URL → button → code paste → auto-forward        ║
║  • Auto-launch agy on /start; auto-reconnect on session loss                ║
║  • Rate-limited live Telegram edits (~1/sec), 90-second idle timeout        ║
║  • File upload/download to per-user workspace                               ║
║  • /status, /logout, /clear, /history commands                              ║
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
    get_state, get_auth_state, is_authenticated,
    set_auth_state, set_auth_url, get_auth_url,
    clear_auth_url, mark_authenticated, mark_logged_out,
)
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.error import BadRequest, RetryAfter, NetworkError
from backend.app.config import settings

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("antigravity.bot")

# ─────────────────────────────────────────────────────────────────────────────
# Core service
# ─────────────────────────────────────────────────────────────────────────────

agy = AntigravityManager()

# ─────────────────────────────────────────────────────────────────────────────
# In-process runtime state  (NOT persisted — cleared on restart)
# Persistent auth state lives in state_store (SQLite)
# ─────────────────────────────────────────────────────────────────────────────

# Virtual terminal screen buffer per user (ANSI-stripped, CR/BS applied)
_screen: dict[str, str] = defaultdict(str)

# Asyncio event fired when new output arrives for a user
_events: dict[str, asyncio.Event] = {}

# Active background streamer tasks
_streamers: dict[str, asyncio.Task] = {}

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

SCREEN_TAIL   = 3500    # chars shown in Telegram (< 4096 - markdown overhead)
EDIT_INTERVAL = 0.40    # seconds between Telegram message edits (rate limit)
IDLE_TIMEOUT  = 90.0    # seconds of no output before live loop exits

# ─────────────────────────────────────────────────────────────────────────────
# Authorization
# ─────────────────────────────────────────────────────────────────────────────

def _parse_authorized_users() -> set[int]:
    raw = settings.authorized_users or os.getenv("AUTHORIZED_USERS", "")
    users: set[int] = set()
    for v in [x.strip() for x in raw.split(",") if x.strip()]:
        try:
            users.add(int(v))
        except ValueError:
            pass
    return users


AUTHORIZED_USERS = _parse_authorized_users()


def is_authorized(user_id: int) -> bool:
    return bool(AUTHORIZED_USERS) and int(user_id) in AUTHORIZED_USERS


# ─────────────────────────────────────────────────────────────────────────────
# PTY / ANSI terminal emulator
# ─────────────────────────────────────────────────────────────────────────────

_RE_OSC8      = re.compile(r'\x1b\]8;[^\x1b\x07]*[\x1b\x07]')
_RE_CSI       = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]')
_RE_ESC_BARE  = re.compile(r'\x1b.')
_RE_CSI_STRAY = re.compile(r'\[[0-9;?]*[mJKhHdDL]')
_RE_CTRL      = re.compile(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]')

# Google OAuth URL — matches both v1 and v2 auth endpoints
_RE_GOOGLE_URL = re.compile(
    r'https://accounts\.google\.com/o/oauth2/(?:v2/)?auth\?[a-zA-Z0-9_.~\-=+%&]+'
)

# Authorization code patterns (what the user pastes back)
_RE_AUTH_CODE = re.compile(
    r'^(4/[0-9A-Za-z_\-]{10,}'       # Standard gcloud auth code
    r'|ya29\.[0-9A-Za-z_\-\.]{10,}'   # Bearer token
    r'|1//[0-9A-Za-z_\-]{10,}'        # Refresh token
    r'|[0-9A-Za-z_\-]{40,})$'         # Long opaque token fallback
)
_RE_DEVICE_CODE = re.compile(r'^[A-Z0-9]{4}-[A-Z0-9]{4}$')   # ABCD-1234

# Success/failure patterns in CLI output
_SUCCESS_KW = [
    "you are now logged in", "login successful", "authenticated successfully",
    "logged in as", "credentials saved", "access granted", "token saved",
    "authorization complete", "welcome", "you are logged in",
]
_CODE_PROMPT_KW = [
    "enter the authorization code", "enter authorization code",
    "enter code", "paste the code", "paste code",
    "verification code", "auth code", "enter the code",
]

_GARBAGE = {'', ']', ']];', ';', 'm', 'm ]8;;', '[m', '0m', '0', ' ', '\r\n'}


def strip_ansi(text: str) -> str:
    text = _RE_OSC8.sub('', text)
    text = _RE_CSI.sub('', text)
    text = _RE_ESC_BARE.sub('', text)
    text = text.replace("[?2004l", "").replace("[?2004h", "")
    text = _RE_CSI_STRAY.sub('', text)
    text = _RE_CTRL.sub('', text)
    return text


def apply_pty_chunk(buf: str, chunk: str) -> str:
    """Apply raw PTY chars onto the virtual screen buffer."""
    for ch in chunk:
        if ch == '\x08':          # backspace
            buf = buf[:-1] if buf else buf
        elif ch == '\r':          # carriage return — overwrite current line
            nl = buf.rfind('\n')
            buf = buf[:nl + 1] if nl != -1 else ''
        else:
            buf += ch
    return buf


def detect_google_url(raw: str) -> str | None:
    m = _RE_GOOGLE_URL.search(raw)
    if not m:
        return None
    url = m.group(0)
    # Trim any ANSI/control junk that may have been appended to the URL
    url = re.split(r'[\s\x1b\x00-\x08\x0b-\x1f\'\"\\]', url)[0]
    url = url.rstrip('];\\,')
    return url if len(url) > 50 else None


def detect_success(text: str) -> bool:
    low = text.lower()
    return any(kw in low for kw in _SUCCESS_KW)


def detect_code_prompt(text: str) -> bool:
    low = text.lower()
    return any(kw in low for kw in _CODE_PROMPT_KW)


def is_auth_code(text: str) -> bool:
    t = text.strip()
    return bool(_RE_AUTH_CODE.match(t)) or bool(_RE_DEVICE_CODE.match(t))


def process_chunk(uid: str, raw: str) -> str:
    """Strip ANSI from chunk, apply to screen buffer, return new buffer."""
    cleaned = strip_ansi(raw)
    if cleaned in _GARBAGE:
        return _screen[uid]
    buf = apply_pty_chunk(_screen[uid], cleaned)
    _screen[uid] = buf
    return buf


def get_tail(uid: str) -> str:
    buf = _screen[uid]
    if len(buf) > SCREEN_TAIL:
        cut = buf[-SCREEN_TAIL:]
        nl = cut.find('\n')
        cut = cut[nl + 1:] if nl != -1 else cut
        return cut
    return buf


def get_event(uid: str) -> asyncio.Event:
    if uid not in _events:
        _events[uid] = asyncio.Event()
    return _events[uid]


# ─────────────────────────────────────────────────────────────────────────────
# tmux interaction
# ─────────────────────────────────────────────────────────────────────────────

_KEY_MAP = {
    "Up": "Up", "Down": "Down", "Left": "Left", "Right": "Right",
    "Enter": "Enter", "Tab": "Tab", "BSpace": "BSpace", "Escape": "Escape",
    "ctrl_c": "C-c", "ctrl_d": "C-d", "ctrl_z": "C-z",
    "F1": "F1", "F2": "F2", "F3": "F3", "F4": "F4", "F5": "F5",
    "PPage": "PPage", "NPage": "NPage", "Home": "Home", "End": "End",
    "DC":  "DC",   # Delete key
    "IC":  "IC",   # Insert key
}


def _tmux(uid: str | int, *args: str) -> bool:
    session = agy.sm._session_name(str(uid))
    try:
        result = subprocess.run(
            ["tmux", *args, "-t", session],
            capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except Exception as e:
        logger.warning(f"tmux {args}: {e}")
        return False


def tmux_key(uid: str | int, key: str) -> None:
    tmux_key_name = _KEY_MAP.get(key, key)
    session = agy.sm._session_name(str(uid))
    try:
        subprocess.run(["tmux", "send-keys", "-t", session, tmux_key_name],
                       capture_output=True, timeout=5)
    except Exception as e:
        logger.warning(f"tmux_key {key}: {e}")


def tmux_send(uid: str | int, text: str, enter: bool = True) -> None:
    """Send text to tmux. Uses -l (literal) to prevent tmux interpreting special chars."""
    session = agy.sm._session_name(str(uid))
    try:
        subprocess.run(["tmux", "send-keys", "-t", session, "-l", text],
                       capture_output=True, timeout=5)
        if enter:
            subprocess.run(["tmux", "send-keys", "-t", session, "Enter"],
                           capture_output=True, timeout=5)
    except Exception as e:
        logger.warning(f"tmux_send: {e}")


def tmux_interrupt(uid: str | int) -> None:
    session = agy.sm._session_name(str(uid))
    try:
        subprocess.run(["tmux", "send-keys", "-t", session, "C-c"],
                       capture_output=True, timeout=5)
    except Exception as e:
        logger.warning(f"tmux_interrupt: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Keyboard layouts
# ─────────────────────────────────────────────────────────────────────────────

def kb_terminal(uid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        # Arrow cluster
        [InlineKeyboardButton("↑", callback_data="key_Up")],
        [
            InlineKeyboardButton("←", callback_data="key_Left"),
            InlineKeyboardButton("↵ Enter", callback_data="key_Enter"),
            InlineKeyboardButton("→", callback_data="key_Right"),
        ],
        [
            InlineKeyboardButton("↓", callback_data="key_Down"),
            InlineKeyboardButton("⇥ Tab", callback_data="key_Tab"),
            InlineKeyboardButton("⌫ BS", callback_data="key_BSpace"),
        ],
        # Modifier keys
        [
            InlineKeyboardButton("ESC", callback_data="key_Escape"),
            InlineKeyboardButton("^C", callback_data="key_ctrl_c"),
            InlineKeyboardButton("^D", callback_data="key_ctrl_d"),
            InlineKeyboardButton("^Z", callback_data="key_ctrl_z"),
        ],
        # Function keys (used by agy TUI menus)
        [
            InlineKeyboardButton("F1", callback_data="key_F1"),
            InlineKeyboardButton("F2", callback_data="key_F2"),
            InlineKeyboardButton("F3", callback_data="key_F3"),
            InlineKeyboardButton("F4", callback_data="key_F4"),
            InlineKeyboardButton("F5", callback_data="key_F5"),
        ],
        # Page navigation
        [
            InlineKeyboardButton("⇞ PgUp", callback_data="key_PPage"),
            InlineKeyboardButton("⇟ PgDn", callback_data="key_NPage"),
            InlineKeyboardButton("⇤ Home", callback_data="key_Home"),
            InlineKeyboardButton("⇥ End",  callback_data="key_End"),
        ],
        # Session controls
        [
            InlineKeyboardButton("🚀 Launch agy",    callback_data="ctrl_agy"),
            InlineKeyboardButton("🔄 Refresh",       callback_data="ctrl_refresh"),
        ],
        [
            InlineKeyboardButton("🛑 Stop (^C)",     callback_data="ctrl_interrupt"),
            InlineKeyboardButton("🗑 Clear Screen",  callback_data="ctrl_clear"),
        ],
    ])


def kb_auth(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Authorize with Google  ↗", url=url)],
        [InlineKeyboardButton("🔄 Refresh", callback_data="ctrl_refresh")],
    ])


def kb_code_waiting() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Check Status", callback_data="ctrl_refresh")],
        [InlineKeyboardButton("🛑 Cancel", callback_data="ctrl_interrupt")],
    ])


def kb_authenticated(uid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖥 Open Terminal", callback_data="ctrl_terminal")],
        [InlineKeyboardButton("🔴 Logout", callback_data="ctrl_logout")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Background PTY streamer — one persistent task per user
# ─────────────────────────────────────────────────────────────────────────────

async def _streamer(uid: str) -> None:
    """Tail the PTY log, update screen buffer, manage auth state transitions."""
    logger.info(f"[Streamer] Started for user {uid}")
    try:
        async for raw in agy.sm.stream_output(uid):
            if not raw:
                continue

            # ── Auth URL detection (before ANSI strip) ──────────────────────
            auth_st = await get_auth_state(uid)
            if auth_st not in ("authenticated",):
                url = detect_google_url(raw)
                if url:
                    stored = await get_auth_url(uid)
                    if stored != url:
                        await set_auth_url(uid, url)
                    if auth_st not in ("url_shown", "code_sent"):
                        await set_auth_state(uid, "url_shown")
                        logger.info(f"[Auth] Google URL detected for {uid}")

            # ── Apply chunk to screen buffer ─────────────────────────────────
            process_chunk(uid, raw)
            tail = get_tail(uid)

            # ── Success detection ────────────────────────────────────────────
            auth_st = await get_auth_state(uid)
            if auth_st in ("code_sent", "url_shown"):
                if detect_success(tail[-600:]):
                    await mark_authenticated(uid)
                    _screen[uid] = _RE_GOOGLE_URL.sub('', _screen[uid])
                    logger.info(f"[Auth] User {uid} authenticated successfully")

            # ── Signal live-update loops ─────────────────────────────────────
            get_event(uid).set()

    except asyncio.CancelledError:
        logger.info(f"[Streamer] Cancelled for user {uid}")
    except Exception as e:
        logger.error(f"[Streamer] Error for user {uid}: {e}", exc_info=True)


def ensure_streamer(uid: str, app) -> None:
    t = _streamers.get(uid)
    if t is None or t.done():
        _streamers[uid] = app.create_task(_streamer(uid))
        logger.debug(f"[Streamer] Spawned for {uid}")


# ─────────────────────────────────────────────────────────────────────────────
# Render screen → Telegram message
# ─────────────────────────────────────────────────────────────────────────────

async def render(context, chat_id: int, msg_id: int, uid: str) -> None:
    """Edit a Telegram message to reflect current terminal state."""
    auth_st = await get_auth_state(uid)

    # ── Google auth URL waiting ──────────────────────────────────────────────
    if auth_st == "url_shown":
        url = await get_auth_url(uid)
        if url:
            text = (
                "🔑 *Antigravity — Authorization Required*\n\n"
                "1\\. Tap *Authorize with Google* below\n"
                "2\\. Complete the sign\\-in flow in your browser\n"
                "3\\. Copy the authorization code shown\n"
                "4\\. *Paste it here* in this chat — it will be forwarded to the CLI automatically"
            )
            markup = kb_auth(url)
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=msg_id,
                    text=text, parse_mode="MarkdownV2",
                    reply_markup=markup,
                )
            except BadRequest as e:
                if "not modified" not in str(e).lower():
                    logger.debug(f"render(auth_url): {e}")
            except (RetryAfter, NetworkError):
                pass
            return

    # ── Code sent, waiting for CLI confirmation ──────────────────────────────
    if auth_st == "code_sent":
        text = (
            "⏳ *Verifying authorization code\\.\\.\\.*\n\n"
            "Antigravity is confirming your credentials with Google\\.\n"
            "This usually takes a few seconds\\. Tap *Check Status* to refresh\\."
        )
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=msg_id,
                text=text, parse_mode="MarkdownV2",
                reply_markup=kb_code_waiting(),
            )
        except BadRequest as e:
            if "not modified" not in str(e).lower():
                logger.debug(f"render(code_sent): {e}")
        except (RetryAfter, NetworkError):
            pass
        return

    # ── Normal terminal output ───────────────────────────────────────────────
    tail = get_tail(uid)
    if not tail.strip():
        tail = "(waiting for output...)"

    safe = tail.replace('`', '\u02cb')   # prevent broken code block
    text = "```\n" + safe + "\n```"
    markup = kb_terminal(uid)

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=msg_id,
            text=text, parse_mode="Markdown",
            reply_markup=markup,
        )
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            logger.debug(f"render(terminal): {e}")
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after + 0.5)
    except NetworkError as e:
        logger.warning(f"render NetworkError: {e}")
    except Exception as e:
        logger.debug(f"render unexpected: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Live update loop — drives message editing while output arrives
# ─────────────────────────────────────────────────────────────────────────────

async def live_loop(
    context, uid: str,
    chat_id: int, msg_id: int,
    timeout: float = IDLE_TIMEOUT,
) -> None:
    """Edit the Telegram message in real-time, rate-limited to EDIT_INTERVAL."""
    event = get_event(uid)
    deadline = time.monotonic() + timeout
    last_edit = 0.0

    while time.monotonic() < deadline:
        try:
            await asyncio.wait_for(asyncio.shield(event.wait()), timeout=1.5)
        except asyncio.TimeoutError:
            continue

        event.clear()
        deadline = time.monotonic() + timeout

        elapsed = time.monotonic() - last_edit
        if elapsed < EDIT_INTERVAL:
            await asyncio.sleep(EDIT_INTERVAL - elapsed)

        await render(context, chat_id, msg_id, uid)
        last_edit = time.monotonic()

    # Final render after loop finishes
    await render(context, chat_id, msg_id, uid)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: build a status message string
# ─────────────────────────────────────────────────────────────────────────────

async def build_status_text(uid: str, user_name: str) -> str:
    s = await get_state(uid)
    auth_st = s.get("auth_state", "none")

    if auth_st == "authenticated":
        logged_in = s.get("logged_in_at")
        if logged_in:
            dt = datetime.fromtimestamp(logged_in, tz=timezone.utc)
            since = dt.strftime("%Y-%m-%d %H:%M UTC")
        else:
            since = "unknown"
        status_icon = "🟢"
        status_line = f"Authenticated since {since}"
    else:
        status_icon = "🔴"
        status_line = "Not authenticated"

    return (
        f"*Antigravity — Session Status*\n\n"
        f"👤 User: `{user_name}`\n"
        f"{status_icon} Status: {status_line}\n\n"
        f"*Available Commands:*\n"
        f"• `/start` — Connect & launch agy\n"
        f"• `/status` — Show this screen\n"
        f"• `/logout` — End session & clear auth\n"
        f"• `/clear` — Clear screen buffer\n"
        f"• `/list` — List workspace files\n"
        f"• `/download <file>` — Download a file\n"
        f"• `/cancel` — Send Ctrl-C to CLI"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Command Handlers
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = update.effective_user.first_name or "User"

    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return

    # Re-initialize session (keeps auth state in DB but refreshes tmux)
    _screen[uid] = ""
    agy.start_for_user(uid)
    ensure_streamer(uid, context.application)

    # Check persistent auth state
    auth_st = await get_auth_state(uid)
    if auth_st == "authenticated":
        # Already logged in — just launch agy directly
        tmux_send(uid, "agy")
        sent = await update.message.reply_text(
            f"✅ *Welcome back, {name}\\!*\n\nConnecting to Antigravity CLI\\.\\.\\.",
            parse_mode="MarkdownV2",
            reply_markup=kb_terminal(uid),
        )
    else:
        # Not authenticated — launch agy which will trigger auth flow
        tmux_send(uid, "agy")
        sent = await update.message.reply_text(
            "🚀 *Antigravity CLI starting\\.\\.\\.*\n\nPlease wait\\.\\.\\.",
            parse_mode="MarkdownV2",
            reply_markup=kb_terminal(uid),
        )

    context.application.create_task(
        live_loop(context, uid, sent.chat_id, sent.message_id, timeout=120.0)
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return
    name = update.effective_user.first_name or "User"
    text = await build_status_text(uid, name)
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    # Mark logged out in DB
    await mark_logged_out(uid)

    # Send logout command to CLI
    tmux_send(uid, "agy logout", enter=True)

    # Clear screen buffer
    _screen[uid] = ""

    await update.message.reply_text(
        "🔴 *You have been logged out.*\n\n"
        "Your Antigravity session has ended and credentials have been cleared.\n"
        "Use `/start` to begin a new session.",
        parse_mode="Markdown",
    )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        return
    tmux_interrupt(uid)
    await update.message.reply_text("🛑 Sent Ctrl\\-C to your session\\.", parse_mode="MarkdownV2")


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        return
    _screen[uid] = ""
    await update.message.reply_text(
        "```\n(screen buffer cleared)\n```",
        parse_mode="Markdown",
        reply_markup=kb_terminal(uid),
    )


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    ws = os.path.join(agy.sm.workspace_root, f"user_{uid}", "default")
    os.makedirs(ws, exist_ok=True)

    try:
        files = sorted(
            f for f in os.listdir(ws)
            if os.path.isfile(os.path.join(ws, f)) and not f.startswith(".")
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error listing files: {e}")
        return

    if not files:
        await update.message.reply_text("📁 Your workspace is currently empty.")
        return

    lines = "\n".join(f"• `{f}`" for f in files)
    await update.message.reply_text(
        f"📁 *Workspace Files ({len(files)}):*\n\n{lines}\n\n"
        f"Use `/download <filename>` to retrieve any file.",
        parse_mode="Markdown",
    )


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
        await update.message.reply_text(f"❌ `{filename}` not found in workspace.", parse_mode="Markdown")
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

    # ── File uploads ─────────────────────────────────────────────────────────
    if update.message.document:
        doc = update.message.document
        fn = doc.file_name
        fp = os.path.join(ws, fn)
        msg = await update.message.reply_text(f"📥 Saving `{fn}` to workspace...", parse_mode="Markdown")
        try:
            tg = await context.bot.get_file(doc.file_id)
            await tg.download_to_drive(fp)
            await msg.edit_text(f"✅ Saved `{fn}` — accessible in your CLI workspace.", parse_mode="Markdown")
        except Exception as e:
            await msg.edit_text(f"❌ Failed: {e}")
        return

    if update.message.photo:
        photo = update.message.photo[-1]
        fn = f"photo_{int(time.time())}.jpg"
        fp = os.path.join(ws, fn)
        msg = await update.message.reply_text("📸 Saving image...", parse_mode="Markdown")
        try:
            tg = await context.bot.get_file(photo.file_id)
            await tg.download_to_drive(fp)
            await msg.edit_text(f"✅ Saved as `{fn}`.", parse_mode="Markdown")
        except Exception as e:
            await msg.edit_text(f"❌ Failed: {e}")
        return

    # ── Text input ───────────────────────────────────────────────────────────
    text = (update.message.text or "").strip()
    if not text:
        return

    # Ensure session & streamer alive
    agy.start_for_user(uid)
    ensure_streamer(uid, context.application)

    auth_st = await get_auth_state(uid)

    # ── AUTH CODE: user pasting Google auth code ─────────────────────────────
    if is_auth_code(text) or auth_st == "url_shown":
        logger.info(f"[Auth] Forwarding auth code for user {uid} (state={auth_st})")

        # Transition state
        await set_auth_state(uid, "code_sent")

        # Forward code to CLI using literal send (no special char interpretation)
        tmux_send(uid, text, enter=True)

        # Scrub the Google URL from screen buffer to prevent re-triggering
        _screen[uid] = _RE_GOOGLE_URL.sub('', _screen[uid])
        await clear_auth_url(uid)

        sent = await update.message.reply_text(
            "⏳ *Authorization code forwarded to Antigravity CLI*\n\n"
            "Verifying with Google — please wait a moment\\.\n"
            "Tap *Check Status* to refresh the screen\\.",
            parse_mode="MarkdownV2",
            reply_markup=kb_code_waiting(),
        )

        context.application.create_task(
            live_loop(context, uid, sent.chat_id, sent.message_id, timeout=60.0)
        )
        return

    # ── NORMAL INPUT: forward to CLI ─────────────────────────────────────────
    tmux_send(uid, text, enter=True)

    sent = await update.message.reply_text(
        "```\n...\n```",
        parse_mode="Markdown",
        reply_markup=kb_terminal(uid),
    )
    context.application.create_task(
        live_loop(context, uid, sent.chat_id, sent.message_id, timeout=60.0)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Callback query handler (button presses)
# ─────────────────────────────────────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(update.effective_user.id)
    if not is_authorized(update.effective_user.id):
        return

    action = query.data
    chat_id  = query.message.chat_id
    msg_id   = query.message.message_id
    logger.debug(f"[CB] user={uid} action={action}")

    # Ensure session & streamer alive
    agy.start_for_user(uid)
    ensure_streamer(uid, context.application)

    # ── Named key ────────────────────────────────────────────────────────────
    if action.startswith("key_"):
        key = action[4:]
        tmux_key(uid, key)
        await asyncio.sleep(0.25)
        await render(context, chat_id, msg_id, uid)

    # ── Stop / Ctrl-C ────────────────────────────────────────────────────────
    elif action == "ctrl_interrupt":
        tmux_interrupt(uid)
        # If stuck in auth, reset state
        auth_st = await get_auth_state(uid)
        if auth_st in ("url_shown", "code_sent"):
            await set_auth_state(uid, "none")
            await clear_auth_url(uid)
        await asyncio.sleep(0.3)
        await render(context, chat_id, msg_id, uid)

    # ── Force refresh ─────────────────────────────────────────────────────────
    elif action == "ctrl_refresh":
        raw = agy.read(uid, lines=60)
        cleaned = strip_ansi(raw)

        # Re-detect auth URL
        url = detect_google_url(raw)
        auth_st = await get_auth_state(uid)
        if url and auth_st not in ("authenticated", "code_sent"):
            await set_auth_url(uid, url)
            await set_auth_state(uid, "url_shown")
        elif not url and auth_st == "url_shown":
            await set_auth_state(uid, "none")

        _screen[uid] = cleaned
        await render(context, chat_id, msg_id, uid)

    # ── Launch agy ───────────────────────────────────────────────────────────
    elif action == "ctrl_agy":
        _screen[uid] = ""
        tmux_send(uid, "agy", enter=True)
        sent = await query.message.reply_text(
            "```\nLaunching Antigravity CLI...\n```",
            parse_mode="Markdown",
            reply_markup=kb_terminal(uid),
        )
        context.application.create_task(
            live_loop(context, uid, sent.chat_id, sent.message_id, timeout=120.0)
        )

    # ── Clear screen buffer ───────────────────────────────────────────────────
    elif action == "ctrl_clear":
        _screen[uid] = ""
        await render(context, chat_id, msg_id, uid)

    # ── Open terminal view ────────────────────────────────────────────────────
    elif action == "ctrl_terminal":
        await render(context, chat_id, msg_id, uid)

    # ── Logout ───────────────────────────────────────────────────────────────
    elif action == "ctrl_logout":
        await mark_logged_out(uid)
        tmux_send(uid, "agy logout", enter=True)
        _screen[uid] = ""
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=msg_id,
                text=(
                    "🔴 *Logged out successfully.*\n\n"
                    "Your Antigravity session has ended.\n"
                    "Use `/start` to reconnect."
                ),
                parse_mode="Markdown",
            )
        except BadRequest:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Bot commands registration
# ─────────────────────────────────────────────────────────────────────────────

BOT_COMMANDS = [
    BotCommand("start",    "Connect & launch Antigravity CLI"),
    BotCommand("status",   "Show your session status"),
    BotCommand("logout",   "End session & clear authentication"),
    BotCommand("cancel",   "Send Ctrl-C to the running CLI"),
    BotCommand("clear",    "Clear the terminal screen buffer"),
    BotCommand("list",     "List workspace files"),
    BotCommand("download", "Download a file from workspace"),
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
# FastAPI async integration (run_bot_async / stop_bot_async)
# ─────────────────────────────────────────────────────────────────────────────

telegram_app = None


async def run_bot_async() -> None:
    global telegram_app
    logger.info("Starting Antigravity Telegram Bot (async mode)...")
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
        # Register bot command menu
        try:
            await telegram_app.bot.set_my_commands(BOT_COMMANDS)
        except Exception:
            pass

        await telegram_app.start()
        await telegram_app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
        logger.info("✅ Antigravity Telegram Bot is running!")

    except Exception as e:
        logger.error(f"FATAL: Bot startup failed: {e}", exc_info=True)


async def stop_bot_async() -> None:
    global telegram_app
    if telegram_app:
        logger.info("Stopping Telegram bot...")
        try:
            await telegram_app.updater.stop()
            await telegram_app.stop()
            await telegram_app.shutdown()
        except Exception as e:
            logger.error(f"Bot shutdown error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Standalone entry point (python -m bot.telegram_bot)
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    import asyncio as _asyncio
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

        logger.info("Starting Antigravity Bot (standalone polling)")
        try:
            await app.bot.set_my_commands(BOT_COMMANDS)
        except Exception:
            pass

        try:
            app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        except Exception:
            logger.exception("Bot crashed.")
        finally:
            await close_db()

    _asyncio.run(_run())


if __name__ == "__main__":
    main()
