# SPEC — database (Modificada) — ISS-S3-04

**Tipo**: Delta spec. **Cambio**: ISS-S3-04 (GitHub #43). **Base**: `proposal.md` (D2 = M4), `openspec/specs/database/ddl_v1.0.sql:258-277` (`anomaly`), migraciones Alembic en `src/api/infrastructure/db/migrations/versions/` (última `0003_is_active.py`).
**Alcance**: `ANOMALY` se ancla a la serie/bucket; sin FK a `rum_metric`; índice único para reproceso idempotente; migración `0004` reversible condicionalmente; `ddl_v1.0.sql` alineado. Sin cambios en `src/api` fuera de la migración.

---

## MODIFIED Requirements

### Requirement: DB-ANOM-1 (ANOMALY ancla a la serie/bucket)

La tabla `anomaly` DEBE agregar las columnas: `application_id` (UUID, NOT NULL, FK a `application.app_id`), `metric_type_id` (SMALLINT, NOT NULL, FK a `metric_type`), `bucket_start` (TIMESTAMPTZ, NOT NULL) y `bucket_seconds` (INT, NOT NULL, `CHECK (bucket_seconds >= 60)`). La columna `timestamp` DEBE conservarse con el significado de instante de detección; NO DEBE renombrarse. (Traceability: proposal Approach "Columnas nuevas"; pregunta 1.)

> Nota de tipos: los tipos de `application_id` y `metric_type_id` DEBEN coincidir con los de `application.app_id` y `metric_type.metric_type_id` en el DDL vigente; lo escrito aquí es el contrato lógico.

#### Scenario: DB-ANOM-1.1 Inserción válida
- GIVEN una app y un `metric_type` existentes
- WHEN se inserta una anomalía con `application_id`, `metric_type_id`, `bucket_start`, `bucket_seconds = 60` y `timestamp`
- THEN la inserción es exitosa

#### Scenario: DB-ANOM-1.2 bucket_seconds bajo el mínimo
- GIVEN una anomalía con `bucket_seconds = 30`
- WHEN se inserta
- THEN falla por violación del `CHECK`

#### Scenario: DB-ANOM-1.3 FK de aplicación inexistente
- GIVEN un `application_id` que no existe en `application`
- WHEN se inserta la anomalía
- THEN falla por violación de FK

#### Scenario: DB-ANOM-1.4 timestamp como detección
- GIVEN una anomalía detectada en `T` sobre el bucket `B`
- WHEN se persiste
- THEN `timestamp = T` y `bucket_start = B` son valores independientes

### Requirement: DB-ANOM-2 (sin vínculo a rum_metric)

`anomaly` NO DEBE contener la columna `metric_id` ni la constraint `fk_anomaly_metric`. La anomalía referencia la serie/bucket, no una fila física de `rum_metric`. (Traceability: D2 = M4; decisiones §3.4.)

#### Scenario: DB-ANOM-2.1 Esquema sin metric_id
- GIVEN la base migrada a `0004`
- WHEN se inspecciona `anomaly`
- THEN no existe la columna `metric_id` ni `fk_anomaly_metric`

#### Scenario: DB-ANOM-2.2 Borrado de rum_metric
- GIVEN una anomalía anclada a una serie
- WHEN se eliminan filas de `rum_metric` de esa serie
- THEN la anomalía no se ve afectada por la ausencia de FK

### Requirement: DB-ANOM-3 (unicidad e idempotencia de reproceso)

DEBE existir un índice único sobre `(application_id, metric_type_id, bucket_start, bucket_seconds, model_id)`. Reprocesar el mismo bucket con el mismo modelo NO DEBE crear una segunda fila: el escritor DEBE usar upsert/`ON CONFLICT` sobre esta clave. Un bucket evaluado por un `model_id` distinto DEBE poder coexistir. (Traceability: pregunta 4.)

#### Scenario: DB-ANOM-3.1 Duplicado
- GIVEN una anomalía existente para `(A, T, B, 60, M)`
- WHEN se inserta otra con la misma tupla
- THEN se rechaza por violación de unicidad (o el upsert no crea fila nueva)

#### Scenario: DB-ANOM-3.2 Otro modelo
- GIVEN una anomalía para `(A, T, B, 60, M1)`
- WHEN se inserta una para `(A, T, B, 60, M2)`
- THEN ambas coexisten

#### Scenario: DB-ANOM-3.3 Otro bucket_seconds
- GIVEN una anomalía para `(A, T, B, 60, M)`
- WHEN se inserta una para `(A, T, B, 300, M)`
- THEN ambas coexisten

### Requirement: DB-MIG-1 (migración 0004)

DEBE existir la migración Alembic `0004` (revisión padre `0003`) en `src/api/infrastructure/db/migrations/versions/` que: (up) elimine `fk_anomaly_metric` y la columna `metric_id`, agregue las columnas de DB-ANOM-1 y cree el índice único de DB-ANOM-3; (down) elimine el índice y las columnas nuevas y restaure `metric_id UUID NOT NULL` con `fk_anomaly_metric` (`ON DELETE RESTRICT`). El downgrade SOLO es válido con `anomaly` vacía: DEBE fallar de forma explícita (sin truncar ni inventar valores) si hay filas. (Traceability: proposal In Scope §2; riesgo "Downgrade no reversible".)

#### Scenario: DB-MIG-1.1 Upgrade
- GIVEN una base en `0003`
- WHEN se ejecuta `alembic upgrade 0004`
- THEN `anomaly` tiene las columnas nuevas, el índice único y no tiene `metric_id`

#### Scenario: DB-MIG-1.2 Downgrade con tabla vacía
- GIVEN una base en `0004` con `anomaly` vacía
- WHEN se ejecuta `alembic downgrade 0003`
- THEN `anomaly` recupera `metric_id NOT NULL` y `fk_anomaly_metric`, y no quedan las columnas ni el índice nuevos

#### Scenario: DB-MIG-1.3 Downgrade con datos
- GIVEN una base en `0004` con al menos una fila en `anomaly`
- WHEN se ejecuta `alembic downgrade 0003`
- THEN la migración falla con un error explícito y el esquema permanece en `0004`

#### Scenario: DB-MIG-1.4 Upgrade con datos preexistentes
- GIVEN `anomaly` vacía en `0003` (nadie la escribe hoy)
- WHEN se ejecuta `upgrade 0004`
- THEN es exitoso sin backfill

### Requirement: DB-DDL-1 (ddl_v1.0.sql alineado)

`openspec/specs/database/ddl_v1.0.sql` DEBE reflejar el estado posterior a `0004` para `anomaly` (columnas, FKs, `CHECK` e índice único; sin `metric_id`). (Traceability: proposal In Scope §2.)

#### Scenario: DB-DDL-1.1 Equivalencia
- GIVEN el DDL actualizado y una base migrada a `0004`
- WHEN se comparan las columnas y constraints de `anomaly`
- THEN coinciden

### Requirement: DB-SCOPE-1 (sin cambios en src/api)

El cambio NO DEBE modificar código de `src/api` fuera del archivo de migración `0004` (ni ingesta, ni read path, ni `openapi.yaml`). (Traceability: proposal Out of Scope.)

#### Scenario: DB-SCOPE-1.1 Diff acotado
- GIVEN el diff del cambio
- WHEN se listan los archivos bajo `src/api`
- THEN el único archivo nuevo o modificado es la migración `0004`

---

## Criterios de aceptación verificables

1. Test de migración up/down (DB-MIG-1.1 a 1.3) contra Postgres.
2. Tests de constraints: CHECK, FK, unicidad (DB-ANOM-1, DB-ANOM-3).
3. `ddl_v1.0.sql` equivalente al esquema migrado (DB-DDL-1).
4. Aviso previo al owner de DB (Santiago) sobre `0004`.
