# Antigravity Telegram Bridge

Production-ready scaffold to control the Antigravity CLI remotely via Telegram.

This repository provides a FastAPI backend, an async Telegram bot, and a session
manager that keeps a persistent `tmux` session running the Antigravity CLI (`agy`).

Key features
- Persistent per-user tmux sessions running `agy`.
- Streaming terminal output to Telegram chats.
- File upload/download and workspace isolation per Telegram chat.
- Docker + Supervisor for production deployment.

See `README_SETUP.md` for installation and quick start instructions.
# Angigravity-Mobile