#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
ENV_FILE="${ENV_FILE:-.env}"
DOMAIN_OVERRIDE="${DOMAIN_OVERRIDE:-}"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-}"
DEPLOY_SERVICES="${DEPLOY_SERVICES:-web nginx}"
DEPLOY_ALL="${DEPLOY_ALL:-false}"
MAX_WEB_CPU_PERCENT="${MAX_WEB_CPU_PERCENT:-85}"
MAX_WEB_MEM_PERCENT="${MAX_WEB_MEM_PERCENT:-90}"

cd "${PROJECT_DIR}"

echo "[deploy] project: ${PROJECT_DIR}"
echo "[deploy] compose file: ${COMPOSE_FILE}"
echo "[deploy] env file: ${ENV_FILE}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[deploy] error: env file not found at ${ENV_FILE}"
  exit 1
fi

if grep -Eq '^DEBUG=true$' "${ENV_FILE}"; then
  echo "[deploy] error: DEBUG=true detected in ${ENV_FILE}. Set DEBUG=false for production."
  exit 1
fi

if ! grep -Eq '^DJANGO_SECRET_KEY=.{50,}$' "${ENV_FILE}"; then
  echo "[deploy] error: DJANGO_SECRET_KEY missing or too short in ${ENV_FILE}."
  exit 1
fi

if grep -Eq '^DJANGO_SECRET_KEY=change-this|^DJANGO_SECRET_KEY=unsafe-dev-secret-key-change-me$' "${ENV_FILE}"; then
  echo "[deploy] error: placeholder/unsafe DJANGO_SECRET_KEY detected in ${ENV_FILE}."
  exit 1
fi

if ! grep -Eq '^ALLOWED_HOSTS=.+$' "${ENV_FILE}"; then
  echo "[deploy] error: ALLOWED_HOSTS is missing or empty in ${ENV_FILE}."
  exit 1
fi

if ! grep -Eq '^CSRF_TRUSTED_ORIGINS=.+$' "${ENV_FILE}"; then
  echo "[deploy] error: CSRF_TRUSTED_ORIGINS is missing or empty in ${ENV_FILE}."
  exit 1
fi

if grep -Eq '^DB_PASSWORD=(1234|password|changeme)$' "${ENV_FILE}"; then
  echo "[deploy] error: weak/default DB_PASSWORD detected in ${ENV_FILE}."
  exit 1
fi

UP_ARGS=(-d --build)
if [[ "${DEPLOY_ALL}" == "true" ]]; then
  echo "[deploy] mode: full stack"
else
  echo "[deploy] mode: selective services (${DEPLOY_SERVICES})"
  # shellcheck disable=SC2206
  SELECTED_SERVICES=(${DEPLOY_SERVICES})
  UP_ARGS+=("${SELECTED_SERVICES[@]}")
fi

if [[ -n "${DOMAIN_OVERRIDE}" ]]; then
  echo "[deploy] using DOMAIN override: ${DOMAIN_OVERRIDE}"
  DOMAIN="${DOMAIN_OVERRIDE}" docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up "${UP_ARGS[@]}"
else
  docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up "${UP_ARGS[@]}"
fi

docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" exec -T web python Services/manage.py migrate --noinput
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" exec -T web python Services/manage.py check --deploy
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" exec -T web python Services/manage.py collectstatic --noinput
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" restart nginx
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps

WEB_CID="$(docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps -q web)"
if [[ -n "${WEB_CID}" ]]; then
  STATS_LINE="$(docker stats --no-stream --format '{{.CPUPerc}}|{{.MemPerc}}' "${WEB_CID}")"
  WEB_CPU_PCT="${STATS_LINE%%|*}"
  WEB_MEM_PCT="${STATS_LINE##*|}"
  WEB_CPU_PCT="${WEB_CPU_PCT%\%}"
  WEB_MEM_PCT="${WEB_MEM_PCT%\%}"

  echo "[deploy] web usage snapshot: CPU=${WEB_CPU_PCT}% MEM=${WEB_MEM_PCT}%"

  if ! awk -v cur="${WEB_CPU_PCT}" -v max="${MAX_WEB_CPU_PERCENT}" 'BEGIN { exit (cur+0 <= max+0) ? 0 : 1 }'; then
    echo "[deploy] error: web CPU usage ${WEB_CPU_PCT}% exceeds limit ${MAX_WEB_CPU_PERCENT}%."
    exit 1
  fi

  if ! awk -v cur="${WEB_MEM_PCT}" -v max="${MAX_WEB_MEM_PERCENT}" 'BEGIN { exit (cur+0 <= max+0) ? 0 : 1 }'; then
    echo "[deploy] error: web memory usage ${WEB_MEM_PCT}% exceeds limit ${MAX_WEB_MEM_PERCENT}%."
    exit 1
  fi
fi

if [[ -n "${HEALTHCHECK_URL}" ]]; then
  echo "[deploy] healthcheck: ${HEALTHCHECK_URL}"
  curl -fsSIL "${HEALTHCHECK_URL}" >/dev/null
  echo "[deploy] healthcheck passed"
fi

echo "[deploy] completed successfully"
