# ADR 0011: Sesiones RUM — creadas por la ingesta, expuestas en solo lectura y sin campos muertos

- **Estado**: Aceptado
- **Fecha**: 2026-11-08
- **Autores**: Santiago Montanari (decisión de alcance acordada con Federico Cavallero)
- **Decisión relacionada**: Issue #42 (ISS-S3-03), ADR-0002, ADR-0003, `openspec/changes/ISS-S3-03/`

## Contexto

La issue #42 pide "la gestión de sesiones necesaria para relacionar actividad RUM con aplicaciones y usuarios cuando corresponda". El EDT detalla `POST /sessions`, `POST /sessions/{id}/finish` y `GET /sessions/{id}` (`docs/business/EDT intellops.md:535-539`). Desde que se escribió, la implementación avanzó:

- **La ingesta ya crea la sesión en el primer evento.** El worker inserta `user_session` con `ON CONFLICT (session_id) DO NOTHING`. `app_id` sale de la aplicación autenticada por la API key, nunca del payload (ADR-0002, `src/api/infrastructure/ingest/queue.py:253-263`). Así, cada métrica y excepción queda ligada a una sesión y, por la sesión, a su aplicación.
- **El agente no reporta el fin de la sesión.** Rota el `session_id` tras 30 minutos de inactividad o 24 horas de vida, sin avisar al servidor (`docs/architecture/ContratoAgenteRUM.md:29,31`).
- **El agente no envía identidad de usuario ni IP.** El `session_id` es un UUID opaco, sin user ID ni email, y la IP está prohibida (`ContratoAgenteRUM.md` §9).
- **El DDL tiene columnas que nadie escribe.** `user_session` define `user_id` (FK a `lab_user`), `ip_address`, `os_version`, `end_timestamp` y `duration_ms` (`openspec/specs/database/ddl_v1.0.sql:131-140`), pero la ingesta solo escribe `session_id`, `app_id`, `user_agent` y `start_timestamp`. La Trazabilidad DER a Contenedores asigna al Core "Insert / Update" de `USER_SESSION` y dice que "calcula la duración al cerrarse".
- **Faltaba la lectura.** No existía forma de leer sesiones: la única señal era `session_count` agregado en `GET /metrics/query`.

## Decisión

1. **Sin endpoints de escritura.** No se implementan `POST /sessions` ni `POST /sessions/{id}/finish`. Crear sesiones duplicaría lo que ya hace la ingesta. Cerrarlas desde el cliente rompería el contrato del agente v0.1, que no tiene evento de fin. Un cierre reportado por el cliente exige primero una nueva versión del contrato (`schema_version` 1.1).
2. **`user_id`, `ip_address` y `os_version` quedan siempre NULL en la ingesta, y nunca se toman del payload**, aunque `metadata` traiga claves con esos nombres:
   - `user_id` apunta a `lab_user`, que son los investigadores de la plataforma, no los usuarios finales del sitio monitoreado. Los usuarios finales son anónimos por diseño.
   - La IP está prohibida por la política de privacidad del agente.
   - `os_version` no forma parte del contrato.

   La "relación con usuarios cuando corresponda" de #42 no corresponde en v1: la actividad RUM se relaciona con la **aplicación**, a través de la sesión.
3. **`end_timestamp` y `duration_ms` quedan NULL en v1.** Sin evento de fin, el servidor no sabe cuándo terminó una sesión. El cierre por inactividad del lado del servidor (un proceso que complete `end_timestamp` y `duration_ms` pasados 30 minutos sin actividad) se trata en una issue aparte. Es la diferencia documentada respecto del "Insert / Update" de la Trazabilidad DER.
4. **Lectura app-scoped con el mismo patrón que `/metrics/*`** (ADR-0003):
   - `GET /sessions` y `GET /sessions/{session_id}` con `Depends(require_api_key)`. El tenant se deriva exclusivamente de la key y no existe parámetro de aplicación en el request.
   - `GET /sessions/{session_id}` filtra por `session_id` **AND** `app_id`, no solo por la clave primaria. Una sesión de otra aplicación responde **404** `session_not_found`, igual que una inexistente. Un 403 confirmaría que la sesión existe bajo otro tenant.
   - `GET /sessions` filtra por `start_timestamp` en `[start, end)`, ordena de la más nueva a la más vieja y acota con `limit` 1..500 (default 50). La ventana default es de 24 h, la vida máxima de una sesión en el agente, con un máximo de 7 días como TQ-2. Una violación responde 422 `invalid_query_range` sin ejecutar la consulta.
