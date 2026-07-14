#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="/app:${PYTHONPATH:-}"

exec python -u core/session_manager.py --watch
