# Developer Setup Guide

## Overview
Alarino runs as a 2-service stack:
- `frontend`: Next.js app on port `3000`
- `backend`: Flask API on port `5001`

The browser talks to same-origin `/api/*` on frontend. Frontend proxies those requests to backend.

## Prerequisites
- Docker Desktop (or Docker Engine + Compose v2)
- Git
- Optional for local non-Docker development:
  - Node.js 20+
  - Python 3.11+

## New Developer Checklist
1. Clone repo and enter project root:
```bash
git clone https://github.com/Iyki/alarino.git
cd /Users/ike/code/alarino
```
2. Create backend env file at `/Users/ike/code/alarino/alarino_backend/.env` with required keys:
```env
DATABASE_URL=postgresql://<user>:<pass>@<host>:<port>/<db>
ADMIN_API_KEY=<secret>
```
3. Start the stack:
```bash
docker compose up --build
```
4. Verify health and routing:
```bash
curl http://localhost:3000/api/health
curl http://localhost:5001/api/health
curl -I http://localhost:3000
```
5. Run frontend checks:
```bash
cd /Users/ike/code/alarino/frontend
npm run lint && npm run typecheck && npm run test
```
6. Stop services when done:
```bash
cd /Users/ike/code/alarino
docker compose down
```

## Repository Layout
- `/Users/ike/code/alarino/frontend`: Next.js TypeScript app
- `/Users/ike/code/alarino/alarino_backend`: Flask API
- `/Users/ike/code/alarino/docs`: project documentation
- `/Users/ike/code/alarino/alarino_frontend`: legacy frontend (reference only, deprecated)

## Quickstart (Docker)
1. Clone and enter the repo.
2. Create backend env file at `/Users/ike/code/alarino/alarino_backend/.env`.
3. Start services:

```bash
cd /Users/ike/code/alarino
docker compose up --build
```

4. Open:
- App: `http://localhost:3000`
- Backend health: `http://localhost:5001/api/health`
- Frontend proxy health: `http://localhost:3000/api/health`

## Stop Services
```bash
cd /Users/ike/code/alarino
docker compose down
```

If you see orphan warnings (for example old `nginx` container), use:

```bash
cd /Users/ike/code/alarino
docker compose down --remove-orphans
```

## Required Backend Environment Variables
Create `/Users/ike/code/alarino/alarino_backend/.env` with at least:

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

## Frontend Environment Variables
Frontend runtime variables are documented in:
- `/Users/ike/code/alarino/frontend/.env.example`

Current variables:
- `FRONTEND_SITE_URL` (metadata/canonical base URL)
- `BACKEND_INTERNAL_URL` (server-side proxy target)

With Docker Compose, these are already set for you.

## Run Without Docker (Optional)

### Backend
```bash
cd /Users/ike/code/alarino/alarino_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r pip-requirements.txt
python -m main.app
```

### Frontend
```bash
cd /Users/ike/code/alarino/frontend
npm install
BACKEND_INTERNAL_URL=http://127.0.0.1:5001 FRONTEND_SITE_URL=http://localhost:3000 npm run dev
```

## Test and Validation Commands

### Frontend
```bash
cd /Users/ike/code/alarino/frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

### Backend
```bash
cd /Users/ike/code/alarino/alarino_backend
python3 -m pytest
```

## Common API Endpoints
- `POST /api/translate`
- `GET /api/daily-word`
- `GET /api/proverb`
- `POST /api/admin/bulk-upload` (requires `Authorization: Bearer <ADMIN_API_KEY>`)
- `GET /api/health`

## Troubleshooting

### Docker build fails on backend with `psycopg2` compile errors
Use the current Dockerfiles in repo (they include build tooling). If this reappears, rebuild without cache:

```bash
cd /Users/ike/code/alarino
docker compose build --no-cache backend
docker compose up
```

### Next.js route typing errors during `next build`
This project uses Next.js 15 route typing conventions:
- Route handlers must only export allowed fields (`GET`, `POST`, `runtime`, etc.).
- Route context params are typed as `Promise<...>` in app router handlers/pages.

### Port already in use
If `3000` or `5001` is occupied:
- stop the conflicting service, or
- edit compose port mapping in `/Users/ike/code/alarino/docker-compose.override.yml`.

## Deployment Notes
- CI workflow: `/Users/ike/code/alarino/.github/workflows/deploy.yml`
- Deploy target runs only `frontend` + `backend` services.
