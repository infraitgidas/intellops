# Carga estándar de la ingesta (ISS-C-03)

Runbook de la prueba de carga de la ingesta: `load/ingest.js` (k6) mide
`POST /telemetry/metrics` sobre la stack real de `docker-compose.yml` con una
carga **estándar, corta y versionada**, y deja el resultado en
`reports/k6-summary.json`.

Alcance: la promesa de la v1 "ingesta ≤ 500 ms bajo carga estándar" (S26) se
convierte en un umbral explícito y reproducible. No es una prueba de capacidad
(§5), es una **regresión de performance**: mismo escenario, mismo umbral, mismo
número comparable entre corridas de la misma máquina.

---

## 1. Qué mide

| Métrica k6 | Qué es | Umbral (LT-3, S26) |
|---|---|---|
| `http_req_duration{expected_response:true}` | latencia de las respuestas OK: login y `POST /telemetry/metrics` del `setup()`, y la ingesta de cada iteración | `p(95) <= 500` ms |
| `http_req_failed` | proporción de requests fallidos (status inesperado o error de red) | `rate < 0.01` (< 1 %) |
| `checks` | los checks del escenario: la ingesta responde **202** y el 202 trae `accepted > 0` | `rate == 1` (100 %) |

El check de `accepted > 0` (D5) es lo que evita el falso verde: un 202 con todos
los eventos rechazados mediría la latencia de una ingesta que no ingiere.

**k6 sale ≠ 0 si un umbral se cruza** (código `99`, con
`thresholds on metrics '...' have been crossed` en el log). Un umbral incumplido
**no se baja**: se reporta con números (§5, "cuando falla").

## 2. La carga estándar

| Parámetro | Valor | Cómo cambiarlo |
|---|---|---|
| VUs | `10` | `make load VUS=20` o `-e VUS=20` |
| Duración | `1m` | `make load DURATION=30s` o `-e DURATION=30s` |
| Lote por iteración | 10 eventos (`BATCH_SIZE`) | constante en `load/ingest.js` |
| Pausa entre iteraciones | `sleep(1)` | constante en `load/ingest.js` |
| Eventos por segundo | ≈100 (10 VUs × 10 eventos / 1 s) | derivado de VUs |

Con la carga estándar una corrida completa son ≈600 iteraciones
(≈600 lotes, ≈6000 eventos) más los tres requests del `setup()`. Los valores de
TTFB que se envían están en el rango realista 120–380 ms a propósito: por debajo
del umbral de las reglas de alerta, así la corrida no dispara alertas.

`BASE_URL`, `ADMIN_EMAIL` y `ADMIN_PASSWORD` tienen defaults
(`http://intellops-core:8000`, el Admin del seed) y se pueden pisar por entorno:

```bash
BASE_URL=http://intellops-core:8000 make load
ADMIN_EMAIL=otro@intellops.local ADMIN_PASSWORD=... make load
```

## 3. Un solo comando

```bash
make up      # la stack tiene que estar arriba (o `docker compose up -d`)
make load
```

`make load`:

1. Resuelve la red del compose con `docker compose ps --format json` (no
   hardcodea el nombre del proyecto: es `intellops_intellops-net` en esta
   máquina, pero cambia con el directorio).
2. Crea `reports/` (ignorado por git).
3. Corre la imagen **pinneada** `grafana/k6:0.57.0` con `load/` montado en
   `/scripts:ro` y `reports/` en `/reports`, dentro de la red del compose, y con
   `--user $(id -u):$(id -g)` para que el summary quede a tu nombre:

```bash
docker run --rm -i --network "$(docker compose ps --format json | \
    python3 -c 'import json,sys; print(next(json.loads(l)["Networks"] for l in sys.stdin if l.strip()))')" \
  --user "$(id -u):$(id -g)" \
  -v "$PWD/load:/scripts:ro" -v "$PWD/reports:/reports" \
  -e BASE_URL=http://intellops-core:8000 \
  -e ADMIN_EMAIL=admin@intellops.local -e ADMIN_PASSWORD=admin-dev-password \
  -e VUS=10 -e DURATION=1m \
  grafana/k6:0.57.0 run --summary-export=/reports/k6-summary.json /scripts/ingest.js
```

Por qué en contenedor y en esa red (D2): nada que instalar en el repo, la
imagen fija la versión de k6 y el contenedor alcanza la API por DNS del compose
(`http://intellops-core:8000`), sin depender de que el host acepte tráfico desde
los contenedores. La primera corrida baja la imagen (~50 MB).

### Prerequisitos