5. **La respuesta no expone campos muertos.** El schema `Session` no incluye `user_id`, `ip_address`, `os_version`, `end_timestamp` ni `duration_ms`. Mostrar campos que siempre valen `null` sugiere una funcionalidad que no existe. Además, cuando el cierre por inactividad los rellene, `null` cambiaría de significado ("no lo calculamos" pasaría a ser "sesión abierta") sin que ningún test de contrato lo detecte. Agregarlos cuando tengan datos es un cambio compatible; quitarlos después no lo sería.
6. **Actividad observada en lugar de cierre.** La respuesta incluye `metric_count`, `exception_count` y `last_activity_at`. Este último es el timestamp más reciente entre las métricas y excepciones de la sesión: un dato real, calculado en SQL al consultar. No se llama "fin" ni "duración" porque no afirma que la sesión haya terminado.

## Consecuencias

Positivas:

- #42 tiene un entregable visible y verificable sin tocar la ingesta, sin migración y sin cambiar el contrato del agente.
- El aislamiento entre tenants del read path se extiende a sesiones con la misma regla que ADR-0003.
- El contrato de la API no promete datos que el servidor no registra.

Negativas / trade-offs:

- La duración de una sesión no está disponible como dato persistido. `last_activity_at - start_timestamp` sirve como aproximación, pero es una cota inferior: no ve la actividad que el agente no reporta.
- `GET /sessions` filtra por `start_timestamp`. Una sesión que empezó antes de la ventana y sigue activa dentro de ella no aparece. Es el comportamiento documentado; se revisa si el dashboard lo necesita.
- No hay paginación por cursor: el cliente acota con la ventana y `limit`.
- El DER sigue declarando "Insert / Update" para `USER_SESSION`. El Update queda pendiente de la issue del cierre por inactividad.

Riesgos:

- Hay un límite heredado de ADR-0003: si dos tenants mandan el mismo `session_id` **nuevo** en el mismo chunk, la colisión no se detecta. La lectura nunca mezcla tenants, porque la sesión tiene un único `app_id` y la consulta filtra por él. Las filas del tenant perdedor siguen ligadas a la sesión del ganador, como antes de este cambio.

## Alternativas consideradas

### Alternativa 1: implementar `POST /sessions` y `POST /sessions/{id}/finish` como pide el EDT

Descartada. La creación duplicaría la de la ingesta y abriría una segunda vía de alta con sus propios casos de borde de ownership. El cierre por el cliente no tiene respaldo en el contrato del agente v0.1. Implementarlo implicaría un endpoint sin consumidor o un cambio de contrato fuera del alcance de la issue.

### Alternativa 2: exponer `end_timestamp` y `duration_ms` como nullable

Descartada. Son campos que siempre valen `null` en v1, y su `null` cambiaría de significado cuando exista el cierre por inactividad (ver Decisión 5).

### Alternativa 3: cerrar sesiones por inactividad del lado del servidor en esta issue

Pospuesta, no descartada. Requiere un proceso periódico (sweep) o un `ON CONFLICT DO UPDATE` en la ingesta, decidir qué pasa con eventos fuera de orden o reintentos y respetar el ownership. No entra en la estimación de 6 h de #42 y va en una issue propia.

### Alternativa 4: asociar `lab_user` a la sesión (por ejemplo, con un `setUser()` en el agente)

Descartada para v1. Contradice la política de privacidad del agente (sin identidad de usuario) y confunde a los investigadores de la plataforma con los usuarios finales del sitio monitoreado.

## Recursos / Compatibilidad

- **Stack existente**: sin dependencias nuevas, sin migración y sin cambios en el agente ni en la ingesta.
- **Recursos**: cada consulta es una sola sentencia. Primero acota las sesiones del tenant y después cuenta su actividad con `LATERAL` sobre los índices existentes `idx_user_session_app_id`, `idx_rum_metric_session_timestamp` e `idx_js_exception_session_timestamp`. Uso de memoria acotado por `limit` (máximo 500 filas).
- **Licencias**: sin cambios.

## Referencias

- Issue #42 (ISS-S3-03) y `docs/business/issues-s2-s3.md`
- ADR-0002 (pipeline de ingesta) y ADR-0003 (ownership de tenant y read path app-scoped)
- `docs/architecture/ContratoAgenteRUM.md` §2.1 y §9
- `openspec/specs/database/ddl_v1.0.sql:131-140`
- `openspec/changes/ISS-S3-03/`
