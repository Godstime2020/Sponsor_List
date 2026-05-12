#!/usr/bin/env bash
# Build a Django SQLite DB with migrations applied and sponsors imported from
# Companies_With_COS.xlsx (same as import_sponsors). Use before docker build, or
# ship this file separately to EC2.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="${1:-$ROOT/docker/preseed.sqlite3}"
mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
export DATABASE_PATH="$OUT"
export DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-build-preseed-only}"
export DJANGO_DEBUG="${DJANGO_DEBUG:-false}"
echo "Migrating into $OUT …"
python manage.py migrate --noinput
echo "Importing sponsors from Companies_With_COS.xlsx (can take several minutes)…"
python manage.py import_sponsors
echo "Done. $(du -h "$OUT" | cut -f1)  $OUT"
