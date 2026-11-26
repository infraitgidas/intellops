"""Despachador de alertas de IntellOps (`intellops-comms`, ISS-B-10).

Este paquete corre en `intellops-comms` (ADR-0010): hace polling de las `ALERT`
en estado `Pending`, elige canal por severidad (Telegram o Email), envía con
retry y backoff exponencial y actualiza la alerta a `Sent` o `Failed`. No
expone puertos.

La decisión y el retry son una clase con repositorio y proveedores inyectados
(`dispatcher.py`), la configuración sale solo del entorno (`config.py`), los
transportes viven en `providers.py` y el acceso a la base en `repository.py`.

No hay imports desde `api.*` ni desde `ml.*`: ADR-0010 prohíbe cross-imports
entre contenedores, así que el módulo declara únicamente los esquemas de las
tablas que usa.
"""
