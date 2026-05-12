# Sponsor List

Django app to browse the UK **Worker & Temporary Worker** sponsor register with per-user notes, blacklist / tried flags, and search. Includes a **static** `public/` viewer that loads a pre-built SQLite file in the browser (no server-side DB).

## Features

- **Dashboard**: search, region filter, tabs (all / blacklisted / tried / has notes), pagination
- **Per-sponsor page**: notes fields and flags
- **Auth**: sign up, sign in, sign out
- **Optional static site**: `public/index.html` + `sql.js` + `public/sponsors.db` (serve over HTTP only; `file://` blocks `fetch`)

## Requirements

- Python **3.12+** (matches the Docker image)
- `Companies_With_COS.xlsx` at the project root (for imports and building `sponsors.db`)

## Quick start (Django)

```bash
cd "Sponsored companies check"
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # edit DJANGO_SECRET_KEY and hosts as needed
python manage.py migrate
python manage.py createsuperuser   # optional
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) (redirects to the dashboard when signed in).

### Load sponsor rows from the spreadsheet

```bash
python manage.py import_sponsors
```

Replace the table first (destructive):

```bash
python manage.py import_sponsors --clear
```

Test with a subset:

```bash
python manage.py import_sponsors --limit 500
```

The XLSX path is configured in `config/settings.py` as `SPONSOR_XLSX` (default: project root `Companies_With_COS.xlsx`).

## Static viewer (`public/`)

Build `public/sponsors.db` from the same XLSX (stdlib only):

```bash
python3 scripts/build_db.py
```

Serve the folder over HTTP (example):

```bash
cd public && python3 -m http.server 8080
```

Then open [http://127.0.0.1:8080/](http://127.0.0.1:8080/).

## Docker

Build and run with Compose (persists SQLite under a Docker volume at `/data`):

```bash
docker compose up --build
```

Set secrets and hosts via environment variables or a `.env` file next to `docker-compose.yml` (see `.env.example`). The container runs migrations on start, then Gunicorn on port **8000**.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Required in production; long random string |
| `DJANGO_DEBUG` | `true` / `false` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated origins when using HTTPS (e.g. `https://example.com`) |
| `DATABASE_PATH` | Optional; SQLite path (default in settings: `db.sqlite3` in project root; Docker compose uses `/data/db.sqlite3`) |

## Project layout

| Path | Role |
|------|------|
| `companies/` | Models, views, templates, static CSS |
| `config/` | Django settings and URL config |
| `public/` | Standalone HTML/JS/CSS + `sponsors.db` for the browser viewer |
| `scripts/build_db.py` | Builds `public/sponsors.db` from the XLSX |
| `Dockerfile` / `docker-compose.yml` | Production-style container |

## Repository

Remote: [github.com/Godstime2020/Sponsor_List](https://github.com/Godstime2020/Sponsor_List)

```bash
git clone https://github.com/Godstime2020/Sponsor_List.git
cd Sponsor_List
```
