#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="/app:${PYTHONPATH:-}"

if [ -z "${BOT_TOKEN:-}" ]; then
    echo "BOT_TOKEN is not set; telegram bot disabled"
    exec sleep infinity
fi

exec python -u bot/telegram_bot.py
