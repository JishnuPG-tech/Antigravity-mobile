---
title: Antigravity Telegram Bridge
emoji: "🪄"
colorFrom: deepBlue
colorTo: purple
sdk: docker
sdk_version: "latest"
app_file: app.py
pinned: false
---

# Antigravity Telegram Bridge

---
title: Antigravity Telegram Bridge
sdk: docker
emoji: "🪄"
license: mit
---

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