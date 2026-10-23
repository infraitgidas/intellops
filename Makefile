# IntellOps — Makefile
# PI+D+i | Grupo GIDAS | UTN FrLP | Equipo InfraIT
#
# Comandos esenciales:
#   make setup      → Prepara el entorno
#   make up         → Levanta servicios
#   make test       → Corre tests
#   make lint       → Corre linters

.PHONY: setup up down test test-unit test-integration test-cov test-contract test-down ci lint lock clean help migrate makemigrations

# Entorno reproducible de testing (ISS-S2-05): imagen con dependencias fijadas
# (requirements/dev.lock) + Postgres efímero, aislado del stack de dev.
export HOST_UID := $(shell id -u)
export HOST_GID := $(shell id -g)
TEST_COMPOSE = docker compose -f docker-compose.test.yml
TEST_RUN = $(TEST_COMPOSE) run --rm --build tests

help:
	@echo "IntellOps — Comandos disponibles"
	@echo "  make setup          → Construye imágenes y prepara entorno"
	@echo "  make up             → Levanta servicios con Docker Compose"
	@echo "  make down           → Detiene servicios"
	@echo "  make migrate        → Aplica migraciones pendientes (alembic upgrade head)"
	@echo "  make makemigrations m=\"mensaje\" → Genera una nueva migración"
	@echo "  make ci             → Pipeline completo del CI en el entorno de testing (lint + unit + suite + cobertura)"
	@echo "  make test           → Corre toda la suite (unit + integration)"
	@echo "  make test-unit      → Solo tests unitarios (sin DB, rápido)"
	@echo "  make test-integration → Solo tests de integración (Postgres)"
	@echo "  make test-cov       → Suite completa con cobertura (gate 70%, HTML en htmlcov/)"
	@echo "  make test-contract  → Contract tests (schemathesis, OpenAPI 3.1)"
	@echo "  make test-down      → Elimina contenedores y DB efímera del entorno de testing"
	@echo "  make lint           → Linters (flake8 + pylint)"
	@echo "  make lock           → Regenera requirements/dev.lock desde pyproject.toml (uv)"
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

# Todos los targets de test/lint corren en el entorno de testing, no en el
# contenedor de dev: misma imagen y mismos pasos que el CI.
ci:
	$(TEST_RUN)

test:
	$(TEST_RUN) sh -c "alembic upgrade head && pytest"

test-unit:
	$(TEST_COMPOSE) run --rm --build --no-deps tests pytest -m unit

test-integration:
	$(TEST_RUN) sh -c "alembic upgrade head && pytest -m integration"

test-cov:
	$(TEST_RUN) sh -c "alembic upgrade head && pytest --cov --cov-report=term-missing --cov-report=html"

test-contract:
	$(TEST_RUN) sh -c "alembic upgrade head && pytest tests/test_contract.py"

test-down:
	$(TEST_COMPOSE) down -v --remove-orphans

lint:
	$(TEST_COMPOSE) run --rm --build --no-deps tests sh -c "flake8 src/ tests/ && pylint src/ --fail-under=9.0"

# Requiere uv (https://docs.astral.sh/uv/). Resuelve para la misma plataforma
# que Dockerfile.test y el CI; mantiene los pins existentes salvo que cambie
# pyproject.toml (forzar upgrade: make lock UV_FLAGS=--upgrade).
lock:
	uv pip compile pyproject.toml --extra dev \
		--python-version 3.11 --python-platform x86_64-manylinux_2_28 \
		--generate-hashes --custom-compile-command "make lock" --quiet \
		$(UV_FLAGS) -o requirements/dev.lock

clean:
	docker compose down -v
	$(TEST_COMPOSE) down -v --remove-orphans
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage coverage.xml reports
