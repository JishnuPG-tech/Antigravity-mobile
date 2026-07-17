---
title: Opencode CLI
emoji: 🖥️
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Opencode CLI - Web Console & Telegram Bridge

A production-ready FastAPI backend, Web Console, and Telegram Bot bridge for the [OpenCode AI coding agent](https://opencode.ai). This Space runs the OpenCode CLI inside a Docker container.

## Features

- Full OpenCode CLI access via Web Terminal (`/webapp` route)
- Telegram Bot Bridge with persistent tmux sessions per user
- WebSocket-based terminal streaming with fast change detection
- Auto-sleep/auto-resume (5-minute inactivity timeout) to conserve Space memory
- Production deployment with Docker & Supervisor