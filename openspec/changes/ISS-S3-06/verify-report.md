# Verify report: ISS-S3-06 — Pruebas unitarias de módulos críticos

**Fecha**: 2026-11-08. **Rama**: `s3-06` sobre `develop` (`0faaf1d`).

## Cómo se midió

Cobertura de líneas con **solo la capa unitaria**, sin Postgres:

```bash
PYTHONPATH=src:. pytest -m unit --cov=src --cov-report=term
```

Mismo comando antes (sobre `develop`) y después (con los tests de este cambio), en un venv con `requirements/dev.lock`.

## Resultado por módulo crítico (QA-U1)

| Criterio de #45 | Módulo | Antes | Después | Mínimo | Estado |
|---|---|---|---|---|---|
| Normalización | `ingest_normalizer.py` | 97 % | **100 %** | 100 % | Cumple |
| Validaciones | `ingest_policy.py` | 94 % | **100 %** | 100 % | Cumple |
| | `query_service.py` | 92 % | **100 %** | 100 % | Cumple |
| | `presentation/dependencies.py` | 48 % | **100 %** | 100 % | Cumple |
| | `presentation/errors.py` | 67 % | **100 %** | 100 % | Cumple |
| Lógica de negocio | `application_service.py` | 29 % | **100 %** | 90 % | Cumple |
| | `user_service.py` | 24 % | **100 %** | 90 % | Cumple |
| | `auth_service.py` | 36 % | **100 %** | 90 % | Cumple |
| | `ingest_service.py` | 91 % | **100 %** | 90 % | Cumple |
| Transformaciones | `infrastructure/ingest/queue.py` | 89 % | **95 %** | 90 % | Cumple |
| | `ml/pipeline/api_reader.py` | 96 % | **100 %** | 90 % | Cumple |

Total del proyecto con la capa unitaria: **80 % → 89 %**.

En `queue.py` quedan sin cubrir el corte de chunk dentro del loop del worker (líneas 179-183) y el dead-letter por error permanente (202-207). Los dos dependen de workers asyncio corriendo y ya los cubren los tests de integración (`test_worker_*` en `test_ingest_telemetry.py`).

## Suite

| Comando | Resultado |
|---|---|
| `pytest -m unit` | **522 passed, 1 xfailed** (antes: 385 passed). 137 tests nuevos más el xfail del bug. |
| `flake8 src/ tests/` | Sin errores |
| `make test-cov` (suite completa, Postgres efímero) | **660 passed, 1 xfailed, 1 xpassed** en 71 s. Cobertura total **95,45 %** (gate: 70 %). |

El `xfailed` es `test_create_application_honours_is_active_false` (QA-U5): documenta el bug de `is_active` en el alta de aplicaciones. Es esperado.

El `xpassed` de la suite completa es `test_schemathesis_live_contract_scoped`, marcado `xfail(strict=False)` desde antes de este cambio. Pasar es su resultado habitual y no lo toca esta PR.

## Hallazgos

| # | Tipo | Descripción | Acción |
|---|---|---|---|
| H-1 | Bug | `ApplicationService.create_application` ignora `ApplicationCreate.is_active` (APP-7): una app creada con `is_active: false` queda activa. | `xfail(strict=True)`; fix en un cambio aparte. |
| H-2 | Brecha de CI | Los tests del agente JS no corren en ningún job del CI. | Seguimiento para B.9. |
| H-3 | Robustez | `_build_rows` asume `metadata` objeto en el camino de métricas; no alcanzable hoy (Pydantic). | Anotado en `tasks.md`. |

## Veredicto

Los criterios de #45 (normalización, lógica de negocio, transformaciones y validaciones) quedan cubiertos con la capa unitaria por encima del mínimo de QA-U1, sin cambios de producción. La suite completa pasa en el entorno reproducible con 95,45 % de cobertura total.
