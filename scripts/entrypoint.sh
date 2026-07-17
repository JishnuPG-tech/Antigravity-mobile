#!/usr/bin/env bash
set -euo pipefail

echo "Entrypoint: preparing environment..."

# Ensure /data exists and is writable
mkdir -p /data /data/workspaces /data/bin /data/logs 2>/dev/null || true

DATA_ROOT="/data"
if [ ! -w /data ]; then
    echo "/data is not writable; falling back to /tmp"
    DATA_ROOT="/tmp"
fi

export PYTHONPATH="/app:${PYTHONPATH:-}"
export WORKSPACE_PATH="${WORKSPACE_PATH:-$DATA_ROOT/workspaces}"
mkdir -p "$WORKSPACE_PATH" "$DATA_ROOT/bin" "$DATA_ROOT/logs" 2>/dev/null || true

install_opencode_async() {
    echo "Installing OpenCode CLI asynchronously..."
    local LOG="$DATA_ROOT/logs/opencode-install.log"
    if curl -fsSL https://opencode.ai/install -o /tmp/opencode-install.sh 2>>"$LOG"; then
        timeout 180 bash /tmp/opencode-install.sh >>"$LOG" 2>&1 || true
        # Try common install locations
        for BIN in "$HOME/.opencode/bin/opencode" "$HOME/.local/bin/opencode" "/usr/local/bin/opencode" "$DATA_ROOT/bin/opencode"; do
            if [ -f "$BIN" ]; then
                cp "$BIN" "$DATA_ROOT/bin/opencode" 2>/dev/null || true
                chmod +x "$DATA_ROOT/bin/opencode" 2>/dev/null || true
                ln -sf "$DATA_ROOT/bin/opencode" /usr/local/bin/opencode 2>/dev/null || true
                echo "OpenCode installed: $BIN" >>"$LOG"
                break
            fi
        done
    else
        echo "OpenCode installer download failed" >>"$LOG"
    fi
}

# Install in the background — don't block server startup
install_opencode_async &

echo "Starting uvicorn on port ${PORT:-7860}..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-7860}" --log-level info
