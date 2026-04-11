#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SONAR_HOST_URL="${SONAR_HOST_URL:-https://sonarcloud.io}"
SONAR_SCANNER_IMAGE="${SONAR_SCANNER_IMAGE:-sonarsource/sonar-scanner-cli:12.0.0.3214_8.0.1}"

if [[ -z "${SONAR_TOKEN:-}" ]]; then
  echo "[sonar] SONAR_TOKEN is not set. Export it first and rerun this script." >&2
  exit 1
fi

cd "${PROJECT_DIR}"

echo "[sonar] project: ${PROJECT_DIR}"
echo "[sonar] host: ${SONAR_HOST_URL}"
echo "[sonar] image: ${SONAR_SCANNER_IMAGE}"

docker run --rm \
  -w /usr/src \
  -e SONAR_HOST_URL="${SONAR_HOST_URL}" \
  -e SONAR_TOKEN="${SONAR_TOKEN}" \
  -v "${PROJECT_DIR}:/usr/src" \
  "${SONAR_SCANNER_IMAGE}" \
  --define "sonar.projectBaseDir=/usr/src" \
  --define "sonar.projectKey=Nycopaderayon03_March-03-30-2026" \
  --define "sonar.organization=nycopaderayon03" \
  --define "sonar.sources=." \
  --define "sonar.exclusions=.venv/**,venv/**,__pycache__/**,logs/**,media/**,staticfiles/**,db.sqlite3"
