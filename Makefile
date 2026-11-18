# IntellOps — Makefile
# PI+D+i | Grupo GIDAS | UTN FrLP | Equipo InfraIT
#
# Comandos esenciales:
#   make setup      → Prepara el entorno
#   make up         → Levanta servicios
#   make test       → Corre tests
#   make lint       → Corre linters

.PHONY: setup up down test test-unit test-integration test-cov test-contract test-down ci lint lock clean help migrate makemigrations fe-install fe-lint fe-test fe-build fe-e2e smoke

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
	@echo "  make smoke          → Smoke E2E sobre la stack real (build + flujo completo + stub de Telegram)"
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

# Smoke E2E (ISS-C-01): levanta la stack de docker-compose.yml con los
# intervalos de los workers en 5 s y el stub de Telegram (`intellops-telegram-stub`,
# profile `smoke`), y apunta el proveedor de Telegram al stub por el DNS del
# compose. Después corre el flujo completo. `SMOKE_NO_BUILD=1` reusa las
# imágenes ya construidas. Bajar todo (stub incluido):
# `docker compose --profile smoke down`. Ver docs/operations/smoke-e2e.md.
SMOKE_ENV = \
	INTELLOPS_RULES_INTERVAL_SECONDS=5 \
	INTELLOPS_COMMS_INTERVAL_SECONDS=5 \
	INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN=smoke-token \
	INTELLOPS_COMMS_TELEGRAM_CHAT_ID=smoke-chat \
	INTELLOPS_COMMS_TELEGRAM_API_BASE=http://intellops-telegram-stub:8099

smoke:
	$(SMOKE_ENV) sh -c 'set -e; if [ "$$SMOKE_NO_BUILD" = "1" ]; then \
		docker compose --profile smoke up -d; \
		else docker compose --profile smoke up -d --build; fi; \
		python3 scripts/smoke.py'

lint:
	$(TEST_COMPOSE) run --rm --build --no-deps tests sh -c "flake8 src/ tests/ && pylint src/ --fail-under=9.0 --fail-on=W,E"

# SPA React (ISS-B-05): build estático, no es un contenedor del compose
# (ADR-0010). Node ≥ 22 (`src/frontend/.nvmrc`); corre en el host, no en Docker.
fe-install:
	cd src/frontend && npm ci

fe-lint:
	cd src/frontend && npm run lint

fe-test:
	cd src/frontend && npm test

fe-build:
	cd src/frontend && npm run build && npm run check-size

fe-e2e:
	cd src/frontend && npm run test:e2e

# Requiere uv (https://docs.astral.sh/uv/); corre la versión fijada en
# UV_VERSION (la misma que setup-uv en .github/workflows/ci.yml) para que el
# lock salga idéntico en cualquier máquina. Hashes de todas las plataformas
# (x86_64 y ARM). Mantiene los pins existentes salvo que cambie pyproject.toml
# (forzar upgrade: make lock UV_FLAGS=--upgrade).
UV_VERSION = 0.9.5
lock:
	uvx uv@$(UV_VERSION) pip compile pyproject.toml --extra dev \
		--python-version 3.11 --python-platform x86_64-manylinux_2_28 \
		--generate-hashes --custom-compile-command "make lock" --quiet \
		$(UV_FLAGS) -o requirements/dev.lock

clean:
	docker compose down -v
	$(TEST_COMPOSE) down -v --remove-orphans
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage coverage.xml reports
