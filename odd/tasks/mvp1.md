# MVP1 — Cierre del MVP v1 sobre rama local (B.14, B.10, B.9, B.5 → C.1, C.3, C.5)

Rama: `MVP1`, local, desde `origin/develop` (057d46b) + merges de `origin/b-03` (#92, B.3)
y `origin/s3-06` (#91, ISS-S3-06). No se pushea ni se mergea a `develop` por ahora.
Fuente normativa de los criterios: issues #74, #72, #71, #69, #76, #78 y #80 (catálogo
`docs/business/issues-fases-abc.md`). Se ignoran las asignaciones de owner.

## Specs

### B.14 — Reglas de umbral (#74), Tramo 1

S1. «Umbrales configurables por métrica y por aplicación (latencia, tasa de errores,
disponibilidad de la sonda).»
S2. «`ALERT` creada en estado Pending con severidad y mensaje.»
S3. «Deduplicación o cooldown para evitar alertas repetidas.»
S4. «Tests de reglas y casos borde: sin datos, datos insuficientes, valor exactamente en el
umbral.»
S5. «Integración con B.10 verificada por un test de contrato.»

### B.10 — Notificaciones por mail y Telegram (#72), Tramo 1

S6. «Envío por mail y Telegram operativo.»
S7. «Retry con backoff ante fallos transitorios.»
S8. «`ALERT` pasa de Pending a Sent/Failed con `sent_at`.»
S9. «Secretos por variables de entorno, nunca en código.»
S10. «Tests con proveedores mockeados.»

### B.9 — Quality gates bloqueantes en CI (#71), Tramo 1

S11. «Coverage < 70 % bloquea el PR.»
S12. «Lint con warnings/errores bloquea el PR.»
S13. «OpenAPI/contract inválido bloquea el PR.»
S14. «Gates documentados y verificados con un PR de prueba.»

### B.5 — SPA React: latencias RUM y heatmap UX (#69), Tramo 1

S15. «Dos vistas funcionales contra la API de B.3.»
S16. «Build estático reproducible.»
S17. «Bundle < 1 MB.»
S18. «Estados de carga/error y responsive básico.»
S19. «Tests de componentes y smoke E2E.»

### C.1 — Integración de punta a punta (#76), Tramo 2

S20. «Flujo E2E funcionando en `develop`.»
S21. «Sin conflictos de integración abiertos.»
S22. «Smoke test documentado y reproducible.»
S23. «Demo de punta a punta para el equipo.»

### C.3 — Tests E2E y carga con k6 (#78), Tramo 2

S24. «Suite E2E automatizada en CI.»
S25. «Escenario k6 versionado.»
S26. «Ingesta ≤ 500 ms bajo carga estándar.»
S27. «Reporte de resultados y umbrales.»

### C.5 — Release v1.0 (#80), Tramo 2

S28. «Tag `v1.0.0` creado.»
S29. «`docker compose up` funciona en máquina limpia.»
S30. «Guía de despliegue y rollback documentados.»
S31. «Smoke test post-deploy.»
S32. «Release notes.»

### Restricciones del tramo

S33. «no se van a mezclar por el momento, asi que mvp va a ser local por ahora» — sin push,
sin PRs a `develop`, sin merge a `develop` mientras dure MVP1.
S34. Fuera de alcance: C.2 (acceso al sitio piloto), C.4 (datos reales del piloto), C.6 y C.7
(informes de PPS, autoría humana).
S35. B.10 se verifica contra canales reales con credenciales que aporta el usuario
(`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, SMTP); nunca se commitean, van a `.env`.

## Tasks

| ID | Tarea | Specs | Ruta | Commit |
| --- | --- | --- | --- | --- |
| T0 | Rama MVP1 + merges de las PRs abiertas de Santiago | S33 | inline | 7eb68a1 (merges) |
| T1 | Motor determinístico de reglas de umbral y `ALERT` Pending | S1–S5 | inline + worker, test-first | cd7a182, bcf1e87, fbc50ee, 0061877, 955ba88, 5bbe050, 31ec509 |
| T2 | Dispatcher de notificaciones mail + Telegram con retry/backoff | S6–S10, S5 | worker + inline, test-first | 6ad623b, 1814b2f, 98a7030, d11a64b (bloqueado: `.env.example` y verificación real de S6) |
| T3 | Quality gates bloqueantes en CI (coverage, lint, contrato) | S11–S14 | inline | 7ad824d, 1104d43, 00a936a, 196f424, 5430842, c237abf |
| T4 | SPA React: vistas de latencias RUM y heatmap UX | S15–S19 | worker×2 + inline, test-first | 9e1ccc1, c934f78, 60c945f, 0ef44f3 |
| T5 | Integración E2E del flujo completo | S20–S23 | worker + inline | 10419a6, 6a58a3e, f8244b6, 63536d0, f9aea30, d86961f |
| T6 | Suite E2E automatizada + escenario k6 ≤ 500 ms | S24–S27 | inline | pendiente |
| T7 | Release v1.0: tag, compose, guía de despliegue y notes | S28–S32 | inline | pendiente |

Orden por dependencia: T1 (alerta) → T2 (despacho de esa alerta) → T3 (gates antes de la SPA)
→ T4 (SPA) → T5 → T6 → T7.

## Log

L1 (2026-11-18, verbatim): «quiero hacer algo, ignoremos las asignaciones, hagamos una rama
nueva con los cambios que hizo santiago en las pr abiertas y hagasmos en la rama nueva que le
prondremos MVP1 todo lo necesario para el mvp tal como esta estipulado»

L2 (2026-11-18, decisiones del usuario): "Solo dentro de MVP1, develop no se toca" para #92 y
#91; alcance "Fase B primero, Fase C encadenada"; "no se van a mezclar por el momento, asi que
mvp va a ser local por ahora" para la llegada a `develop`; credenciales de Telegram y SMTP
aportadas por el usuario cuando se necesiten.

L3 (2026-11-18, evidencia): merge de `origin/b-03` y `origin/s3-06` sobre `origin/develop`
entra sin conflictos (solo `CHANGELOG.md` auto-mergeado). `git diff --shortstat origin/develop`
= 48 archivos, +4910/−55. Estado en `MVP1`: 7eb68a1.

L4 (2026-11-18, hallazgo): `/dashboard/summary` y `/dashboard/heatmap` existen solo en
`openspec/specs/openapi.yaml` como stubs sin parámetros ni schemas, y ninguna issue del catálogo
A/B/C/R las implementa. El heatmap de B.5 (S15) se arma sobre `GET /metrics/query`
(`application_id, metric_type_id, timestamp, value, session_count`, bucket ≥ 60 s) +
`GET /metrics/list` + `GET /metrics/probes`, sin backend nuevo.

L5 (2026-11-18, frontera de slices T1): la rama acumula 7760 líneas desde `origin/develop` por
los merges de Santiago; esa base NO es una slice de este trabajo. Las slices propias de B.14 son,
por commit: docs del cambio (`cd7a182`), esquema `0008` + espejos + DDL + tests de migración
(`bcf1e87`), API de configuración con sus tests (`fbc50ee`) y contrato OpenAPI + arquitectura
(`0061877`). Evidencia: 813 passed, 1 xfailed, 1 xpassed; lint 9.95/10; 39/39 en
`test_migrations.py`. La slice del motor (`src/ml/rules/`) se delega a un worker con superficies
`src/ml/rules/`, `src/ml/entrypoint.py` y tres archivos de test.

L6 (2026-11-18, T1 cerrado): siete commits. Evidencia final: 843 passed + 1 xfailed + 1 xpassed,
lint 9.94/10, 39/39 en `test_migrations.py`. El empaquetado de la imagen del `ai-engine` era un
hueco real: copiaba solo `entrypoint.py` y el motor importa `ml.rules` como top-level. Se reescribió
`src/ml/Dockerfile`, se ancló con `tests/test_ai_engine_container.py` y se verificó construyendo la
imagen y corriéndola contra la base de test: build, imports, migración, seis ciclos a intervalo de
2 s y apagado ordenado por SIGTERM. Dos correcciones de diseño: `RAGE_CLICK` se agrega por p95
(la spec es normativa y el diseño decía AVG) y el observado se cuantiza a 6 decimales para que la
comparación inclusiva no falle por la interpolación de `percentile_cont` sobre `float8`.

L7 (2026-11-18, T2 bloqueado): cuatro commits con el dispatcher, el contrato con B.14, el
empaquetado de `intellops-comms` y la documentación. Evidencia: 889 passed + 1 skipped + 1 xfailed
+ 1 xpassed, lint 9.91/10. Prueba de contenedor: build de `src/comms/Dockerfile`, arranque contra
la base de test (`channels=none`), aviso único por canal, ciclos `claimed=0 sent=0 failed=0`,
`docker stop` con exit 0, y una alerta real que quedó `Pending` sin destinatario (no `Failed`).
Corrección del padre sobre el handoff: `mark_failed` ahora persiste `channel_id` y `recipient` del
intento y deja `sent_at` NULL; sin eso una alerta fallida no se podía diagnosticar ni distinguir
de una que nadie intentó despachar. Quedan abiertos dos puntos que dependen del usuario:
`.env.example` está bloqueado por la política de rutas sensibles (el worker y el padre fueron
rechazados), y S6 («envío por mail y Telegram operativo») necesita credenciales reales.

L8 (2026-11-18, T3 cerrado): seis commits (árbol → workflow + Makefile → pin → documentación).
Estado inicial medido en un worktree detached de `ac10991` montado en el contenedor de testing
(versiones del lock, pylint 4.1.3/astroid 4.3.4), no supuesto: flake8 ya bloqueaba (exit 0 en la
base, bloqueante por sí mismo); el `pylint src/ --fail-under=9.0` del CI salía **0 con un `W0613`
en `metrics.py:97`** (score 9.91), es decir S12 no se cumplía; el gate de cobertura sí bloqueaba
vía `fail_under` de `pyproject.toml` pero no estaba declarado en el job; el job de contrato ya
era `needs` de `docker` y el test ya falla con un spec roto. Cambios: `--cov-fail-under=70`
explícito, `--fail-on=W,E` en pylint **sin `--disable`**, y el árbol llevado a 0 warnings y 0
errores con dos correcciones de código en vez de supresiones: `_application` en el catálogo
`GET /metrics/list` (W0613 real) e imports `src.ml.*` → `ml.*`. La segunda corrige un bug real,
no cosmético: el mismo archivo cargado como `src.ml.schemas` y `ml.schemas` producía dos clases
`MetricBatchInput` y rompía `isinstance` entre el loader del dataset y sus tests (se vio rojo en
la primera corrida de la suite), y `src.*` no resuelve con el `PYTHONPATH=/app/src` de las
imágenes. Evidencia GREEN (entorno fijado, `docker-compose.test.yml`): 902 passed + 1 skipped +
1 xfailed + 1 xpassed, cobertura total 92.59 % (gate 70), `flake8` exit 0 y `pylint --fail-on=W,E`
exit 0 con 9.91/10 y cero mensajes W/E. Evidencia RED (los gates fallan de verdad): cobertura 35 %
→ exit 1 («Required test coverage of 70.0% not reached»); un warning en un archivo → flake8 exit 1
y pylint exit 20; `security` borrado de `POST /telemetry/metrics` en una copia del spec montada en
el contenedor → `test_oas6_telemetry_paths_require_api_key` FAILED. Descartado en el camino:
desactivar `unused-argument` globalmente en el CI (silencia futuros W0613 reales), agregar
supresiones de `E1102`/`W2301` (el entorno fijado ya no los reporta) y el «PR de prueba» que pide
S14 (MVP1 es local y no se pushea): se reemplaza por `tests/test_ci_gates.py` + la evidencia
negativa de arriba; cuando haya PRs reales se puede hacer igual. Frontera de slice: los seis
commits de T3 son la slice de este trabajo; los ~13k líneas que acumula `MVP1` sobre
`origin/develop` siguen siendo, en su mayoría, los merges de Santiago (L5). Próxima task: T4 (SPA).

L9 (2026-11-18, T4 cerrado): cuatro commits (openspec → base de la SPA → heatmap + E2E → CI).
Decisiones que el contrato no resolvía (`openspec/changes/ISS-B-05/design.md`): autenticación con
la key que pega el operador en `sessionStorage` (D2: `/metrics/*` es `apiKey` y cablear JWT es
backend nuevo), heatmap = tiempo × métrica normalizado por fila (D3: la API pública no expone
`page_url` ni `metadata`, así que una grilla página × posición no es posible sin backend nuevo) y
React 19 + TS + Vite sin D3 (D1: grilla y serie en SVG propio; desvío de ADR-0009 documentado).
Evidencia en el host (Node 26): `npm run lint` 0 warnings, `npm test` 50 passed (7 archivos),
`npm run build` OK (js 237.57 kB, gzip 74.17 kB), `npm run check-size` 243.1 kB raw / 74.9 kB
gzip contra un presupuesto de 1 MB, `npm run test:e2e` 5 passed (Chromium de Playwright; fallback
verificado con `PLAYWRIGHT_CHROMIUM_PATH=/usr/bin/chromium`). Gate negativo del tamaño probado con
una copia del script: sin `dist/` → exit 1, `dist` de 1.1 MB → exit 1. El worker de la fase B
encontró dos cosas que el padre tenía mal en el brief y las corrigió contra el código: el envelope
de error real es `{"error":{code,message}}` de ADR-09 (no `{"detail":{...}}`) y `vite preview` en
este host escucha en `::1`, así que el `baseURL` del E2E es `localhost`. La fuente de la API
quedó sin tocar (el heatmap y las dos vistas salen de `/metrics/{query,list,probes}`). Frontera de
slice: los cuatro commits de T4 son la slice de este trabajo; el árbol de `src/frontend/` es
greenfield (sólo `.gitkeep`), por eso no hay baseline diferencial de comandos previos. Próxima
task: T5 (integración E2E del flujo completo).

L10 (2026-11-18, T5 cerrado): seis commits (openspec → base URL de Telegram → smoke + stub en
compose → runbook y demo → fix del ancla del compose → changelog/tasks). Estado previo verificado:
ningún script recorría el flujo (`scripts/ci-tests.sh` corre pytest en el contenedor) y el tramo
"notificación" nunca se había probado end-to-end porque sin credenciales la alerta queda en
`Pending`. Se agregó `INTELLOPS_COMMS_TELEGRAM_API_BASE` (aditivo, default la constante actual) y
`make smoke` recorre diez etapas sobre la stack real en ~6-10 s: health → login del admin → app +
API key → catálogo → ingesta → lectura por `/metrics/query` → regla → alerta → `sent` + mensaje en
el stub. Decisión que cambió a mitad de camino: el stub primero vivía en el host con
`host.docker.internal`, pero el firewall de esta máquina dropea el tráfico contenedor→host (nftables
con `input policy drop`; desde comms ningún puerto del host responde y a internet sí), así que el
stub pasó a ser un servicio del compose bajo `profiles: ["smoke"]` en la red `intellops-net`: la
stack por defecto sigue con cuatro servicios y el smoke no depende del sistema operativo. El
rename del servicio a `intellops-telegram-stub` destapó un ancla frágil en
`tests/test_comms_container.py` (cortaba el bloque de comms por el prefijo `intellops-`), que ahora
corta en la próxima clave de servicio. Evidencia: `make smoke` verde 10/10 (alerta `sent` por
telegram, mensaje `[CRITICAL] TTFB p95 1500,0 ms supera el umbral de 500,0 ms en los últimos 5
min.`, total 6.3 s en la corrida final), suite Python 905 passed + 1 skipped + 1 xfailed + 1
xpassed con 93.26 % de cobertura, `pytest tests/test_comms_dispatch.py` 36 passed,
`pytest tests/test_comms_container.py` 8 passed + 1 skipped, y `git merge-tree --write-tree
origin/develop HEAD` sin conflictos (S20/S21 como *mergeable*, porque MVP1 no se pushea).
Frontera de slice: los seis commits de T5 son la slice de este trabajo. Próxima task: T6 (suite E2E
en CI + escenario k6 ≤ 500 ms).
