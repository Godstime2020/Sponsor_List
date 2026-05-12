#!/bin/sh
set -e

cd /app

DB_PATH="${DATABASE_PATH:-/app/db.sqlite3}"
mkdir -p "$(dirname "$DB_PATH")"

python manage.py migrate --noinput

exec "$@"
