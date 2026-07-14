#!/usr/bin/env bash
set -euo pipefail

echo "Entrypoint: preparing environment..."

# Ensure /data exists and is writable
mkdir -p /data /data/workspaces /data/bin /data/logs
chown -R appuser:appuser /data || true

install_antigravity_async() {
    echo "Installing Antigravity CLI asynchronously..."
    if curl -fsSL https://antigravity.google/cli/install.sh -o /tmp/install.sh; then
        timeout 180 bash /tmp/install.sh >>/data/logs/antigravity-install.log 2>&1 || true
        if [ -f "$HOME/.local/bin/agy" ]; then
            cp "$HOME/.local/bin/agy" /data/bin/agy || true
            chmod +x /data/bin/agy || true
            ln -sf /data/bin/agy /usr/local/bin/agy || true
        fi
    else
        echo "Antigravity installer download failed" >>/data/logs/antigravity-install.log
    fi
}

# Do not block Space startup on CLI installation.
install_antigravity_async &

echo "Starting supervisord"
exec /usr/bin/supervisord -n -c /app/config/supervisord.conf
