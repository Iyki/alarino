## Next.js TypeScript Frontend Migration + Docker 2-Service Cutover

### Summary
Migrate the current Flask-rendered frontend to a new Next.js (TypeScript) app in `/Users/ike/code/alarino/frontend`, with a **2-service topology in both dev and prod**: `frontend + backend`.  
Cut over immediately so Next.js serves web routes, make Flask backend API-only, keep `/Users/ike/code/alarino/alarino_frontend` temporarily in-repo for reference, and update CI/deploy for the new stack.

Browser API calls stay on same-origin `/api` via a thin Next.js proxy layer (BFF-lite).  
`api.alarino.com` routing is required and mapped by DNS/provider routing directly to the backend service.

### Locked Decisions
1. Scope: full parity now (`/`, `/word/[word]`, `/about`, `/admin`) with a **light refresh**.
2. Runtime: Next.js Node server (standalone output), not static export.
3. Routing: web app uses same-origin `/api` proxy; direct API host is required at `https://api.alarino.com/api/*`.
4. Cutover: immediate switch to Next.js for frontend routing.
5. Backend: remove legacy HTML/static Flask routes; keep API routes only.
6. Containers: 2 services in both dev and prod (`frontend` + `backend`).
7. CI: update now for new stack.
8. Testing: layered frontend test strategy without Playwright E2E.

### Implementation Plan

### 1) Scaffold and structure new frontend
1. Create/initialize Next.js App Router + TypeScript in `/Users/ike/code/alarino/frontend`.
2. Add core structure:
   - `/Users/ike/code/alarino/frontend/app/layout.tsx`
   - `/Users/ike/code/alarino/frontend/app/page.tsx`
   - `/Users/ike/code/alarino/frontend/app/word/[word]/page.tsx`
   - `/Users/ike/code/alarino/frontend/app/about/page.tsx`
   - `/Users/ike/code/alarino/frontend/app/admin/page.tsx`
   - `/Users/ike/code/alarino/frontend/lib/api.ts`
   - `/Users/ike/code/alarino/frontend/lib/types.ts`
   - `/Users/ike/code/alarino/frontend/components/*`
3. Add global styling + tokens (Tailwind + CSS vars) to keep current brand palette with light polish (spacing, typography, responsive refinements, focus states).

### 2) Migrate feature behavior from legacy templates/scripts
1. Homepage (`/`):
   - Translate form + result panel.
   - Word of day card with reveal toggle.
   - Proverb card with “next proverb”.
   - Contribution actions (modals or equivalent dialogs).
2. Word route (`/word/[word]`):
   - Auto-run translation for path word.
   - Update title/description/canonical with dynamic metadata.
3. About route (`/about`):
   - Move markdown source to frontend content path and render in Next.
4. Admin route (`/admin`):
   - Bulk upload form with API key input and dry-run toggle.
   - Render success/failure summary lists.
5. Replace legacy `window.ALARINO_CONFIG` usage with typed API client using relative `/api`.

### 3) Frontend Dockerization
1. Add `/Users/ike/code/alarino/frontend/Dockerfile` (multi-stage):
   - Build stage: install deps, `next build`.
   - Runtime stage: run standalone server on port `3000`.
2. Add `/Users/ike/code/alarino/frontend/.dockerignore`.
3. Configure Next for container runtime:
   - Standalone output.
4. Add `/Users/ike/code/alarino/frontend/.env.example` with frontend runtime vars.

### 4) Convert backend to API-only
1. In `/Users/ike/code/alarino/alarino_backend/main/app.py`, keep only `/api/*` endpoints (plus optional `/api/health`).
2. Remove Flask template/static/catch-all frontend-serving routes.
3. Keep CORS config aligned with frontend origin and direct API access patterns.

### 5) Compose and API proxy routing changes
1. Update `/Users/ike/code/alarino/docker-compose.yml`:
   - `backend` service exposing internal `5001`.
   - `frontend` service exposing app `3000`.
