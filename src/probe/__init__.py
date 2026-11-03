"""Sonda HTTP de disponibilidad (ISS-B-13, B.13).

Mide disponibilidad, código de estado HTTP y latencia contra un origen único y
reporta cada corrida por el mismo camino de ingesta RUM (`POST
/telemetry/metrics`). Módulo ejecutable: `python -m probe` (D5: no se agrega
contenedor en este slice).

Módulos:
- `probe.config`: configuración por entorno (`PROBE_*`, `INGEST_BASE_URL`).
- `probe.runner`: una corrida (latencia, status, disponibilidad, S4).
- `probe.ingest`: arma el `RumEventBatch` y lo envía con la API key del tenant.
- `probe.scheduler`: corrida periódica a intervalo configurable (S1).
"""

__all__ = ["config", "ingest", "runner", "scheduler"]
