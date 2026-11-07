# B.13 — Sonda HTTP mínima de disponibilidad (issue #73)

Fase B · hito M1 · frente captura · owner Federico · 8 h.
Feature branch: `feat/ISS-B-13`.

## Specs

S1. «Sonda programada a intervalo configurable, ejecutada desde un solo origen.»
S2. «Registro de disponibilidad, código de estado HTTP y latencia por ejecución.»
S3. «Datos enviados por el mismo camino de ingesta y consultables en la API de lectura.»
S4. «Manejo explícito de timeouts y errores de conexión como indisponibilidad.»
S5. «Tests de la sonda y evidencia de una ejecución real contra el sitio piloto.»

Restricciones del issue, literales: «TLS, DNS y multi-origen quedan en R.4 (2027) y no
forman parte de esta issue.» y «Depende de: B.1».

## Decisiones de diseño

- **D1 — Un tipo de métrica nuevo, `AVAILABILITY`, unidad `count`, valor 1/0.** La
  disponibilidad es una razón (`AVG(value)` de 0/1 = uptime del bucket), que es
  exactamente lo que `GET /metrics/query` ya agrega. Reusar un tipo existente
  (`JS_EXCEPTION_RATE`) sería mentir sobre el dominio.
- **D2 — La latencia va como `TTFB`.** La sonda mide tiempo hasta el primer byte de un
  `GET`, que es literalmente TTFB: mismo tipo, misma unidad (`ms`), mismos rangos, y
  queda agregable y comparable con la latencia RUM.
- **D3 — El código de estado HTTP se persiste en `rum_metric.metadata`**
  (`http_status`, `probe_target`, `outcome`). No se modela como métrica porque
  `AVG(404, 200)` no significa nada; el promedio de un código de estado es un error
  conceptual. Se expone por ejecución en `GET /metrics/probes`.
- **D4 — Una sesión sintética estable por target.** La ingesta exige `session_id` UUID
  y `user_session` es por aplicación; la sonda usa un UUID derivado del target
  (uuid5) para no inventar cardinalidad de sesiones.
- **D5 — El contenedor no se agrega.** ADR-0010 fija cuatro contenedores; la sonda se
  entrega como módulo ejecutable (`python -m probe`) y el despliegue se decide en C.5
  junto con el release. No se toca `docker-compose.yml` en este slice.

## Tasks

| ID | Spec | Tarea | Commit |
|----|------|-------|--------|
| T1 | S2 | Contrato: tipo `AVAILABILITY` en OpenAPI, ContratoIngestaRUM y política de ingesta (+ aliases, unidad, rango 0..1) | 1 |
| T2 | S2 | Migración `0006` siembra `metric_type` `AVAILABILITY` + asserts de head en `tests/test_migrations.py` | 1 |
| T3 | S1, S2, S4 | Módulo `src/probe/`: config por entorno, corrida de sonda (latencia, status, disponibilidad, timeout/errores de conexión) | 2 |
| T4 | S1, S3 | Cliente de ingesta de la sonda: arma el batch `RumEventBatch` y lo envía por `POST /telemetry/metrics` con API key | 2 |
| T5 | S1 | Scheduler de intervalo configurable + entrypoint (`python -m probe`) y logging | 2 |
| T6 | S3 | `GET /metrics/probes`: corridas de la sonda por tenant (timestamp, target, status, latencia, disponibilidad) | 3 |
| T7 | S5 | Tests de la sonda (timeout, error de conexión, 5xx, éxito) + verificación del read path | 2, 3 |
| T8 | S5 | Evidencia de una ejecución real contra el sitio piloto | 4 |

## Criterios de aceptación (issue #73)

- [x] Sonda programada a intervalo configurable, ejecutada desde un solo origen.
- [x] Registro de disponibilidad, código de estado HTTP y latencia por ejecución.
- [x] Datos enviados por el mismo camino de ingesta y consultables en la API de lectura.
- [x] Manejo explícito de timeouts y errores de conexión como indisponibilidad.
- [ ] Tests de la sonda y evidencia de una ejecución real contra el sitio piloto.

## Log

- **L1** (03/11/2026): «sigue con b13 completo».
- **L2** (03/11/2026): el owner preguntó por el sitio piloto para la corrida real (S5) y
  no respondió todavía; T8 queda pendiente de esa URL. Todo lo demás se implementa con
  target configurable por `PROBE_TARGET_URL`.
- **L3** (03/11/2026): hallazgo de exploración — el contrato vigente acepta exactamente
  cinco tipos de métrica (`TTFB`, `FCP`, `XHR_LATENCY`, `JS_EXCEPTION_RATE`,
  `RAGE_CLICK`), el catálogo `metric_type` se siembra en la migración `0001` y el
  repositorio de ingesta resuelve el tipo contra ese catálogo cacheado. Sin un tipo
  nuevo no hay forma de registrar disponibilidad como métrica agregable (D1).
- **L4** (03/11/2026): hallazgo — `GET /metrics/query` solo devuelve `AVG(value)` y
  `COUNT(DISTINCT session_id)` por bucket; no hay forma de leer `metadata` por el read
  path existente. De ahí D3 + T6.
- **L5** (03/11/2026): slices de entrega. El candidato completo son ~875 líneas
  autoradas en 3 commits (`dcbfa58` doc ODD, `52e26c6` contrato + catálogo, `cc855f1`
  sonda). Ese volumen pasa el límite de ~400 líneas por slice, así que el límite queda
  acá: contrato+catálogo y sonda son el **slice 1**, y `GET /metrics/probes` (T6) es el
  **slice 2** con su propio commit. Si el PR crece más, se encadena por slice
  (`chained-pr`) en lugar de empujar todo junto.
