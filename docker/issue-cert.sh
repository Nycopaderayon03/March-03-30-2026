#!/bin/sh
set -eu

DOMAIN="${1:-${DOMAIN:-jmcedu.duckdns.org}}"
EMAIL="${2:-${LETSENCRYPT_EMAIL:-admin@jmcedu.duckdns.org}}"

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
  echo "Usage: DOMAIN=<domain> LETSENCRYPT_EMAIL=<email> ./docker/issue-cert.sh"
  exit 1
fi

echo "Starting stack (HTTP challenge mode)..."
docker compose up -d db web nginx

echo "Requesting certificate for ${DOMAIN}..."
docker compose run --rm --entrypoint certbot certbot \
  certonly --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email

echo "Reloading Nginx with HTTPS config..."
docker compose restart nginx

echo "Done. HTTPS should now be available at https://${DOMAIN}"
