FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema (asyncpg necesitaría compilar si no hay wheel).
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Dependencias de Python: las mismas del core, que ya traen SQLAlchemy,
# asyncpg y pydantic-settings que usa el motor de reglas.
COPY src/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código fuente completo: el worker importa `ml.rules`, así que el paquete
# tiene que estar en la imagen. Copiar solo `entrypoint.py` (como hacía el
# placeholder) deja la imagen con ModuleNotFoundError al arrancar (ISS-B-14).
COPY src/ src/

# `api.*` y `ml.*` son top-level, igual que en el core.
ENV PYTHONPATH=/app/src

# Worker sin puertos (ADR-0010): no expone HTTP; un ciclo cada
# INTELLOPS_RULES_INTERVAL_SECONDS.
CMD ["python", "-m", "ml.entrypoint"]
