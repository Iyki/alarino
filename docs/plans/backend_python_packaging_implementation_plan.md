# Backend Python Packaging Implementation Plan

## Objective

Turn the backend into a properly installable Python package so backend development no longer depends on running commands from a specific working directory. This should reduce friction for local development, tests, scripts, Docker, and migrations.

## Current Problems

- Imports are cwd-sensitive and rely on top-level module names like `main` and `data`.
- Some backend code uses `sys.path` manipulation to make imports work.
- Local run commands depend on being inside `alarino_backend/`.
- Tests currently validate behavior, but they do not yet fully protect the packaging/runtime contract we want to preserve.
- Generic module names like `main` and `data` increase collision risk in a normal Python environment.

## Target State

The backend should be installable with `pip install -e .` from `alarino_backend/`, and all backend code should import from a single package namespace.

Preferred target layout:

```text
alarino_backend/
  pyproject.toml
  src/
    alarino_backend/
      __init__.py
      app.py
      flask_extensions.py
      db_models.py
      languages.py
      llm_service.py
      response.py
      translation_service.py
      data/
        __init__.py
        seed_data_utils.py
        proverbs_loader.py
        word_translations_loader.py
        create_tables.py
        generate_sitemap.py
        datasets/
  tests/
  migrations/
```

All imports should use `alarino_backend.*`.

The refactor should also commit to an app factory architecture:

- `app.py` exposes `create_app()`
- shared Flask extension objects live in `flask_extensions.py`
- runtime, tests, and migration tooling all target the factory-based app setup

## Non-Goals

- No API contract changes.
- No feature additions in translation, LLM, or admin flows.
- No schema changes unless migration loading requires minimal wiring updates.
- No broad cleanup unrelated to packaging and test safety.

## Implementation Phases

### Phase 1: Baseline and test hardening

Add regression coverage before moving files.

Work items:

- Preserve and clean up the existing Flask route tests.
- Add characterization tests for current API behavior:
  - `POST /api/translate`
  - `POST /api/translate/llm`
  - `GET /api/daily-word`
  - `GET /api/proverb`
  - `POST /api/admin/bulk-upload`
  - `GET /api/health`
- Add service-level tests for:
  - LLM client caching
  - retry behavior
  - prompt construction
  - translation service success/error paths with mocks
- Add startup/wiring tests:
  - app import succeeds
  - routes are registered
  - SQLAlchemy initialization succeeds
- Remove noisy prints and any test behavior that depends on manual inspection.

Exit criteria:

- Backend tests are runnable in a standard virtualenv.
- Current behavior is covered well enough to detect packaging regressions.

### Phase 2: Add packaging metadata

Introduce modern Python packaging in `alarino_backend/`.

Work items:

- Add `pyproject.toml`.
- Define project metadata and runtime dependencies.
- Define a `dev` optional dependency group for test/dev tooling.
- Configure package discovery for `src/`.
- Make `pyproject.toml` the single maintained dependency source of truth.
- Remove `pip-requirements.txt` as a hand-maintained dependency file.
- If a requirements-style artifact is still useful for Docker or caching later, generate it from packaging metadata rather than maintaining two sources by hand.

Recommended approach:

- Use `setuptools` with `pyproject.toml`.
- Install backend locally with `pip install -e .[dev]`.

Exit criteria:

- `pip install -e .` works from `alarino_backend/`.
- `import alarino_backend` works in a clean virtualenv after install.

### Phase 3: Break import-time coupling before the move

Restructure Flask wiring before relocating modules so the package move does not preserve the current import-order problems.

Work items:

- Introduce `flask_extensions.py` as a required step:
  - define `db`, `migrate`, and other shared Flask extension objects there
  - move extension initialization out of import-heavy modules
- Introduce an app factory and make it the target architecture:
  - `app.py` exposes `create_app()`
  - route registration happens from the factory or a dedicated registration module
  - Flask-Migrate wiring uses the factory-compatible initialization path
- Update tests and migration commands to target the app factory rather than relying on import-time global app creation.

Exit criteria:

- Shared extensions live outside the application package entry module.
- The backend can create the Flask app through `create_app()` without circular imports.
- Tests and migration wiring no longer rely on importing a globally created app.

### Phase 4: Restructure modules into a real package

Move backend code under `src/alarino_backend/`.

Work items:

- Move `main/` module contents into `src/alarino_backend/`.
- Move `data/` into `src/alarino_backend/data/`.
- Keep tests outside `src/`.
- Remove `sys.path` hacks.
- Replace all imports:
  - `from main ...` -> `from alarino_backend ...`
  - `from data ...` -> `from alarino_backend.data ...`
- Handle the old paths explicitly in the same change set:
  - remove the old `main/` and `data/` directories once imports and entry points are switched
  - do not leave long-lived compatibility stubs for the old namespace
  - call out that branches still importing `main.*` or `data.*` must be rebased or updated when this lands

