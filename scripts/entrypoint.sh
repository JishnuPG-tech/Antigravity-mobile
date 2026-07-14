#!/usr/bin/env bash
set -euo pipefail

echo "Entrypoint: preparing environment..."

# Ensure /data exists and is writable
mkdir -p /data /data/workspaces /data/bin /data/logs 2>/dev/null || true
mkdir -p /tmp/antigravity-workspaces /tmp/antigravity-bin /tmp/antigravity-logs

DATA_ROOT="/data"
if [ ! -w /data ]; then
    echo "/data is not writable; falling back to /tmp for runtime files"
    DATA_ROOT="/tmp"
fi

export WORKSPACE_PATH="${WORKSPACE_PATH:-$DATA_ROOT/workspaces}"
mkdir -p "$WORKSPACE_PATH" "$DATA_ROOT/bin" "$DATA_ROOT/logs" 2>/dev/null || true

install_antigravity_async() {
    echo "Installing Antigravity CLI asynchronously..."
    if curl -fsSL https://antigravity.google/cli/install.sh -o /tmp/install.sh; then
        timeout 180 bash /tmp/install.sh >>"$DATA_ROOT/logs/antigravity-install.log" 2>&1 || true
        if [ -f "$HOME/.local/bin/agy" ]; then
            cp "$HOME/.local/bin/agy" "$DATA_ROOT/bin/agy" || true
            chmod +x "$DATA_ROOT/bin/agy" || true
            ln -sf "$DATA_ROOT/bin/agy" /usr/local/bin/agy || true
        fi
    else
        echo "Antigravity installer download failed" >>"$DATA_ROOT/logs/antigravity-install.log"
    fi
}

# Do not block Space startup on CLI installation.
install_antigravity_async &

echo "Starting supervisord"
exec /usr/bin/supervisord -n -c /app/config/supervisord.conf