- **L6** (03/11/2026): la migración `0006` y los asserts de head se verifican contra
  Postgres real en un proyecto docker aislado (`intellops_b13_mig`), para no depender de
  la base local ni ensuciar la del worker del read path. Corrido: 18 passed.
- **L7** (03/11/2026, owner): «con respecto a la url, como el objetivo seria que la
  persona ingrese la url del sitio del que se recuperan los datos creo que lo mejor sera
  que me pases un instructivo con los pasos para preparar el sitio siendo un usuario de
  nuestra aplicacion». Entregado `docs/guias/preparar-sitio-piloto.md` (S5 pasa a
  ejecutarse con el target que el usuario elija). **Decisión abierta**: hoy el target es
  por despliegue (`PROBE_TARGET_URL`); el alta autoservicio de la URL por aplicación es
  un cambio de producto que excede B.13 y queda registrado como pendiente en la sección
  7 del instructivo. No se implementa sin decisión del owner.
- **L8** (03/11/2026, review nativa): el grupo de 4 lentes corrió sobre el candidato
  congelado `d0141dd` y levantó 6 hallazgos severos, todos `introduced` por este
  cambio y todos aceptados:
  - `R1-001`/`R3-001`/`R4-005` (CRITICAL/BLOCKER): la sesión sintética se derivaba
    solo del target, así que dos tenants que miden el mismo sitio compartían
    `session_id` —PK de `user_session`, cuya dueña es la aplicación— y las métricas
    se atribuían o se descartaban al otro tenant. Corregido: derivación de
    `(sha256(api_key), target)`.
  - `R3-002`/`R4-001` (CRITICAL): `client.get` leía el body completo antes de medir,
    así que la latencia era tiempo total y no TTFB, y un body lento podía registrar
    `timeout` en un sitio arriba. Corregido: `client.stream`, medición al recibir
    headers, body nunca leído.
  - `R3-003` (CRITICAL): `send_batch` pasaba `timeout=None` y desactivaba el timeout
    del cliente, colgando el ciclo si la ingesta no responde. Corregido: timeout
    acotado por default.
  Corrección commiteada en `0c9e669` (154 diff lines sobre el candidato congelado,
  dentro del budget de 200).
- **L9** (03/11/2026, bloqueo de la review nativa): declarar el plan de corrección
  falla con `review_authority_newer_release`: la autoridad la escribió un `gentle-ai`
  más nuevo (campo `lens_selection_reason`) y el binario del `PATH` es 3.7.0, que no
  puede parsearla (`/home/federico/go/bin/gentle-ai` es 2.6.0, todavía más viejo). El
  grupo de reviewers sí corrió porque lo ejecuta el build de la extensión. Remedio que
  imprime el propio provider: actualizar el `gentle-ai` que resuelve el `PATH` al build
  que escribió la autoridad. Decisión del owner: es mantenimiento de entorno.
- **L10** (03/11/2026, evidencia de ejecución real, S5): target del owner
  `https://inns-officials-singles-green.trycloudflare.com/login`. Tres ciclos reales de
  `python -m probe` contra la API local:
  `outcome=ok http_status=200 latency_ms=289.194 / 272.217 / 277.669 ingest_status=202`.
  Consultable por el read path: `GET /metrics/query` AVAILABILITY → `value: 1.0` (uptime
  del bucket) y TTFB → `279.69` ms; `GET /metrics/probes?limit=5` → 200 con las tres
  corridas, la más nueva primero, `target`, `http_status`, `outcome`, `latency_ms` y
  `available` mapeados desde `metadata`.
  Alta hecha por la API pública (login → `POST /applications` → `POST .../api-key`) tras
  restaurar el usuario seed `admin@intellops.local` que la migración `0002` declara y que
  faltaba en la base de desarrollo (la tabla `lab_user` estaba vacía). Sin cambios de
  código por esto.
- **L11** (03/11/2026, verificador independiente): S1-S4 `pass` con evidencia de
  sockets reales (headers rápidos + body lento no leído, timeout a 400 ms contado,
  puerto cerrado y host inválido como `connection_error`, redirect no seguido,
  dos tenants con sesiones distintas). Los 6 hallazgos de la review: 6/6
  corregidos, probado contra `git show cc855f1`. Encontró además 5 defectos
  propios, corregidos en `498a1df`: (1) un TTFB sobre el tope de cordura hacía
  rechazar el evento entero y se perdía la disponibilidad; (2)
  `PROBE_APPLICATION_ID` no-UUID descartaba el evento; (3) el log decía 202 aunque
  se aceptaran 0 eventos; (4) el downgrade de `0006` reventaba con
  `RestrictViolation` una vez usada la métrica; (5) fila de tabla huérfana en este
  doc, bullets pegados y el 503 del instructivo recomendando bajar el intervalo.
  S5 quedó `pending` en su corrida (no tenía la URL); cubierto por L10.
- **L12** (03/11/2026, cierre de verificación): suite completa en docker con Postgres 16
  efímero sobre el commit final: **460 passed + 1 xpassed** (21.92 s), alembic a head
  incluido. Cobertura de la feature: 17 tests de la sonda, 20 de migraciones, contrato y
  read path verdes. En el host queda una única falla ambiental conocida y ajena:
  `tests/test_ml_worker.py` por `numpy` ausente en `.venv`.
