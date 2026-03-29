#!/bin/sh
set -eu

if [ -n "${CLOUDFLARED_TOKEN:-}" ]; then
  echo "Starting Cloudflare Tunnel using token..."
  exec cloudflared tunnel --no-autoupdate run --token "$CLOUDFLARED_TOKEN"
fi

echo "CLOUDFLARED_TOKEN not set. Starting Quick Tunnel URL..."
exec cloudflared tunnel --no-autoupdate --url http://nginx:80
