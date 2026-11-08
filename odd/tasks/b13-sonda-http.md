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
- **L13** (07/11/2026, correcciones de review de la PR #88, comentario de RomeKai):
  cuatro arreglos test-first (RED → GREEN, 7 tests nuevos, 24/24 de la sonda y
  suite completa **466 passed + 1 xpassed**; única falla la ambiental conocida de
  `numpy`). (3) Un status de ingesta no-2xx (401 por API key mala, 422) se loguea
  como WARNING aunque `accepted` no se pueda leer: la sonda mal configurada ya no
  parece sana. (4) `cycle()` atrapa cualquier excepción, no solo `httpx.HTTPError`:
  un error inesperado (p. ej. de `build_batch`) se registra con stack trace y el
  próximo ciclo reintenta, el proceso no muere. (5) El scheduler ancla el ritmo a
  `time.monotonic()` y duerme intervalo − duración del ciclo (recortado a cero):
  el período real es el intervalo y los buckets no quedan con 0 o 2 muestras.
  (6) `probe_target` se persiste y se loguea saneado (sin query string, fragmento
  ni credenciales): un token en la URL del target no queda guardado ni expuesto.
  Doc de arquitectura actualizada en los cuatro puntos.
- **L14** (07/11/2026, hallazgos informativos de la review nativa): la review
  aprobada de la PR #88 dejó 12 hallazgos no bloqueantes (0 correcciones
  abiertas). El texto de los reviewers no era recuperable — la autoridad era
  `compact-v2` y quedó quemada al acknowledgear —, así que cada hallazgo se
  reconstruyó desde su id/lente/ubicación contra el árbol congelado (`674676d`,
  idéntico al árbol de HEAD). Seis defectos reales, test-first (5 RED, 43/43 en
  sonda + read path, suite completa **473 passed + 1 xpassed**, única falla la
  ambiental de `numpy`; `pylint src/probe/` 10.00/10):
  (1) `sanitize_target_url` — R1-002/R2-003/R3-002/R4-002: el fallback (URL que
  `urlsplit` no entiende) era más débil que el camino principal y conservaba
  `user:pass@`, justo lo que la función existe para no persistir. Un solo saneo
  para ambos caminos.
  (2) `_validate_url` — R4-001/R3-003: validar solo el prefijo dejaba pasar
  `http://`, `https:// ` y puertos no numéricos; la sonda arrancaba y perdía
  cada corrida. Ahora exige esquema `http(s)` + host no vacío + puerto válido al
  construir.
  (3) `_as_float` — R1-001/R3-001: `float("nan")`/`float("inf")` no lanzan, así
  que un `metadata.latency_ms` corrupto entraba como NaN al dominio. El endpoint
  lo tapaba (pydantic serializa NaN como `null` en JSON — hay test que lo fija
  como comportamiento previo), pero violaba el contrato del helper y cualquier
  consumidor de `ProbeRun` recibía un no-número. Se rechaza lo no finito.
  (4) `_log_startup` — R1-003: el arranque saneaba el target pero no
  `INGEST_BASE_URL`, que es igual de configurable y puede traer userinfo o token.
  (5) `run_cycle` — R4-003: si `send_batch` fallaba, `_log_result` nunca corría y
  la medición ya tomada no quedaba registrada. Ahora se registra con
  `ingest_status=unknown` antes de propagar el error.
  (6) docstring D4 — R2-001: decía "derivado del target" cuando la sesión se
  deriva de (tenant, target).
  Doc de arquitectura actualizada en los cuatro comportamientos observables.
  Endurecimiento posterior del mismo slice (hallado al atacar el arreglo 1 con
  URLs adversariales): en el fallback el userinfo se quita PRIMERO, porque
  recortar el query antes partía el userinfo (`user:pa?ss@host` quedaba como
  `https://user:pa`, un pedazo de la contraseña persistido), y el camino
  principal repone los corchetes de IPv6 (`hostname` viene sin ellos y
  `urlunsplit` no los agrega). 15/15 casos adversariales sin fuga; 45/45 en
  sonda + read path, suite completa **475 passed + 1 xpassed**; differential
  contra `e28b04b`: único diff, el arreglo IPv6.
- **L15** (07/11/2026, hallazgos de la segunda review nativa): la review
  `review-e7da28ac` (candidato `21fa6d2`) aprobó con 11 hallazgos informativos.
  Se compararon con los de la review anterior: 7 de los 12 previos desaparecieron
  (el read path y `__main__.py` quedaron sin hallazgos), 1 se repitió
  (`get_probe_settings`) y 6 eran nuevos. Los 6 nuevos + el repetido, corregidos
  test-first (6 RED, 50/50 en sonda + read path, suite completa **480 passed +
  1 xpassed**, única falla la ambiental de `numpy`; `pylint` 10.00/10):
  (1) `scheduler.py` — R3-001/R4-001: `next_tick += intervalo` sin acotar; si un
  ciclo se pasa del intervalo el atraso se acumula y la espera queda en 0 para
  siempre (bucle sin pausa). Ahora se resincroniza el reloj monotónico.
  (2) `sanitize_target_url` — R2-001/R3-004: sin `esquema://` no hay authority,
  así que un `@` en el path es parte del path; recortarlo lo mutilaba
  (`host.com/user@example.com/p` quedaba `example.com/p`). La forma
  scheme-relative sí se sanea.
  (3) `ProbeSettings` — R4-003: `extra="ignore"` se tragaba los typos, y `extra`
  tampoco ve un env var mal escrito (pydantic-settings solo lee los campos
  declarados). Se rechaza al construir cualquier `PROBE_*`/`INGEST_*` que no
  corresponda a un campo.
  (4) `send_batch` — R3-002: `base_url.rstrip('/')` pegaba el path de ingesta
  detrás del query del base. Ahora se arma con path + `urlunsplit`, conservando
  un prefijo `/v1` y descartando query/fragmento.
  (5) `query_service.list_probe_runs` — R2-002: el 422 decía el rango pero no el
  valor rechazado, así que no se sabía si se mandó 0 o 501.
  (6) `get_probe_settings` — R2-003 (la SUGGESTION repetida): decía ser el
  singleton del proceso y `main()` lo saltaba construyendo otro `ProbeSettings`.
  Ahora `main()` la usa.
  Differential contra `21fa6d2`: únicos diffs, el path con `@` y el query del
  base; todo lo demás idéntico.
