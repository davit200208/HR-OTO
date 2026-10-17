# HR-OTO

HR-OTO არის ქართული, multi-tenant HR Management SaaS-ის საწყისი modular monorepo. ეს repository ამჟამად მოიცავს მხოლოდ Stage 1 — Foundation-ს: სამ Flutter app shell-ს, საერთო design system-ს, FastAPI API skeleton-ს, PostgreSQL/Redis infrastructure-ს, Alembic bootstrap-სა და საწყის ტესტებს.

## Repository

```text
apps/employee_flutter       HR-OTO Employee (Android/iOS shell)
apps/admin_flutter          HR-OTO Admin (Android/iOS/Windows shell)
apps/owner_flutter          HR-OTO Owner (Android/iOS/Windows shell)
packages/flutter_core       shared Flutter primitives
packages/flutter_design_system  Georgian UI, themes, logo
services/api                FastAPI modular backend
infra                       Docker Compose and backend image
docs                        product and architecture source of truth
```

## Prerequisites

- Flutter SDK (stable channel) with Android/iOS/Windows targets as needed.
- Python 3.12+ recommended (Python 3.14 may require dependency wheels).
- Docker Desktop with Compose v2.

## Backend local run

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r services/api/requirements.txt
alembic -c services/api/alembic.ini upgrade head
uvicorn app.main:app --app-dir services/api --reload --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health/live
Invoke-RestMethod http://localhost:8000/api/v1/health/ready
```

## Docker Compose

```powershell
docker compose --env-file .env -f infra/docker-compose.yml up --build
```

The API is available at `http://localhost:8000`, PostgreSQL at `localhost:5432`, and Redis at `localhost:6379`. Production must use HTTPS termination, managed persistence and runtime secret injection.

## Flutter apps

Run each shell from its own directory:

```powershell
flutter pub get
flutter run -d windows       # Admin/Owner on Windows
flutter run                  # selected mobile device/emulator
```

For static verification:

```powershell
flutter analyze
```

The apps start with a real Material 3 window, Georgian UI, OTO-HR logo, responsive layout and Dark/Light mode toggle. No business module, authentication or PIN was added in Stage 1.

## Owner API

The independent Owner app uses the authenticated server endpoints below; it does not share Company Admin navigation or permissions:

```text
POST /api/v1/auth/login
GET  /api/v1/owner/dashboard
GET  /api/v1/owner/audit-log
GET  /api/v1/companies?search=&status=&license_status=
POST /api/v1/companies
GET  /api/v1/companies/{id}
PATCH /api/v1/companies/{id}
POST /api/v1/companies/{id}/owner
```

Owner routes require the server-side `system:manage` or `company:*` permission. Company actions are persisted in PostgreSQL and recorded in `audit_logs`.

## Tests

```powershell
pytest -q tests/backend
```

The integration test uses the app's dependency interfaces and can run against Docker services when the environment is available.

## Security notes

- Never commit `.env` or provider credentials.
- Brevo/SMSOffline secrets are intentionally absent from `.env.example` and must remain server-side.
- Tenant-aware data access and authentication are Stage 2 concerns; this Foundation API exposes health only.

See [docs/MASTER_SPEC.md](docs/MASTER_SPEC.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/ROADMAP.md](docs/ROADMAP.md) and [docs/PROGRESS.md](docs/PROGRESS.md).

