#!/bin/sh
set -e

if [ "${DB_ENGINE:-postgresql}" = "postgresql" ] || [ "${DB_ENGINE:-postgresql}" = "postgres" ]; then
  echo "Waiting for PostgreSQL at ${DB_HOST:-db}:${DB_PORT:-5432}..."
  until python - <<'PY'
import os
import psycopg2

psycopg2.connect(
    dbname=os.environ.get("DB_NAME", "sanction_tracker_db"),
    user=os.environ.get("DB_USER", "sanction_user"),
    password=os.environ.get("DB_PASSWORD", "1234"),
    host=os.environ.get("DB_HOST", "db"),
    port=os.environ.get("DB_PORT", "5432"),
).close()
print("PostgreSQL is ready")
PY
  do
    sleep 1
  done
fi

python Services/manage.py migrate --noinput
python Services/manage.py collectstatic --noinput

exec "$@"
