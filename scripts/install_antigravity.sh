#!/usr/bin/env bash
set -euo pipefail

echo "Installing Antigravity CLI if available..."
if curl -fsSL https://antigravity.google/cli/install.sh -o /tmp/install.sh; then
    bash /tmp/install.sh || true
else
    echo "Could not download Antigravity installer during build/runtime."
fi
