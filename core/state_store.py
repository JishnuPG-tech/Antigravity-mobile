"""Persistent user-state store backed by SQLite (aiosqlite).

Stores per-user data that survives process restarts:
  - auth_state : 'none' | 'url_shown' | 'code_sent' | 'authenticated' | 'logged_out'
  - auth_url   : the Google OAuth URL currently displayed to the user
  - logged_in_at  : Unix timestamp of last successful authentication
  - logged_out_at : Unix timestamp of last explicit logout (NULL = still authenticated)

All public functions are coroutines safe to call from asyncio tasks.
"""

import asyncio
import logging
import os
import time

import aiosqlite

logger = logging.getLogger(__name__)

# DB lives in the same persistent volume as workspaces
_DB_PATH = os.getenv("STATE_DB_PATH", "/data/workspaces/.bot_state.db")

_db: aiosqlite.Connection | None = None
_lock = asyncio.Lock()

_DDL = """
CREATE TABLE IF NOT EXISTS user_state (
    user_id      TEXT PRIMARY KEY,
    auth_state   TEXT NOT NULL DEFAULT 'none',
    auth_url     TEXT,
    logged_in_at  REAL,
    logged_out_at REAL,
    updated_at   REAL NOT NULL
);
"""


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

async def init_db() -> None:
    """Open (or create) the SQLite database and ensure schema."""
    global _db
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    _db = await aiosqlite.connect(_DB_PATH, check_same_thread=False)
    _db.row_factory = aiosqlite.Row
    await _db.execute(_DDL)
    await _db.commit()
    logger.info(f"[StateStore] Initialised at {_DB_PATH}")


async def close_db() -> None:
    global _db
    if _db:
        await _db.close()
        _db = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _ensure_row(uid: str) -> None:
    """Insert a default row for a new user if not already present."""
    await _db.execute(
        "INSERT OR IGNORE INTO user_state (user_id, auth_state, updated_at) VALUES (?, 'none', ?)",
        (uid, time.time()),
    )
    await _db.commit()


async def _update(uid: str, **fields) -> None:
    """Generic field updater. Always sets updated_at."""
    fields["updated_at"] = time.time()
    cols = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [uid]
    await _db.execute(f"UPDATE user_state SET {cols} WHERE user_id = ?", vals)
    await _db.commit()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_state(uid: str) -> dict:
    """Return the full state dict for a user. Creates a default row if absent."""
    async with _lock:
        await _ensure_row(uid)
        async with _db.execute(
            "SELECT * FROM user_state WHERE user_id = ?", (uid,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else {}


async def get_auth_state(uid: str) -> str:
    """Return just the auth_state string for this user."""
    s = await get_state(uid)
    return s.get("auth_state", "none")


async def is_authenticated(uid: str) -> bool:
    """Return True when the user has a live authenticated session."""
    return await get_auth_state(uid) == "authenticated"


async def set_auth_state(uid: str, state: str) -> None:
    """Update auth_state. Sets logged_in_at on 'authenticated', logged_out_at on 'logged_out'."""
    async with _lock:
        await _ensure_row(uid)
        fields: dict = {"auth_state": state}
        if state == "authenticated":
            fields["logged_in_at"] = time.time()
            fields["logged_out_at"] = None
        elif state == "logged_out":
            fields["logged_out_at"] = time.time()
        await _update(uid, **fields)


async def set_auth_url(uid: str, url: str) -> None:
    """Persist the Google OAuth URL for this user."""
    async with _lock:
        await _ensure_row(uid)
        await _update(uid, auth_url=url)


async def get_auth_url(uid: str) -> str | None:
    """Return the stored Google OAuth URL, or None."""
    s = await get_state(uid)
    return s.get("auth_url")


async def clear_auth_url(uid: str) -> None:
    """Remove the cached auth URL (after auth is complete or cancelled)."""
    async with _lock:
        await _update(uid, auth_url=None)


async def mark_authenticated(uid: str, auth_url: str | None = None) -> None:
    """Mark this user as fully authenticated."""
    async with _lock:
        await _ensure_row(uid)
        await _update(uid, auth_state="authenticated", logged_in_at=time.time(),
                      logged_out_at=None, auth_url=None)


async def mark_logged_out(uid: str) -> None:
    """Mark this user as explicitly logged out (auth state cleared)."""
    async with _lock:
        await _ensure_row(uid)
        await _update(uid, auth_state="none", auth_url=None,
                      logged_out_at=time.time())
