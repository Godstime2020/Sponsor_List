#!/bin/sh
set -e

cd /app

DB_PATH="${DATABASE_PATH:-/app/db.sqlite3}"
mkdir -p "$(dirname "$DB_PATH")"

# First boot on an empty volume: copy DB baked at image build (migrations + sponsors).
if [ ! -s "$DB_PATH" ] && [ -f /app/preseed.sqlite3 ]; then
  echo "Initializing database from image pre-seed…"
  cp /app/preseed.sqlite3 "$DB_PATH"
fi

python manage.py migrate --noinput

exec "$@"
