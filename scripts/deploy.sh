#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
ENV_FILE="${ENV_FILE:-.env}"
DOMAIN_OVERRIDE="${DOMAIN_OVERRIDE:-}"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-}"

cd "${PROJECT_DIR}"

echo "[deploy] project: ${PROJECT_DIR}"
echo "[deploy] compose file: ${COMPOSE_FILE}"
echo "[deploy] env file: ${ENV_FILE}"

if [[ -n "${DOMAIN_OVERRIDE}" ]]; then
  echo "[deploy] using DOMAIN override: ${DOMAIN_OVERRIDE}"
  DOMAIN="${DOMAIN_OVERRIDE}" docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --build
else
  docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --build
fi

docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" exec -T web python Services/manage.py migrate --noinput
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" exec -T web python Services/manage.py collectstatic --noinput
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" restart nginx
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps

if [[ -n "${HEALTHCHECK_URL}" ]]; then
  echo "[deploy] healthcheck: ${HEALTHCHECK_URL}"
  curl -fsSIL "${HEALTHCHECK_URL}" >/dev/null
  echo "[deploy] healthcheck passed"
fi

echo "[deploy] completed successfully"
