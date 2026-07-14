#!/usr/bin/env bash
set -euo pipefail

echo "Entrypoint: preparing environment..."

# Ensure /data exists and is writable
mkdir -p /data /data/workspaces /data/bin
chown -R appuser:appuser /data || true

echo "Installing Antigravity CLI to /data (if available)"
if curl -fsSL https://antigravity.google/cli/install.sh -o /tmp/install.sh; then
    bash /tmp/install.sh || true
    # Try to move binary into /data/bin for persistence
    if [ -f "$HOME/.local/bin/agy" ]; then
        mv "$HOME/.local/bin/agy" /data/bin/agy || true
        chmod +x /data/bin/agy || true
        ln -sf /data/bin/agy /usr/local/bin/agy || true
    fi
fi
# If a pre-baked binary is included in the repo at /app/antigravity-cli/bin/agy, copy it to /data
if [ -f /app/antigravity-cli/bin/agy ]; then
    cp /app/antigravity-cli/bin/agy /data/bin/agy || true
    chmod +x /data/bin/agy || true
    ln -sf /data/bin/agy /usr/local/bin/agy || true
fi

echo "Starting supervisord"
exec /usr/bin/supervisord -n -c /app/config/supervisord.conf
