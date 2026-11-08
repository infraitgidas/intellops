# ADR 0012: Alerta independiente de la anomalía y lectura app-scoped de anomalías y alertas

- **Estado**: Aceptado
- **Fecha**: 2026-11-08
- **Autores**: Santiago Montanari (esquema revisado con el equipo; afecta a B.14 de Romeo y a B.10)
- **Decisión relacionada**: Issue #68 (B.3), D1, ADR-0003, ADR-0008, `openspec/changes/ISS-B-03/`

## Contexto

B.3 pide exponer la API de lectura app-scoped de series, anomalías y alertas. Las series ya están (`GET /metrics/query`, `/metrics/list` y `/metrics/probes`, ISS-S3-01 y B.13). `/anomalies` y `/alerts` solo existían como stubs del contrato, sin router.

Al revisar el esquema para definir la lectura de alertas aparecieron dos problemas:

- **La tabla `alert` no admite las alertas de la v1.** D1 movió la detección ML a M3: en la v1 las alertas las crea el motor de reglas de umbral (B.14), sin modelo ni anomalía detrás. Pero el DDL 0001 exige `alert.anomaly_id` NOT NULL, y `anomaly.model_id` es NOT NULL con FK a `ml_model`. B.14 tendría que inventar un modelo y una anomalía por cada alerta.
- **A `alert` le faltan datos que la lectura y B.14 necesitan.** No tiene `application_id` (el tenant solo se derivaba con un JOIN a una anomalía que en la v1 no existe), ni `severity` (que B.14 tiene que registrar), ni `created_at` (sin él no hay forma de acotar la ventana ni de ordenar el listado). Además, `recipient` y `channel_id` son NOT NULL, aunque cuando B.14 crea la alerta en Pending el destino todavía no se conoce: lo resuelve el dispatcher de B.10 desde su configuración (los secretos van por variables de entorno).
- **Los schemas del contrato no coinciden con las tablas.** `Anomaly` declaraba `score`, `severity` (enum), `detector`, `description` y `metrics_snapshot`, que la tabla no guarda. `Alert` declaraba `severity` y `created_at`, que la tabla no tenía.

La tabla `alert` está vacía en todos los entornos (nada escribe alertas todavía), así que cambiar su forma ahora es barato.

## Decisión

1. **Migración `0007`: la alerta es independiente de la anomalía.**
   - Agrega `application_id UUID NOT NULL` (FK `fk_alert_application` a `application`, ON DELETE RESTRICT), `severity TEXT NOT NULL` con `ck_alert_severity` (`low`, `medium`, `high`, `critical`) y `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`.
   - Relaja `anomaly_id` (NULL en las alertas de umbral; con valor en las de ML, M3), `recipient` y `channel_id` (los completa B.10 al despachar).
   - Crea los índices del read path newest-first: `idx_alert_app_created (application_id, created_at DESC)` e `idx_anomaly_app_timestamp (application_id, timestamp DESC)`.
   - Como la `0004`, upgrade y downgrade abortan con un mensaje claro si `alert` tiene filas: no hay forma segura de derivar el tenant y la severidad, ni de restaurar los NOT NULL.
2. **`severity` es TEXT con CHECK, no ENUM de Postgres ni catálogo.** Un ENUM es costoso de extender. Un catálogo SMALLINT (como `alert_status` y `alert_channel`) agrega un JOIN o un mapeo sin ganancia: severidad es un dominio cerrado que el contrato expone como string. Si algún día se ordena por severidad, ese orden se mapea en la aplicación, porque TEXT no ordena `low < critical`.
3. **Las columnas propias de las reglas las agrega B.14.** Umbral, valor observado e id de la regla no entran en la `0007`. La migración de B.14 cuelga de esta (`down_revision = "0007"`) para no dejar dos heads en Alembic.
4. **Lectura app-scoped con el mismo patrón que `/metrics/*` y `/sessions`** (ADR-0003):
   - `GET /anomalies`, `GET /anomalies/{anomaly_id}` y `GET /alerts` con `Depends(require_api_key)`. El tenant sale exclusivamente de la key.
   - El detalle filtra por `anomaly_id` **AND** `application_id`: una anomalía de otro tenant da **404** `anomaly_not_found`, igual que una inexistente.
   - Los listados filtran por ventana `[start, end)` (anomalías sobre `detected_at`, alertas sobre `created_at`), con default de 24 h y máximo de 7 días. Ordenan de la más nueva a la más vieja y acotan con `limit` de 1 a 500 (default 50). Filtros opcionales: `metric_type` en anomalías y `status` en alertas.
   - El servicio valida `limit`, la ventana y `status`: cualquier violación responde 422 `invalid_query_range` con el contrato `ErrorResponse`, sin ejecutar la consulta.
