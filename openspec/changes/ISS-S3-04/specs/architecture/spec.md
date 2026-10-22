# SPEC — architecture (Modificada) — ISS-S3-04

**Tipo**: Delta spec. **Cambio**: ISS-S3-04 (GitHub #43). **Base**: `proposal.md`, `openspec/specs/architecture/containers.md` §2.3/§5.1 y C4, `openspec/specs/architecture/interfaces.md` §2.1, ADR-0003 (read path app-scoped).
**Alcance**: reconciliar la lectura de telemetría del AI engine (HTTP, no DB) con la escritura de `ANOMALY`/`ALERT` (DB), vía ADR-0008. Sin cambios de runtime en `src/api`.

---

## MODIFIED Requirements

### Requirement: ARCH-AI-1 (el AI engine lee telemetría vía HTTP)

El contenedor `intellops-ai-engine` DEBE leer telemetría exclusivamente mediante el read path HTTP (`GET /metrics/query`, autenticado con API key por aplicación), y NO DEBE leer `RUM_METRIC` directamente de la base de datos. La relación "Read batch / RUM_METRIC (read)" hacia DB en `containers.md` §2.3 y el diagrama C4 DEBEN reemplazarse por una relación HTTP hacia `intellops-core`. (Traceability: proposal Capabilities "architecture"; ADR-0003; ADR-0008.)

#### Scenario: ARCH-AI-1.1 Documentación coherente
- GIVEN `containers.md` §2.3/C4 e `interfaces.md` §2.1 actualizados
- WHEN se revisa la relación AI engine → telemetría
- THEN se documenta como HTTP pull del read path y no como lectura directa de `RUM_METRIC`

#### Scenario: ARCH-AI-1.2 Sin acceso directo
- GIVEN el código de `src/ml`
- WHEN se buscan consultas SQL o sesiones de DB contra `rum_metric`
- THEN no existen

### Requirement: ARCH-AI-2 (el AI engine escribe ANOMALY/ALERT en DB)

El AI engine SIGUE escribiendo `ANOMALY` y `ALERT` en la base de datos; esa relación de escritura DEBE mantenerse documentada y distinguirse de la lectura HTTP. Las escrituras de `ANOMALY` DEBEN anclarse a la serie/bucket (capability `database`, DB-ANOM-1) y ser idempotentes (DB-ANOM-3). (Traceability: proposal Capabilities "architecture"; D2 = M4.)

#### Scenario: ARCH-AI-2.1 Relación de escritura vigente
- GIVEN el diagrama C4 actualizado
- WHEN se revisa la relación AI engine → DB
- THEN figura como escritura de `ANOMALY`/`ALERT` y no como lectura de telemetría

### Requirement: ARCH-AI-3 (ADR-0008 y aislamiento de módulos)

DEBE existir `docs/adr/0008-*.md` que reconcilie `containers.md` ("lee `RUM_METRIC` de DB") con ADR-0003 (HTTP) y registre D2 = M4 y D4 = (a). La numeración 0004–0007 queda reservada a PR #59. Se DEBE mantener la regla de `containers.md` §5.1: sin cross-imports entre `intellops-core` e `intellops-ai-engine`; el contrato entre ambos es el read path público. (Traceability: proposal In Scope §6; Risks "Colisión con PR #59".)

#### Scenario: ARCH-AI-3.1 ADR presente
- GIVEN el cambio completado
- WHEN se lista `docs/adr/`
- THEN existe `0008-*.md` con estado y decisión, y no modifica ADR 0004–0007

#### Scenario: ARCH-AI-3.2 Aislamiento
- GIVEN `src/ml` y `src/api`
- WHEN se analizan imports cruzados
- THEN no existen en ninguna dirección

---

## Fuera de alcance

- Cambios de runtime en `src/api` y `openapi.yaml`.
- Archivos de PR #59 (ARCH-5/6, ADR 0004–0007, `CHANGELOG.md`; follow-up post-merge).
- Scheduler y orquestación del pull.

## Criterios de aceptación verificables

1. `containers.md` §2.3/C4 e `interfaces.md` §2.1 reflejan HTTP-read + DB-write.
2. ADR-0008 aprobado y referenciado.
3. Sin cross-imports ni acceso directo a `rum_metric` desde `src/ml`.

## Next recommended

**design** (si no existe) y luego **tasks**.
