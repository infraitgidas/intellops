"""Motor determinístico de reglas de umbral (ISS-B-14, ADR-0013).

Este paquete corre en `intellops-ai-engine` (ADR-0010) y escribe las alertas
`Pending` que B.10 despacha. La agregación se calcula en PostgreSQL
(`aggregates.py`), la decisión es una función pura (`engine.py`) y el acceso a
la base vive en `repository.py`.

No hay imports desde `api.*` ni desde `probe.*`: ADR-0010 prohíbe
cross-imports entre contenedores, así que el módulo declara únicamente los
esquemas de las tablas que usa.
"""
