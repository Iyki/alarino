# Frontend (Next.js)

## Location
`frontend`

## Purpose
- Serves all web routes (`/`, `/word/[word]`, `/about`, `/admin`)
- Proxies browser API requests from `/api/*` to backend using app route proxy

## Key Commands
```bash
cd frontend
npm install
npm run dev
npm run lint
npm run typecheck
npm run test
npm run build
npm run start
```

## Runtime Environment Variables
See `frontend/.env.example`.

- `FRONTEND_SITE_URL`: canonical/metadata site URL
- `BACKEND_INTERNAL_URL`: backend target for server-side proxy

## API Proxy
- Route file: `frontend/app/api/[...path]/route.ts`
- Helper utilities: `frontend/lib/api-proxy.ts`

## Notes
- Uses Next.js App Router + TypeScript.
- In Docker Compose, frontend is exposed on `http://localhost:3000` in local development.
