FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Dependencias de Python
COPY src/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Migraciones (alembic.ini apunta a src/api/infrastructure/db/migrations)
COPY alembic.ini .
COPY .flake8 .
COPY pyproject.toml .

# Código fuente y tests
COPY src/ src/
COPY tests/ tests/

# El test estático de path de import (tests/test_container_import_path.py)
# lee este Dockerfile desde /app para anclar el CMD del runtime.
COPY Dockerfile .

# api.* y ml.* deben ser importables como top-level (así los usan tests/ y src/api/main.py)
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port 8000"]
