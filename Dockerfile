# --- Stage 1: build a SQLite file with Django migrations + sponsor import from XLSX
FROM python:3.12-slim-bookworm AS seed-builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    DJANGO_SECRET_KEY=build-only-not-for-production \
    DJANGO_DEBUG=false \
    DATABASE_PATH=/seed/db.sqlite3

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /seed \
    && python manage.py migrate --noinput \
    && python manage.py import_sponsors

# --- Stage 2: runtime image (includes preseed for empty volumes)
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    DJANGO_SECRET_KEY=build-only-not-for-production

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY --from=seed-builder /seed/db.sqlite3 /app/preseed.sqlite3

RUN mkdir -p /data \
    && DJANGO_DEBUG=false python manage.py collectstatic --noinput

RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