5. **La respuesta expone lo que la tabla guarda, sin campos muertos.**
   - `Anomaly`: columnas reales (ancla a la serie y al bucket, ADR-0008) más `metric_name` del catálogo. Los scores se exponen tal como los escribe el detector, sin inventar un mapeo de score a severidad.
   - `Alert`: `status` y `channel` en minúsculas desde los catálogos. **`recipient` no se expone**: es un mail o un chat id, un dato de configuración del dispatcher.
6. **Fuera de alcance:** `/alerts/config` (la configuración de umbrales es de B.14), `/alerts/{id}/ack`, `/predictions*` y `GET /alerts/{id}`, que el contrato no tiene.

## Consecuencias

Positivas:

- B.14 puede crear una alerta de umbral en Pending sin modelo ni anomalía falsos, con tenant, severidad y momento de creación.
- B.10 tiene un estado por alerta (Pending → Sent/Failed con `sent_at`) y completa el destino al despachar, que es cuando lo conoce.
- El aislamiento entre tenants del read path se extiende a anomalías y alertas con la misma regla que ADR-0003, y con índices que evitan el seq scan al paginar.
- El contrato deja de prometer campos que la base no guarda.

Negativas / trade-offs:

- En la v1 `GET /anomalies` devuelve casi siempre `[]`: no hay detector que escriba anomalías hasta M3.
- Una alerta registra un solo canal. Si se despacha por Telegram y por mail, `channel` y `status` reflejan un solo envío. Registrar cada envío por separado necesita una tabla `alert_delivery`, que queda para cuando haga falta (M3).
- No hay paginación por cursor: el cliente acota con la ventana y `limit`.
- Nada impide que una alerta con `anomaly_id` apunte a una anomalía de otro tenant (no hay FK compuesta). La lectura no lo expone, porque solo devuelve el `anomaly_id` y el detalle de la anomalía filtra por tenant. Quien escriba alertas de ML (M3) debe usar la aplicación de la anomalía.

## Alternativas consideradas

### Alternativa 1: mantener el esquema y que B.14 cree un `ml_model` y una anomalía por cada alerta

Descartada. Mezcla detecciones ML con reglas determinísticas en la misma tabla, ensucia el dataset que consume el motor ML en M3 y obliga a inventar `expected_value`, `severity_score` y `confidence_score`.

### Alternativa 2: leer alertas con JOIN a `anomaly` para derivar el tenant, sin migración

Descartada. En la v1 no hay anomalías, así que el listado siempre estaría vacío, y seguiría faltando `created_at` para acotar la ventana.

### Alternativa 3: dejar `recipient` y `channel_id` NOT NULL y que B.14 resuelva el destino al crear la alerta

Descartada. El motor de reglas tendría que conocer chat ids y mails, que son configuración del dispatcher (B.10).

### Alternativa 4: severidad como ENUM de Postgres o como catálogo SMALLINT

Descartada (ver Decisión 2).

## Recursos / Compatibilidad

- **Stack existente**: sin dependencias nuevas.
- **Migración**: la `0007` solo corre sobre `alert` vacía. Su downgrade restaura la forma de 0001.
- **Recursos**: cada consulta es una sola sentencia, acotada por tenant, ventana y `limit` (máximo 500 filas) sobre los índices de la `0007`.
- **Licencias**: sin cambios.

## Referencias

- Issue #68 (B.3), `docs/business/issues-fases-abc.md` §B.3, §B.10 y §B.14
- D1 en `docs/business/brief-v1.md`
- ADR-0003 (ownership de tenant y read path app-scoped) y ADR-0008 (anomalía anclada a la serie)
- `openspec/specs/database/ddl_v1.0.sql` §9 y §10
- `openspec/changes/ISS-B-03/`
