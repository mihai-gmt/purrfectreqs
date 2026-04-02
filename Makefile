# Forțează bash explicit — pe macOS, /bin/sh este bash în mod POSIX,
# dar read -p și alte bash-isme pot avea comportament diferit.
SHELL := /bin/bash

.PHONY: dev stop logs test test-file lint format migrate reset-db shell-db ollama-start ollama-stop ollama-pull ollama-list help

help:
	@echo "PurrfectReqs — comenzi disponibile:"
	@echo ""
	@echo "  make dev          Pornește toate serviciile Docker (build dacă e nevoie)"
	@echo "  make stop         Oprește toate serviciile Docker"
	@echo "  make logs         Urmărește log-urile aplicației"
	@echo "  make test         Rulează toate testele"
	@echo "  make test-file    Rulează un test specific: make test-file f=tests/..."
	@echo "  make lint         Rulează black --check + flake8"
	@echo "  make format       Formatare automată cu black"
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