Exit criteria:

- No backend code depends on cwd-based imports.
- No file modifies `sys.path` to load internal modules.
- No supported code path imports from legacy `main.*` or `data.*`.
- The old `main/` and `data/` directories are removed after the move.

### Phase 5: Standardize entry points, CI, and operational tooling

Update all execution paths to use the installed package namespace.

Work items:

- Update local run commands.
- Update Dockerfile to install the backend package and run the package entry point.
- Update GitHub Actions workflows to install the backend with `pip install -e .[dev]` and run backend verification explicitly.
- Update deployment/build automation to use the new backend packaging flow and entry point.
- Update pytest invocation guidance.
- Update migration commands for Flask/Alembic.
- Update any helper scripts and docs that still refer to `main` or `data`.

Target command style:

```bash
cd alarino_backend
conda create -n alarino python=3.11
conda activate alarino
python -m pip install -e .[dev]
python -m alarino_backend.app
python -m pytest
```

Preferred Flask command style:

```bash
flask --app alarino_backend.app:create_app routes
flask --app alarino_backend.app:create_app db upgrade
```

Exit criteria:

- Local dev docs, Docker, GitHub Actions, deployment automation, and migrations all use the same package namespace.

### Phase 6: Validation and rollout

Run verification in the environments developers actually use.

Work items:

One-time migration verification:

- Run tests from `alarino_backend/`.
- Run tests from the repo root where practical.
- Verify editable install in a clean environment.
- Verify app startup and health endpoint.
- Verify migrations can import application metadata.
- Verify data-loader scripts still import successfully.

Permanent GitHub Actions verification:

- Run backend tests on every relevant PR/push.
- Verify `pip install -e .[dev]` succeeds.
- Verify the package/app factory imports cleanly.
- Optionally keep one lightweight namespace regression check to prevent new `main.*` imports from being introduced.

Exit criteria:

- The backend can be installed and run without relying on current working directory quirks.
- The recurring packaging contract is covered by GitHub Actions rather than by manual checks alone.

## Test Plan

The packaging change should be protected by tests in four layers.

### 1. API regression tests

Goal: protect user-visible behavior.

Add or strengthen tests for:

- status codes
- JSON payload shapes
- validation errors
- admin authentication failures
- successful and failing translation paths
- health endpoint contract

### 2. Service tests

Goal: protect business logic while allowing refactors.

Add or strengthen tests for:

- `translation_service` with mocked DB and LLM dependencies
- `llm_service` configuration and retry behavior
- response helpers and language handling where behavior is non-trivial

### 3. Packaging/import tests

Goal: verify the new package contract directly.

Add tests or scripted checks for:

- `import alarino_backend`
- route module import
- package imports from a clean editable install
- no remaining imports from `main` or `data`

### 4. Startup/integration tests

Goal: catch wiring regressions.

Add tests or scripted checks for:

- app factory import/creation
- route registration
- database extension initialization
- migration environment importability

## Verification

### One-Time Migration Verification

- `pip install -e .[dev]` succeeds in `alarino_backend/`
- `pytest` passes
- `python -m alarino_backend.app` starts successfully
- health endpoint returns `200`
- no source file uses `sys.path` for internal package loading
- no source file imports from bare `main` or `data`
- Docker backend still starts with the new entry point
- migration commands still locate app metadata

### Permanent GitHub Actions Verification

- backend tests run on every relevant PR/push
- editable install succeeds in CI
- app factory import/startup wiring is exercised in CI
- keep at most a lightweight namespace regression check if it proves useful

## Risks and Mitigations

### Risk: import cycles appear after module moves

Mitigation:

- Separate shared objects into `flask_extensions.py`
- introduce the app factory before the package move

### Risk: tests encode current incidental behavior

Mitigation:

- focus characterization tests on public behavior, not internal implementation details

### Risk: scripts break after package rename

Mitigation:

- update all script imports in the same change set
- include import checks for script modules in validation

### Risk: docs and Docker lag behind code changes

Mitigation:

- treat docs and runtime command updates as part of the refactor, not follow-up work

## Recommended Execution Order

1. Harden tests around current backend behavior.
2. Add `pyproject.toml` and make it the maintained dependency source.
3. Introduce `flask_extensions.py` and `create_app()` to break import-time coupling.
4. Move code into `src/alarino_backend/`, rewrite imports, and remove legacy `main/` and `data/`.
5. Update Docker, GitHub Actions, docs, deployment flow, and migration commands.
6. Run one-time migration verification and keep recurring checks in GitHub Actions.

## Definition of Done

This work is complete when:

- the backend is a standard installable Python package
- imports use `alarino_backend.*` consistently
- local development no longer depends on running from a special directory
- Docker and migrations use the same package entry point
- regression and packaging tests pass and protect the new structure
