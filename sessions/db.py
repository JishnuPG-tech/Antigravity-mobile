"""Simple SQLite-backed session metadata store.
"""
import os
import sqlite3
from typing import Optional

DB_PATH = os.environ.get("SESSION_DB", "/app/data/sessions.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


class SessionStore:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id INTEGER PRIMARY KEY,
                    project TEXT,
                    created_at INTEGER
                )
                """
            )

    def create_session(self, user_id: int, project: str = "default"):
        import time
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions(user_id, project, created_at) VALUES (?,?,?)",
                (user_id, project, int(time.time())),
            )

    def get_session(self, user_id: int) -> Optional[dict]:
        with sqlite3.connect(self.path) as conn:
            cur = conn.execute("SELECT user_id, project, created_at FROM sessions WHERE user_id=?", (user_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {"user_id": row[0], "project": row[1], "created_at": row[2]}
