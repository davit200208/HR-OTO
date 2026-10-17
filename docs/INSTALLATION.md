# HR-OTO Installation

1. Copy `.env.example` to `.env` and provide production secrets through a secret manager.
2. Start PostgreSQL and Redis with `docker compose -f infra/docker-compose.yml up -d`.
3. Install API dependencies from `services/api/requirements.txt`.
4. Run central Alembic migrations and tenant provisioning through the API service.
5. Install Flutter SDK, then run `flutter pub get` separately in `apps/employee_flutter`, `apps/admin_flutter` and `apps/owner_flutter`.

Native builds are not produced in this environment because Flutter/Docker toolchains are unavailable.