2. Keep `/Users/ike/code/alarino/docker-compose.prod.yml` and `/Users/ike/code/alarino/docker-compose.override.yml` aligned with 2-service topology.
3. Add `BACKEND_INTERNAL_URL=http://backend:5001` for frontend runtime.
4. Implement Next.js `/api` proxy route (BFF-lite):
   - Add `/Users/ike/code/alarino/frontend/app/api/[...path]/route.ts`.
   - Forward required methods, headers, query params, and request body to backend `/api/*`.
   - Preserve backend status codes and error payloads.

### 6) Provider-level domain routing tasks
1. Map frontend domains (for example, `alarino.com` and `www.alarino.com`) to the frontend service via DNS/provider routing.
2. Map `api.alarino.com` to the backend service via DNS/provider routing (required).
3. Ensure managed-provider SSL/TLS is active for frontend domains and `api.alarino.com`.

### 7) CI/CD updates
1. Update `/Users/ike/code/alarino/.github/workflows/deploy.yml` to validate new stack:
   - build backend and frontend images (or compose build),
   - run frontend checks + unit/component/proxy tests before deploy.
2. Deploy step brings up only `frontend + backend`.

### 8) Legacy frontend handling
1. Keep `/Users/ike/code/alarino/alarino_frontend` temporarily (reference only, not runtime).
2. Mark as deprecated in docs.
3. Remove in a later cleanup once post-cutover verification is complete.

### Public APIs / Interfaces / Config Changes
1. External site routing changes:
   - Web UI served by Next.js at `/`.
   - Browser path for app API remains `/api/*` through Next proxy.
2. Backend interface intent:
   - Flask becomes API-only (no HTML/static routes).
3. Infra interface changes:
   - Compose includes explicit `frontend` and `backend` services only.
4. Domain interface:
   - Direct API host available at `https://api.alarino.com/api/*` (required).

### Test Cases and Scenarios

### Frontend Test Matrix (without Playwright E2E)
1. Lint + typecheck + production build:
   - Heaviness: Low to Medium
   - Usefulness: Very high
   - Scope: `eslint`, `tsc --noEmit`, `next build`.
2. Unit tests (utilities and API helpers):
   - Heaviness: Low
   - Usefulness: High
   - Scope: frontend utility functions, response mappers, input validation helpers, API request builders.
3. Component tests (React Testing Library):
   - Heaviness: Medium
   - Usefulness: High
   - Scope:
     - homepage translate form submit/loading/error states,
     - word-of-day reveal toggle,
     - proverb refresh behavior,
     - contribution modal open/close interactions,
     - admin results rendering for success/failure data.
4. Next.js `/api` proxy route tests:
   - Heaviness: Low to Medium
   - Usefulness: Very high
   - Scope:
     - method forwarding (GET/POST and required methods),
     - query/body passthrough,
     - header forwarding rules,
     - backend status/error passthrough.
5. Post-deploy API smoke checks:
   - Heaviness: Low
   - Usefulness: High operational confidence
   - Scope:
     - direct reachability of `https://api.alarino.com/api/*`,
     - expected non-2xx behavior for invalid requests,
     - SSL and host routing sanity checks.

### Integration/stack checks
1. `docker compose up --build` starts the 2 services.
2. Web app `/api/*` calls succeed through Next proxy to backend.
3. Direct `https://api.alarino.com/api/*` reachability works for required endpoints.

### Acceptance criteria
1. No user-facing dependence on Flask templates/static assets.
2. Core routes/features parity achieved with light visual refresh.
3. CI validates frontend and deploys the 2-service stack.
4. Production domain routing works for frontend domains and `api.alarino.com`.

### Assumptions and Defaults
1. Keep existing backend API contracts unchanged.
2. Use npm for frontend dependency management.
3. Use App Router + TypeScript in Next.js.
4. Use same-origin `/api` as primary frontend API path via Next proxy.
5. Keep legacy frontend directory temporarily, but remove Flask frontend routes immediately.
6. Existing secrets/env management remains in current deployment workflow; only required new frontend vars are added.