| Requisito | Cómo se comprueba |
|---|---|
| Docker con Compose v2 | `docker compose version` |
| Stack arriba con la API en verde | `curl -fsS http://localhost:8000/health` |
| El Admin del seed en la base | lo siembra la migración `0002`; si el login falla, `docker compose down -v && make up` |
| Imagen `grafana/k6:0.57.0` | se baja sola en la primera corrida |

## 4. El escenario (`load/ingest.js`)

| Fase | Qué hace |
|---|---|
| `setup()` | `POST /auth/login` (Admin del seed) → `POST /applications` con nombre `k6-load-<timestamp>` → `POST /applications/{id}/api-key`; devuelve `{apiKey, appId}` |
| iteración (`default`) | `POST /telemetry/metrics` con `X-API-Key` y un lote de 10 eventos → `check` del 202 y de `accepted > 0` → `sleep(1)` |
| `teardown()` | no borra nada (D4): sólo informa el `app_id` de la corrida |

El payload es el mismo del smoke (`scripts/smoke.py`): envelope
`schema_version: "1.0"` con 1..500 eventos, cada evento con `session_id` (UUID
v4), `timestamp` ISO 8601 UTC y una métrica `TTFB` en `ms`. Un evento por
muestra hace que `accepted` cuente exactamente las muestras.

Variables: `BASE_URL`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `VUS`, `DURATION`
(LT-2). No hay imports fuera de los módulos de k6 (`k6/http`, `k6`, `k6/crypto`).

## 5. Leer `reports/k6-summary.json`

El summary es el JSON de `--summary-export`. Tres bloques: `root_group`,
`metrics` y `setup_data`.

```bash
python3 - <<'EOF'
import json
m = json.load(open("reports/k6-summary.json"))["metrics"]
print("p95 (ms):", round(m["http_req_duration{expected_response:true}"]["p(95)"], 1))
print("errores :", m["http_req_failed"]["value"])
print("checks  :", m["checks"]["value"], m["checks"]["passes"], m["checks"]["fails"])
print("iterac. :", m["iterations"]["count"])
for name, metric in m.items():
    if "thresholds" in metric:
        print(name, metric["thresholds"])
EOF
```

| Clave | Qué leer |
|---|---|
| `metrics["http_req_duration{expected_response:true}"]["p(95)"]` | p95 de latencia en **ms**: el número del umbral (≤ 500) |
| `metrics["http_req_duration{expected_response:true}"]["thresholds"]` | `{"p(95)<=500": false}` |
| `metrics.http_req_failed.value` | proporción de requests fallidos (0 = 0 %); tiene que ser < 0.01 |
| `metrics.checks.value` / `.passes` / `.fails` | tasa de checks (1 = 100 %) y cuántos pasaron/fallaron |
| `metrics.iterations.count` / `.rate` | iteraciones (lotes) completadas y por segundo |
| `metrics.vus_max.max` | VUs efectivos (tiene que ser el `VUS` pedido) |
| `setup_data` | `{apiKey, appId}` de la corrida |

**Ojo con `thresholds`:** el valor es `true` cuando el umbral **se cruzó**
(k6 lo marca como *aborted*), no cuando pasó. Todos en `false` = todo en verde,
que es lo mismo que dice el código de salida de k6 (`0`). El `✓`/`✗` del log de
la consola es la lectura directa.

**Ojo con `passes`/`fails` de una métrica `Rate`:** son las muestras internas
del *flag* de k6, no requests exitosos/fallidos. En `http_req_failed` con todo
OK vas a ver `fails = <cantidad de requests>`; el número que importa es `value`.
En `checks` sí son los checks pasados y fallados.

**`setup_data` trae la API key en claro** (`setup_data.apiKey`): es una key
efímera de la app `k6-load-*` de la corrida, pero no se commitea ni se comparte
fuera del equipo. `reports/` está en `.gitignore` por eso.

### Una corrida de referencia

Máquina de desarrollo del laboratorio (stack completo en el mismo host, 10 VUs,
1 min), `make load` del 2026-11-18:

```
     ✓ { expected_response:true }...: avg=4.41ms min=1.71ms med=3.26ms max=78.31ms p(90)=6.71ms p(95)=9.89ms
   ✓ http_req_failed................: 0.00%   0 out of 603
   ✓ checks.........................: 100.00% 1203 out of 1203
     iterations.....................: 600     9.91/s
```

El `✓` delante de una métrica es el resultado de su umbral; los tres en `✓` y
salida `0`.

Es el orden de magnitud esperable con todo en el mismo host. Otro número no es
mejor ni peor: es otra máquina.

### Qué NO prueba este número (LT-4, D3)

