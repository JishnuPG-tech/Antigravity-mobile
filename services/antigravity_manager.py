"""High level wrapper to interact with the Antigravity CLI running inside
tmux sessions.
"""
import os
import subprocess
from core.session_manager import SessionManager


class AntigravityManager:
    def __init__(self, cfg=None):
        self.sm = SessionManager(cfg)

    def start_for_user(self, user_id: str, project: str | None = None):
        self.sm.ensure_session(user_id, project=project)

    def send_command(self, user_id: str, cmd: str) -> None:
        self.sm.send_input(user_id, cmd)

    def read(self, user_id: str, lines: int = 200) -> str:
        return self.sm.capture_output(user_id, lines=lines)
