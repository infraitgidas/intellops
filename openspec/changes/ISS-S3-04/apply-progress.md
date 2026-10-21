# Apply progress: ISS-S3-04

Estrategia: `single-pr` con `size:exception` (3 work units + 2 fixes de CI + 1 de docs). Modo: strict TDD.

## Commits (`git log --oneline 9b85365..HEAD`, del más antiguo al más nuevo)

| Commit | Mensaje | Tipo |
|---|---|---|
| `773b084` | feat(ml): contrato M4 sin metric_id y con bucket_seconds | work unit 1 |
| `e623787` | feat(db): migración 0004 ancla ANOMALY a la serie/bucket | work unit 2 |
| `7c1aa88` | feat(ml): reader HTTP del read path, config y mapper | work unit 3 |
| `c9e8fd5` | fix(tests): omite test del generador cuando numpy no está instalado | fix posterior |
| `c4abaa3` | fix(tests): agrega numpy a dev para verificar el generador en CI | fix posterior (deja el test sin skip) |
| `f4369e3` | docs(openspec/changes/ISS-S3-04): corrige referencias a ISS-S3-05 (#44) | docs |

ADR-0008 se entregó antes, en `9b85365` (commit base del rango).

## Estado de tareas

| Tarea | Estado | Nota |
|---|---|---|
| 1.1 a 1.6 | Hecha | Contrato M4 en `schemas.py`, `mock_data.json`, generador, `ContratoEntradaSalida.md`; sin `metric_id` en `src/ml` |
| 2.1 a 2.4 | Hecha | Migración `0004` + tests de constraints/guard/DDL; `ddl_v1.0.sql` actualizado |
| 3.1 a 3.6 | Hecha | `config.py`, `mapper.py`, `api_reader.py`, `httpx` movido a runtime; pylint 9.61 |
| V2, V3, V4, V5, V6, V9, V10 | Ejecutadas y OK | ver `verify-report.md` |
| V1, V7, V8 | No ejecutadas | pendiente en CI / máquina con Docker |

## Desviaciones

- `numpy>=1.26.0` se agregó a `dev` (no estaba en `tasks.md` 3.5, que decía "sin otras dependencias nuevas"): el test del generador (MLD-1.3) lo necesita; primero se probó un skip condicional (`c9e8fd5`) y luego se optó por la dependencia (`c4abaa3`). Cambio justificado, no registrado en tasks.
- `read_dataset` recibe un parámetro extra `now` (inyectable) no listado en el design; mejora la testabilidad.
- Se agregó `http_retries` y `http_timeout_seconds` a config (6 variables del design) sin cambios de contrato.
- Discrepancia MLD-8 (spec vs design) resuelta: la spec ahora dice fail-fast.
- ARCH-AI-1/2 (`containers.md`, `interfaces.md`): follow-up declarado, no implementado.
- Los tests y el código llegaron en el mismo commit por work unit: el orden RED/GREEN no es auditable desde el historial.
- Warnings abiertos tras verify: W-1 (ventana 7 d con bucket no divisor), W-2 (URL/key vacías), W-3 (asserts débiles). Ver `verify-report.md`.