- **No mide capacidad**: 10 VUs y 60 s no buscan el punto de quiebre. Eso es
  estrés/soak, fuera de alcance (proposal, "Out of Scope").
- **No hay red real**: el contenedor de k6 habla con la API por el bridge de
  Docker en el mismo host. La latencia de red del usuario final (RTT, TLS,
  móvil) no está en el número.
- **No hay DB dedicada ni tuning**: la base es la de dev, compartida con los
  workers de reglas y anomalías; no dice nada de un Postgres tuneado o
  replicado.
- **La máquina entera compite**: API, workers, Postgres y k6 en el mismo CPU.
  Es realista para la demo y el piloto, no representativo de producción.
- **No compara corridas entre máquinas** (por eso el job de CI es manual, D6).

## 6. Limpieza de las apps `k6-load-*`

`teardown()` no limpia (D4): cada corrida deja una aplicación
`k6-load-<timestamp>` con sus sesiones y métricas. `DELETE /applications/{id}`
**no** sirve una vez que la app tiene sesiones (FK `RESTRICT` de
`user_session.app_id` → 409 Conflict), así que:

```bash
# 1. La corrida de referencia: app_id del log o de reports/k6-summary.json
python3 -c "import json; print(json.load(open('reports/k6-summary.json'))['setup_data']['appId'])"

# 2. Borrar el contenido de una app puntual (orden de FKs)
docker compose exec -T intellops-db psql -U intellops -d intellops <<'SQL'
\set app  '00000000-0000-0000-0000-000000000000'
DELETE FROM alert        WHERE application_id = :'app';
DELETE FROM anomaly      WHERE application_id = :'app';
DELETE FROM js_exception WHERE session_id IN (SELECT session_id FROM user_session WHERE app_id = :'app');
DELETE FROM rum_metric   WHERE session_id IN (SELECT session_id FROM user_session WHERE app_id = :'app');
DELETE FROM user_session WHERE app_id = :'app';
DELETE FROM application  WHERE app_id = :'app';
SQL

# 3. O la vía simple: tirar el volumen de desarrollo
docker compose down -v && make up
```

`docker compose down -v` borra también el Admin del seed: la próxima corrida lo
recrea con la migración `0002`.

## 7. El job `load` del CI

Manual a propósito (D6): en cada PR duplicaría el coste del job `e2e` sin
agregar señal (la latencia de un runner compartido no es comparable entre
corridas). Se corre cuando se toca ingesta o infraestructura.

- **Disparo**: Actions → *IntellOps CI* → *Run workflow*, con las entradas
  `vus` (default `10`) y `duration` (default `1m`).
- **Condición**: `if: github.event_name == 'workflow_dispatch'`; depende de
  `lint`.
- **Pasos**: `docker compose up -d --build` → espera `/health` → `make load
  VUS=<vus> DURATION=<duration>` (el mismo comando local) →
  sube `reports/k6-summary.json` como artefacto `k6-summary`.
- **Artefacto**: se sube siempre (`if: always()`): si un umbral se cruzó, el
  summary es la evidencia que hay que mirar.

El job **bloqueante** en cada push/PR es `e2e` (el smoke completo, el mismo
flujo que `make e2e-ci`), no este: un rojo de `load` en una corrida manual se
lee con los números de §5.

## 8. Cuando falla

| Síntoma | Causa probable | Qué mirar |
|---|---|---|
| `make load` corta en el `setup` con `setup/login` | la base no tiene el Admin del seed, o `ADMIN_PASSWORD` no es la del seed | `docker compose logs intellops-core`; `docker compose down -v && make up` |
| `setup: aplicación 201` falla | rol o JWT: no es Admin | logs de `intellops-core`; `GET /users/me` |
| k6 dice `cannot resolve host intellops-core` | la red resuelta no es la del compose (stack caída o proyecto distinto) | `docker compose ps`; `docker network ls` |
| `could not open '/reports/k6-summary.json': permission denied` | el contenedor corre con otro UID | el target pasa `--user $(id -u):$(id -g)`; si corrés a mano, agregalo |
| `thresholds on metrics 'http_req_duration{expected_response:true}' have been crossed` (exit `99`) | p95 > 500 ms, errores > 1 % o un check en rojo: **un umbral incumplido** | el summary (§5); `docker compose logs intellops-core`; CPU del host |
| `checks` < 100 % con `accepted == 0` | el payload dejó de validar (drift con el contrato) o la ingesta rechaza todo | el `reason` de cada rechazo en el cuerpo del 202; `tests/test_contract.py` |

Un umbral incumplido **no se baja**: se reporta con p95, tasa de error y checks,
y se abre la issue de performance correspondiente (el tuning de performance está
fuera del alcance de C.3).
