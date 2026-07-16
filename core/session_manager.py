"""Session manager: keeps persistent tmux sessions per user and proxies
input/output to the Antigravity CLI (`agy`).

This module provides a `SessionManager` class with operations to ensure a
tmux session exists, send input, and capture output. It uses `tmux` commands
and `pexpect` for robust interaction.
"""
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
        return f"agy_user_{user_id}"

    def ensure_session(self, user_id: str, project: Optional[str] = None) -> None:
        """Ensure a tmux session exists for the user and that `agy` is running.

        Creates per-user workspace under `WORKSPACE_PATH/user_{id}/project` and
        launches `agy` inside tmux if not present.
        """
        session = self._session_name(user_id)
        # create workspace
        project = project or "default"
        ws = os.path.join(self.workspace_root, f"user_{user_id}", project)
        os.makedirs(ws, exist_ok=True)

        # Force resize of the session in case it already exists
        subprocess.run(["tmux", "resize-window", "-t", session, "-x", "100", "-y", "40"], capture_output=True)

        # Check if tmux session exists
        res = subprocess.run(["tmux", "has-session", "-t", session], capture_output=True)

        if res.returncode != 0:
            # create detached session and start shell
            subprocess.run(["tmux", "new-session", "-d", "-s", session, "-c", ws, "bash"], check=True)
            time.sleep(0.1)
            # Set window size to 100x40 to prevent TUI menu clipping
            subprocess.run(["tmux", "resize-window", "-t", session, "-x", "100", "-y", "40"], check=False)
            # start `agy` inside tmux (it will self-update/run)
            subprocess.run(["tmux", "send-keys", "-t", session, "agy", "Enter"])

            # set up a tmux pipe-pane to write session output to a log file for streaming
            log_path = os.path.join(ws, ".agy_output.log")
            try:
                subprocess.run(["tmux", "pipe-pane", "-t", session, f"cat >> {log_path}"], check=False)
            except FileNotFoundError:
                # tmux not available in the environment
                pass

    def send_input(self, user_id: str, text: str) -> None:
        session = self._session_name(user_id)
        # send text and Enter
        try:
            subprocess.run(["tmux", "send-keys", "-t", session, text, "Enter"], check=True)
        except FileNotFoundError:
            # tmux not installed in test environment — ignore
            return

    def capture_output(self, user_id: str, lines: int = 200) -> str:
        session = self._session_name(user_id)
        # capture last N lines from tmux pane
        try:
            cmd = ["tmux", "capture-pane", "-pS", f"-{lines}", "-t", f"{session}:0.0"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            return res.stdout
        except FileNotFoundError:
            return ""

    async def stream_output(self, user_id: str):
        """Async generator that yields appended output from the session log file.

        Relies on `tmux pipe-pane` writing to `<workspace>/.agy_output.log`.
        If the log file doesn't exist or tmux is unavailable, yields empty strings.
        """
        session = self._session_name(user_id)
        ws = os.path.join(self.workspace_root, f"user_{user_id}")
        # find the first project folder if any
        if os.path.isdir(ws):
            # choose default project dir if available
            candidates = [os.path.join(ws, d) for d in os.listdir(ws)]
            target_dir = candidates[0] if candidates else ws
        else:
            target_dir = ws

        log_path = os.path.join(target_dir, ".agy_output.log")
        # create file if missing
        open(log_path, "a").close()

        # Tail file asynchronously
        pos = 0
        try:
            while True:
                if not os.path.exists(log_path):
                    await asyncio.sleep(0.5)
                    continue
                with open(log_path, "r", errors="replace") as f:
                    f.seek(pos)
                    data = f.read()
                    if data:
                        pos = f.tell()
                        yield data
                await asyncio.sleep(0.4)
        except asyncio.CancelledError:
            return

    def interrupt(self, user_id: str) -> None:
        """Send a SIGINT-like Ctrl-C to the tmux session to interrupt running command."""
        session = self._session_name(user_id)
        try:
            # send literal Ctrl-C
            subprocess.run(["tmux", "send-keys", "-t", session, "C-c"], check=True)
        except FileNotFoundError:
            return

if __name__ == "__main__":
    import argparse
    import logging
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    logger = logging.getLogger(__name__)
    sm = SessionManager()
    try:
        if args.watch:
            # Simple watcher loop to keep the supervisor process alive.
            while True:
                time.sleep(10)
    except Exception:
        logger.exception("Session watcher crashed; sleeping before retry")
        while True:
            time.sleep(60)
