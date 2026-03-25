.PHONY: dev stop logs test test-file lint format migrate reset-db shell-db help

help:
	@echo "PurrfectReqs — available commands:"
	@echo ""
	@echo "  make dev          Start all Docker services (builds if needed)"
	@echo "  make stop         Stop all Docker services"
	@echo "  make logs         Tail application logs"
	@echo "  make test         Run all tests"
	@echo "  make test-file    Run a specific test file: make test-file f=tests/..."
	@echo "  make lint         Run black --check + flake8"
	@echo "  make format       Run black (auto-format)"
	@echo "  make migrate      Run pending Alembic migrations"
	@echo "  make reset-db     Drop and recreate database (dev only — destructive)"
	@echo "  make shell-db     Open a psql shell inside the database container"
	@echo ""

dev:
	docker compose up --build -d
	@echo ""
	@echo "Stack is starting. Check status: docker compose ps"
	@echo "Application: http://localhost:8000"

stop:
	docker compose down

logs:
	docker compose logs -f app

test:
	pytest tests/ -v

test-file:
	pytest $(f) -v

lint:
	black . --check
	flake8 .

format:
	black .

migrate:
	docker compose exec app alembic upgrade head

reset-db:
	@echo "WARNING: This will delete all data in the development database."
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	docker compose down -v
	docker compose up -d db
	@echo "Waiting for database to be ready..."
	@sleep 5
	docker compose up -d

shell-db:
	docker compose exec db psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}