#!/bin/sh
# IntellOps — Pipeline de QA dentro del entorno de testing (ISS-S2-05)
#
# Mismos pasos y gates que .github/workflows/ci.yml (ISS-S2-04):
# lint → unit (sin DB) → migraciones → suite completa + cobertura (≥70%).
# Pensado para correr en el contenedor `tests` de docker-compose.test.yml:
#   make ci
set -eu

echo "==> Lint (flake8 + pylint ≥ 9.0)"
flake8 src/ tests/
pylint src/ --fail-under=9.0

echo "==> Unit tests (sin DB)"
pytest -m unit

echo "==> Migraciones (alembic upgrade head)"
alembic upgrade head

echo "==> Suite completa + cobertura"
pytest \
    --cov \
    --cov-report=term-missing \
    --cov-report=xml \
    --cov-report=html \
    --junitxml=reports/junit.xml
