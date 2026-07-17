"""OpenCode CLI session manager — tmux-based per-user terminals."""
import asyncio
import os
import subprocess
import time
from typing import Optional

from backend.app.config import settings


class SessionManager:
    def __init__(self, cfg=None):
        self.workspace_root = os.getenv("WORKSPACE_PATH", settings.workspace_path)

    def _session_name(self, user_id: str) -> str:
        return f"opencode_user_{user_id}"

    def ensure_session(self, user_id: str, project: Optional[str] = None) -> None:
        """Ensure a tmux session exists for the user."""
        session = self._session_name(user_id)
        project = project or "default"
        ws = os.path.join(self.workspace_root, f"user_{user_id}", project)
        os.makedirs(ws, exist_ok=True)

        # Resize if session already exists
        subprocess.run(
            ["tmux", "resize-window", "-t", session, "-x", "88", "-y", "35"],
            capture_output=True,
        )

        # Check if session exists
        res = subprocess.run(["tmux", "has-session", "-t", session], capture_output=True)
        if res.returncode != 0:
            # Create new detached session
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", session, "-c", ws, "bash"],
                check=True,
            )
            time.sleep(0.1)
            subprocess.run(
                ["tmux", "resize-window", "-t", session, "-x", "88", "-y", "35"],
                capture_output=True,
            )

    def send_input(self, user_id: str, text: str) -> None:
        """Send text + Enter to the tmux pane (literal, no special char interpretation)."""
        session = self._session_name(user_id)
        try:
            subprocess.run(
                ["tmux", "send-keys", "-t", session, "-l", text],
                capture_output=True, timeout=5,
            )
            subprocess.run(
                ["tmux", "send-keys", "-t", session, "Enter"],
                capture_output=True, timeout=5,
            )
        except FileNotFoundError:
            pass

    def capture_output(self, user_id: str, lines: int = 40) -> str:
        """
        Capture the current rendered terminal screen via tmux capture-pane.
        Without -e flag tmux returns plain text — no ANSI escape codes.
        tmux handles all terminal emulation internally.
        """
        session = self._session_name(user_id)
        try:
            res = subprocess.run(
                ["tmux", "capture-pane", "-p", "-S", f"-{lines}",
                 "-t", f"{session}:0.0"],
                capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=5,
            )
            return res.stdout
        except FileNotFoundError:
            return ""
        except subprocess.TimeoutExpired:
            return ""
        except Exception:
            return ""

    def interrupt(self, user_id: str) -> None:
        """Send Ctrl-C to the tmux session."""
        session = self._session_name(user_id)
        try:
            subprocess.run(
                ["tmux", "send-keys", "-t", session, "C-c"],
                capture_output=True, timeout=5,
            )
        except FileNotFoundError:
            pass
