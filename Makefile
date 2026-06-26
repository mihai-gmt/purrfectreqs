# Forțează bash explicit — pe macOS, /bin/sh este bash în mod POSIX,
# dar read -p și alte bash-isme pot avea comportament diferit.
SHELL := /bin/bash

# Folosește interpretorul din venv explicit, ca testele/lint să meargă
# indiferent dacă venv-ul e activat (source .venv/bin/activate) sau nu.
# Override la nevoie: make test VENV=/alt/cale
VENV ?= .venv
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff

.PHONY: dev stop logs test test-file test-ui playwright-install lint lint-file format migrate reset-db shell-db ollama-start ollama-stop ollama-pull ollama-list help

help:
	@echo "PurrfectReqs — comenzi disponibile:"
	@echo ""
	@echo "  make dev          Pornește toate serviciile Docker (build dacă e nevoie)"
	@echo "  make stop         Oprește toate serviciile Docker"
	@echo "  make logs         Urmărește log-urile aplicației"
	@echo "  make test         Rulează toate testele"
	@echo "  make test-file    Rulează un test specific: make test-file f=tests/..."
	@echo "  make test-ui      Rulează testele UI în browser (necesită: make playwright-install)"
	@echo "  make playwright-install  Descarcă binarul de browser Playwright (Chromium)"
	@echo "  make lint         Rulează ruff check + ruff format --check"
	@echo "  make lint-file    Lint un fișier/listă specifică: make lint-file f=\"app/...\""
	@echo "  make format       Formatare automată cu ruff format + ruff check --fix"
	@echo "  make migrate      Rulează migrațiile Alembic în așteptare"
	@echo "  make reset-db     Șterge și recreează baza de date (dev only — distructiv)"
	@echo "  make shell-db     Deschide psql shell în containerul bazei de date"
	@echo "  make ollama-start Pornește Ollama ca serviciu macOS background"
	@echo "  make ollama-stop  Oprește serviciul Ollama"
	@echo "  make ollama-pull  Descarcă modelele Ollama necesare"
	@echo "  make ollama-list  Listează modelele Ollama disponibile local"
	@echo ""

dev:
	docker compose up --build -d
	@echo ""
	@echo "Stack pornit. Verificare: docker compose ps"
	@echo "Aplicație: http://localhost:8000"
	@echo "Ollama rulează nativ — verificare: curl http://localhost:11434/api/tags"

stop:
	docker compose down

logs:
	docker compose logs -f app

test:
	$(PYTEST) tests/ -v

test-file:
	$(PYTEST) $(f) -v

test-ui:
	$(PYTEST) -m ui -v

playwright-install:
	$(VENV)/bin/playwright install chromium

lint:
	$(RUFF) check .
	$(RUFF) format --check .

lint-file:
	$(RUFF) check $(f)
	$(RUFF) format --check $(f)

format:
	$(RUFF) format .
	$(RUFF) check --fix .

migrate:
	docker compose exec app alembic upgrade head

reset-db:
	@echo "ATENȚIE: Aceasta va șterge toate datele din baza de date de development."
	@read -p "Ești sigur? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	docker compose down -v
	docker compose up -d db
	@echo "Așteptare baza de date..."
	@sleep 5
	docker compose up -d

shell-db:
	docker compose exec db psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

ollama-start:
	brew services start ollama
	@echo "Ollama pornit. Verificare: curl http://localhost:11434/api/tags"

ollama-stop:
	brew services stop ollama

# Actualizează tag-ul modelului dacă folosești Qwen3-Coder în loc de Qwen2.5-Coder
ollama-pull:
	ollama pull qwen2.5-coder:32b-instruct-q4_K_M
	@echo "Model descărcat. Verificare: ollama list"

ollama-list:
	ollama list