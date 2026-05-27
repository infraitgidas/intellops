# IntellOps — Makefile
# PI+D+i | Grupo GIDAS | UTN FrLP | Equipo InfraIT
#
# Comandos esenciales:
#   make setup      → Prepara el entorno
#   make up         → Levanta servicios
#   make test       → Corre tests
#   make lint       → Corre linters

.PHONY: setup up down test lint clean help

help:
	@echo "IntellOps — Comandos disponibles"
	@echo "  make setup     → Construye imágenes y prepara entorno"
	@echo "  make up        → Levanta servicios con Docker Compose"
	@echo "  make down      → Detiene servicios"
	@echo "  make test      → Corre tests unitarios"
	@echo "  make test-cov  → Tests con cobertura"
	@echo "  make lint      → Linters (flake8 + pylint)"
	@echo "  make clean     → Limpia artefactos"
	@echo "  make logs      → Logs de servicios"

setup:
	docker compose build
	docker compose run --rm api python -c "print('✅ Entorno listo')"

up:
	docker compose up -d
	@echo "✅ IntellOps API corriendo en http://localhost:8000"
	@echo "   Docs: http://localhost:8000/docs"
	@echo "   Health: http://localhost:8000/health"

down:
	docker compose down

logs:
	docker compose logs -f

test:
	docker compose run --rm api python -m pytest tests/ -v

test-cov:
	docker compose run --rm api python -m pytest tests/ --cov=src --cov-report=term-missing

lint:
	docker compose run --rm api flake8 src/ tests/
	docker compose run --rm api pylint src/ --fail-under=7.0

clean:
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage coverage.xml
