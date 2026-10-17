.PHONY: api test compose-up compose-down

api:
	uvicorn app.main:app --app-dir services/api --reload --port 8000

test:
	pytest -q tests/backend

compose-up:
	docker compose --env-file .env -f infra/docker-compose.yml up --build

compose-down:
	docker compose -f infra/docker-compose.yml down

