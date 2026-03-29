#!/bin/sh
set -eu

DOMAIN="${DOMAIN:-jmcedu.duckdns.org}"
CERT_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"

if [ -f "$CERT_PATH" ]; then
  sed "s|__DOMAIN__|${DOMAIN}|g" /etc/nginx/templates/https.conf > /etc/nginx/conf.d/default.conf
  echo "Using HTTPS Nginx config for ${DOMAIN}"
else
  sed "s|__DOMAIN__|${DOMAIN}|g" /etc/nginx/templates/http-only.conf > /etc/nginx/conf.d/default.conf
  echo "Using HTTP-only Nginx config for ${DOMAIN} (certificate not found yet)"
fi
