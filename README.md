# Sponsor List

Django app to browse the UK **Worker & Temporary Worker** sponsor register with per-user notes, blacklist / tried flags, and search. Includes a **static** `public/` viewer that loads a pre-built SQLite file in the browser (no server-side DB).

## Features

- **Dashboard**: search, region filter, tabs (all / blacklisted / tried / has notes), **server-side** pagination with **editable rows per page** (25 / 50 / 100 via `per_page` query param)
- **Per-sponsor page**: notes fields and flags
- **Auth**: sign up, sign in, sign out
- **Django admin** (`/admin/`): **staff-only**, **Sponsors only** — browse the register, edit **Type &amp; rating** and **Route** (organisation / town / county are read-only), **Sync from Excel** (diff then insert/update; no row deletes from admin, no add-row button)
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

### Admin: sponsor register (staff)

The admin site is **limited to sponsors** (no Users / Groups / per-user note models). Use **`createsuperuser`** or set `is_staff=True` in the shell for accounts that may sign in here.

1. Sign in at `/admin/`
2. **Sponsors** — changelist (search/filter) and **change** form: **organisation, town, county** are read-only; **type &amp; rating** and **route** are editable.
3. **Sync from Excel** — **Sponsors** → *Sync from Excel*, or `/admin/companies/sponsor/sync-xlsx/` — upload `.xlsx`; the server runs the diff (add new rows, update rows that match org/town/county; it does **not** remove rows that exist only in the DB).

New sponsor rows are added **only** via Excel sync (or `import_sponsors` / Docker pre-seed); the admin **Add** control is disabled.

Very large uploads may hit the web server timeout — use `import_sponsors` from the shell for huge one-off loads.

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

The **Dockerfile** is multi-stage: it runs **`migrate`** + **`import_sponsors`** during **`docker build`**, using `Companies_With_COS.xlsx` in the build context. The resulting SQLite is copied into the final image as **`/app/preseed.sqlite3`**.

On **first container start**, if `DATABASE_PATH` points to a **missing or empty** file (typical new volume), **`docker-entrypoint.sh`** copies that pre-seed into place, then runs **`migrate`** (for any newer migrations), then Gunicorn.

Build and run with Compose (persists SQLite under a Docker volume at `/data`):

```bash
docker compose up --build
```

**Requirements:** `Companies_With_COS.xlsx` must be present in the project directory when you build (it is not excluded by `.dockerignore`). The first image build can take **a long time** while the sheet is imported.

Set secrets and hosts via environment variables or a `.env` file next to `docker-compose.yml` (see `.env.example`). Gunicorn listens on port **8000**.

To **re-seed from a new image** after you already used the volume, remove the old volume (this deletes DB + user data): `docker compose down -v` then `up` again.

### Pre-seed SQLite without Docker (optional)

To produce a standalone DB file (e.g. to inspect or copy manually):

```bash
chmod +x scripts/build_preseed_sqlite.sh
./scripts/build_preseed_sqlite.sh
# writes docker/preseed.sqlite3 by default; or: ./scripts/build_preseed_sqlite.sh /path/to/out.sqlite3
```

### Building for EC2 (avoid “exec format error”)

Typical EC2 instances are **linux/amd64**. If you build the image on an **Apple Silicon Mac**, the default image is often **linux/arm64**. That image will fail on EC2 with `exec format error` and a platform mismatch warning.

Build explicitly for AMD64, then save and copy to the server:

```bash
docker build --platform linux/amd64 -t sponsor-list:latest .
docker save sponsor-list:latest | gzip -9 > sponsor-list-docker-image.tar.gz
```

The first AMD64 build from an ARM Mac can be slow (QEMU emulation). After `docker load` on EC2, run the container again; the platform warning should be gone.

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
| `scripts/build_preseed_sqlite.sh` | Builds a Django SQLite DB with sponsors (optional; Docker also pre-seeds at build) |
| `Dockerfile` / `docker-compose.yml` | Multi-stage image with baked-in sponsor data for empty volumes |

## Repository

Remote: [github.com/Godstime2020/Sponsor_List](https://github.com/Godstime2020/Sponsor_List)

```bash
git clone https://github.com/Godstime2020/Sponsor_List.git
cd Sponsor_List
```
