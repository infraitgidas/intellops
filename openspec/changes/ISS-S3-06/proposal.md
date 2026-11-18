# Proposal: ISS-S3-06 — Pruebas unitarias de módulos críticos

**Cambio**: ISS-S3-06 (#45). **Owner**: Santiago. **Base**: `develop` (`0faaf1d`). **Depende de**: ISS-S2-04 (capas `unit`/`integration`), ISS-S2-05 (entorno reproducible).

## Intent

#45 pide "aumentar cobertura sobre los módulos de mayor riesgo": normalización, lógica de negocio, transformaciones y validaciones. El plan de fases la etiqueta "≥ 70 %".

Ese número global ya se cumple. Con solo `pytest -m unit` la cobertura total da **80 %**, y con la suite completa las verificaciones anteriores registran cerca de **90 %**. Leída literal, la issue ya estaría cerrada. El riesgo real está en **qué** cubre cada capa:

- Normalización y validación de ingesta estaban bien cubiertas (94-97 %).
- La lógica de negocio (`application_service` 29 %, `user_service` 24 %, `auth_service` 36 %) y la autorización (`dependencies.py` 48 %) solo se verificaban con tests de integración contra Postgres. Sin base de datos, reglas como la protección contra enumeración de cuentas, el commit/rollback de ADR-10, los 409 o el 401 indistinguible de la API key no tenían ninguna verificación rápida.

## Scope

### In Scope (RFC 2119)

- MUST: cada módulo crítico llega a **≥ 90 % de cobertura de líneas con `pytest -m unit` solo** (sin Postgres); los de validación y normalización, a 100 %.
- MUST: tests unitarios de `application_service`, `user_service` y `auth_service` con dobles en memoria (`FakeSession` y repositorios), incluida la invariante de ADR-10.
- MUST: tests unitarios de `get_current_user`, `require_role`, `require_api_key` y de los handlers de error.
- MUST: tests de los casos límite de `ingest_policy`, `ingest_normalizer`, `query_service`, de la transformación `_build_rows`/`_parse_ts`, `_as_int` y `api_reader`.
- MUST: tabla de cobertura antes/después por módulo en `verify-report.md`, como insumo para B.9 (gates obligatorios en CI).
- MUST NOT: modificar código de producción. Un bug que aparezca se documenta y se corrige en un cambio aparte.

### Out of Scope

- Agente JS (`src/agent`): ya tiene tests (`node --test`), pero ningún job del CI los corre. Queda como seguimiento para B.9.
- `session_service` (ISS-S3-03): todavía no está en `develop` y entra con sus propios tests unitarios.
- Repositorios SQLAlchemy: su lógica es SQL y se prueba en integración.
- Volver obligatorio un gate por módulo en CI: es el alcance de B.9.

## Capabilities

- **Nuevas**: ninguna (cambio solo de tests).
- **Modificadas**: `qa` (capa unitaria de módulos críticos).

## Approach

- Dobles en memoria por módulo: los servicios reciben `FakeSession` (fixture en `tests/conftest.py`, registra `commit`/`rollback`/`refresh`) y un repositorio en memoria que implementa la misma interfaz que el SQLAlchemy.
- Los guards de `dependencies.py` se llaman directamente, con los repositorios SQLAlchemy reemplazados por `monkeypatch`.
- Los tests nuevos no piden fixtures de base de datos, así que `conftest.py` los marca `unit` y corren en el job "Unit Tests" del CI.

## Affected Areas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `tests/conftest.py` | Modificado | Fixture `fake_session` |
| `tests/test_application_service.py`, `test_user_service.py`, `test_auth_service.py` | Nuevo | Lógica de negocio |
| `tests/test_dependencies.py` | Nuevo | Autorización y handlers de error |
| `tests/test_ingest_policy.py`, `test_ingest_transform.py` | Nuevo | Validaciones y transformaciones |
| `tests/test_ingest_normalizer.py`, `test_metrics_query.py`, `test_ingest_telemetry.py`, `test_ml_dataset_reader.py` | Modificado | Casos faltantes |
| `openspec/changes/ISS-S3-06/`, `CHANGELOG.md` | Docs | Documentos del cambio y changelog |

Módulos: QA, seguridad (auth y API keys) y captura (ingesta). No toca ML ni dashboard más allá del lector del dataset.

## Vínculo con la investigación

Una capa unitaria rápida sobre la ingesta y la autenticación sostiene la confiabilidad del dato que alimenta los experimentos de detección. Además deja medida la línea base de calidad que B.9 vuelve obligatoria.

## Recursos

Sin dependencias nuevas. La suite unitaria completa corre en unos 20 s, CPU-only y sin Postgres.

## Rollback

Son solo tests: revertir el PR deja el código de producción idéntico.
