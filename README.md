# Alarino

Alarino is a digital Yoruba-English dictionary project focused on data quality, cultural preservation, and community contributions.

## Project Layout
- Frontend: `frontend` (Next.js + TypeScript)
- Backend: `alarino_backend` (Flask API)
- Docs: `docs`

## Developer Quickstart
1. Create backend env file at `alarino_backend/.env` with:

```env
DATABASE_URL=postgresql://<user>:<pass>@<host>:<port>/<db>
ADMIN_API_KEY=<secret>
```

2. Start the full stack:

```bash
docker compose up --build
```

3. Open:
- App: `http://localhost:3000`
- Frontend proxy health: `http://localhost:3000/api/health`
- Backend health: `http://localhost:5001/api/health`

4. Stop services:

```bash
docker compose down
```

## Documentation
- Docs hub: `docs/README.md`
- Full setup guide: `docs/developer_setup.md`
- Frontend guide: `frontend/README.md`
- Backend guide: `alarino_backend/readme.md`
- Migration plan: `docs/frontend_migration_plan.md`

## Stack and Routing Notes
- The web app is served by Next.js.
- Browser API path is `/api/*` (proxied by frontend to backend).
- Flask backend is API-only and no longer serves template/static web routes.
- Runtime topology in dev/prod is two services: `frontend` + `backend`.

## Community Contributions
You can contribute by:
- Suggesting new words and translations
- Providing feedback on existing translations
- Contributing to the codebase
- Sharing Alarino with others interested in Yoruba language resources

- GitHub issues: [https://github.com/Iyki/alarino/issues](https://github.com/Iyki/alarino/issues)
- Add words form: [https://forms.gle/uBySW3JvVb32z5W69](https://forms.gle/uBySW3JvVb32z5W69)
- Translation feedback form: [https://forms.gle/nvJxyCjD2EcLha7m7](https://forms.gle/nvJxyCjD2EcLha7m7)
