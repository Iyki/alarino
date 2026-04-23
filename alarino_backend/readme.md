# Backend (Flask API)

## Location
`alarino_backend`

## Purpose
Provides API-only endpoints consumed by the Next.js frontend and direct API clients.

## Core Endpoints
- `POST /api/translate`
- `GET /api/daily-word`
- `GET /api/proverb`
- `POST /api/admin/bulk-upload`
- `GET /api/health`

## Local Run (without Docker)
Backend Python dependencies are expected to be installed in the Conda environment
`alarino`.

```bash
cd alarino_backend
conda create -n alarino python=3.11
conda activate alarino
python -m pip install -e .[dev]
python -m alarino_backend.app
```

If you prefer a plain virtualenv, create and activate `.venv`, then run the same
`python -m pip install -e .[dev]` command.

Docker production runs the API with Gunicorn via `alarino_backend.wsgi:app`.

## Environment Variables
Required in `alarino_backend/.env`:

```env
DATABASE_URL=postgresql://<user>:<pass>@<host>:<port>/<db>
ADMIN_API_KEY=<secret>
```

Optional:

```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://alarino.com,https://www.alarino.com
MAIN_PORT=5001
SITE_DOMAIN=https://alarino.com
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
GUNICORN_TIMEOUT=120
```

## Tests
```bash
cd alarino_backend
conda activate alarino
python -m pytest
```

## Docker
- Dockerfile: `alarino_backend/Dockerfile`
- Compose service name: `backend`
- Exposed internally on port `5001`
