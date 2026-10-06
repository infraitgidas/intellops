# IntellOps — Makefile
# PI+D+i | Grupo GIDAS | UTN FrLP | Equipo InfraIT
#
# Comandos esenciales:
#   make setup      → Prepara el entorno
#   make up         → Levanta servicios
#   make test       → Corre tests
#   make lint       → Corre linters

.PHONY: setup up down test test-unit test-integration test-cov lint clean help migrate makemigrations

help:
	@echo "IntellOps — Comandos disponibles"
	@echo "  make setup          → Construye imágenes y prepara entorno"
	@echo "  make up             → Levanta servicios con Docker Compose"
	@echo "  make down           → Detiene servicios"
	@echo "  make migrate        → Aplica migraciones pendientes (alembic upgrade head)"
	@echo "  make makemigrations m=\"mensaje\" → Genera una nueva migración"
	@echo "  make test           → Corre toda la suite (unit + integration)"
	@echo "  make test-unit      → Solo tests unitarios (sin DB, rápido)"
	@echo "  make test-integration → Solo tests de integración (Postgres)"
	@echo "  make test-cov       → Suite completa con cobertura (gate 70%, HTML en htmlcov/)"
	@echo "  make lint           → Linters (flake8 + pylint)"
	@echo "  make clean          → Limpia artefactos"
	@echo "  make logs           → Logs de servicios"

setup:
	docker compose build
	docker compose run --rm intellops-core python -c "print('✅ Entorno listo')"

up:
	docker compose up -d
	@echo "✅ IntellOps stack corriendo (intellops-core, intellops-db, intellops-ai-engine, intellops-comms)"
	@echo "   API: http://localhost:8000"
	@echo "   Docs: http://localhost:8000/docs"
	@echo "   Health: http://localhost:8000/health"

down:
	docker compose down

migrate:
	docker compose run --rm intellops-core alembic upgrade head

makemigrations:
	docker compose run --rm intellops-core alembic revision -m "$(m)"

logs:
	docker compose logs -f

test:
	docker compose run --rm intellops-core python -m pytest tests/ -v

test-unit:
	docker compose run --rm --no-deps intellops-core python -m pytest tests/ -m unit

test-integration:
	docker compose run --rm intellops-core python -m pytest tests/ -m integration

test-cov:
	docker compose run --rm intellops-core python -m pytest tests/ --cov --cov-report=term-missing --cov-report=html

lint:
	docker compose run --rm intellops-core flake8 src/ tests/
	docker compose run --rm intellops-core pylint src/ --fail-under=9.0

clean:
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage coverage.xml reports
