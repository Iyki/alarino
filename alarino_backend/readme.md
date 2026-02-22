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
```bash
cd alarino_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r pip-requirements.txt
python -m main.app
```

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
```

## Tests
```bash
cd alarino_backend
python3 -m pytest
```

## Docker
- Dockerfile: `alarino_backend/Dockerfile`
- Compose service name: `backend`
- Exposed internally on port `5001`
