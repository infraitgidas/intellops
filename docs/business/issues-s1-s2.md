# Issues de Desarrollo — Sistema de Observabilidad Predictiva UX-Céntrica (IntellOps)

Issues concretos derivados del [EDT intellops.md](./EDT%20intellops.md), **redefinidos contra el estado real del repositorio** (revisión 14/08/2026): código existente, specs OpenSpec, DER v1.2, minutas 20-07/23-07/12-08 y arquitectura de 4 contenedores decidida en agosto.

**Convenciones:**

- **ID**: `ISS-<Sprint>-<N>` (secuencial por sprint).
- **Owner**: responsable técnico según el EDT y las minutas.
- **Etiquetas sugeridas**: `sprint-<n>`, `owner:<nombre>`, `<área>` (`backend`, `telemetria`, `ml`, `anomalias`, `alertas`, `frontend`, `qa`, `infra`, `docs`, `decision`).
- **Prioridad**: Alta / Media.
- **Dependencias**: issues que deben estar completos antes de poder empezar.
- ** Ya documentado**: indica que existe material previo en el repo que el issue debe **consumir**, no reescribir.

---

##  Contexto — Estado real del proyecto (no es la hoja en blanco del EDT)

El EDT asume un proyecto que arranca de cero. La realidad del repo es otra:

| Área | Qué existe YA | Qué falta |
|---|---|---|
| **Código** | `src/api/main.py` (FastAPI: solo `/health`, `/ready`), `tests/test_health.py` (2 tests), Dockerfile, docker-compose con servicio `api` | Todos los endpoints de negocio, routers, modelos, auth, DB |
| **DB** | DER v1.2 + diccionario + trazabilidad DER→Contenedores (`docs/der/`, rama sin mergear) | **Ninguna** base de datos implementada  |
| **Arquitectura** | Spec OpenSpec (13 contenedores LGTM) + **decisión agosto: 4 contenedores + PostgreSQL** (minuta 12-08, PDF `User Session Metrics`) | ADR que registre la decisión PostgreSQL y el cambio de stack (sin ADR, "la decisión no existe") |
| **Contratos** | `openspec/specs/architecture/interfaces.md` (20 endpoints) + endpoints del EDT | `openspec/specs/openapi.yaml` / `asyncapi.yaml` **no existen** |
| **ML** | Hipótesis H1–H7, 24 experimentos planificados (EXP-*), selección de 5 métricas (TTFB, FCP, XHR Latency, JS Exceptions, Rage Clicks), flujo híbrido ML clásico + Llama 3.2 1B | `src/ml/` **no existe**; `ml/experiments/` vacío; cero datasets/modelos |
| **Telemetría** | Investigación profunda (frontend-observability 929 líneas, rum-agent-deep-dive 1.207 líneas, observability-tools 845 líneas) | `src/agent/rum.js` **no existe** |
| **CI** | `.github/workflows/ci.yml` (jobs lint, test, contract, license-scan, docker) | Jobs `contract` y `license-scan` **comentados/inertes**; sin gate real de coverage |
| **Frontend** | Decisión: postergado a Sprint 3/4 (minuta 12-08) | Nada |
| **Ramas** | `docs/meeting-2026-08-12`, `docs/architecture-isolation-and-traceability`, `docs/edt-sprint-planning` sin mergear a main | Merge + registro de decisiones |

###  Decisiones abiertas que bloquean o condicionan issues

1. **PostgreSQL vs SQLite**: la spec dice SQLite; la minuta 23-07 y la justificación arquitectónica deciden PostgreSQL 16 + JSONB. Falta el ADR. → Resolver en S1 (ISS-S1-01).
2. **Stack de observabilidad**: spec = LGTM completo (Tempo, Loki, Prometheus, Grafana, Alertmanager, Netdata); diseño de agosto = 4 contenedores sin esos servicios. → Resolver en S1 (ISS-S1-01).
3. **Ownership**: el EDT asigna a Santiago backend core/DB y a Federico telemetría/RUM; el TEAM_CHARTER asigna a Federico seguridad/RUM y a Santiago QA/CI. Este documento **sigue el EDT** (es el plan aprobado en la rama), pero conviene ratificarlo en la reunión con Emanuel.
4. **Endpoints**: `interfaces.md` usa `/metrics/ingest`; el EDT usa `/telemetry/metrics`. Unificar en ISS-S1-02.

---

## SPRINT 1 — 24/08 al 06/09 · Arquitectura e infraestructura

>  Nota: la minuta 12-08 define un Sprint 1 del 12/08 al 26/08 con core de ingesta + compose + PostgreSQL + esqueleto IA. Este sprint del EDT absorbe y formaliza ese trabajo pendiente de la rama.

### ISS-S1-01 — Consolidar decisiones de arquitectura en ADRs y mergear ramas pendientes

- **Sprint**: S1
- **Owner**: Equipo (coordina Santiago)
- **Etiquetas**: `sprint-1`, `decision`, `arquitectura`, `docs`
- **Dependencias**: —
- **Prioridad**: Alta · **Bloqueante**
- **Ramas** docs/meeting-2026-08-12 y docs/architecture-isolation-and-traceability mergeadas a develop.
**Descripción**: El repo tiene 3 arquitecturas en conflicto (spec LGTM 13 contenedores, C4 desactualizado, diseño agosto 4 contenedores + PostgreSQL)

**Criterios de aceptación**:
- [ ] ADR que registra PostgreSQL 16 + JSONB como DB definitiva (reemplaza SQLite).
- [ ] ADR que registra la arquitectura de 4 contenedores (`intellops-core`, `intellops-ai-engine`, `intellops-db`, `intellops-comms`) y qué pasa con el stack LGTM (descarta, aplaza o conserva Netdata como self-monitoring).
- [ ] `docs/infrastructure/c4_container_v1.puml` actualizado o marcado como histórico.
- [ ] Ownership de módulos ratificado (EDT vs TEAM_CHARTER) y documentado.

---

### ISS-S1-02 — Contratos API: OpenAPI + DDL + unificación de endpoints

- **Sprint**: S1
- **Owner**: Santiago
- **Etiquetas**: `sprint-1`, `owner:santiago`, `backend`, `contrato`
- **Dependencias**: ISS-S1-01
- **Prioridad**: Alta

**Descripción**: Convertir la definición de endpoints en contratos versionados antes de codificar. Unificar las dos nomenclaturas existentes (`interfaces.md` vs EDT): decidir `/telemetry/metrics` vs `/metrics/ingest` y dejar una sola. Generar el DDL inicial desde el DER v1.2.

**Criterios de aceptación**:
- [ ] `openspec/specs/openapi.yaml` creado con los endpoints acordados (auth, users, applications, sessions, telemetry, metrics, anomalies, alerts, models).
- [ ] `openspec/specs/asyncapi.yaml` creado para canales `anomaly/detected` y `alert/triggered` (o decisión explícita de aplazarlos).
- [ ] Nomenclatura de endpoints unificada y documentada.
- [ ] DDL v1.0 generado desde DER v1.2 (entidades APPLICATION, LAB_USER, USER_FAVORITE_METRIC, USER_SESSION, RUM_METRIC, JS_EXCEPTION, ML_MODEL, ANOMALY, ALERT).

---

### ISS-S1-03 — Infraestructura docker-compose multi-contenedor

- **Sprint**: S1
- **Owner**: Federico
- **Etiquetas**: `sprint-1`, `owner:federico`, `infra`
- **Dependencias**: ISS-S1-01
- **Prioridad**: Alta

**Descripción**: Ampliar `docker-compose.yml` (hoy solo `api`) al diseño de 4 contenedores: `intellops-core` (FastAPI, expone 80/443, límite ~250MB), `intellops-ai-engine` (worker AI aislado ~1000MB, sin puertos), `intellops-db` (PostgreSQL 16), `intellops-comms` (dispatcher de alertas).

**Criterios de aceptación**:
- [ ] Los 4 servicios definidos con límites de RAM y redes.
- [ ] `intellops-core` es el único que expone puertos.
- [ ] `intellops-ai-engine` aislado (contenedor de OOM) sin tráfico web.
- [ ] Volúmenes y red `intellops-net` correctamente cableados.
- [ ] `make up` levanta todo el stack.

---

### ISS-S1-04 — PostgreSQL inicializado con DER v1.2 y migraciones

- **Sprint**: S1
- **Owner**: Santiago
- **Etiquetas**: `sprint-1`, `owner:santiago`, `base-de-datos`, `backend`
- **Dependencias**: ISS-S1-02, ISS-S1-03
- **Prioridad**: Alta

**Descripción**: Levantar PostgreSQL 16 en el stack, crear la base con el DDL del DER v1.2 (JSONB + MVCC) y establecer un mecanismo de migraciones. Conectar `intellops-core` a la DB (asyncpg/SQLAlchemy, pool_size=20, max_overflow=10).

**Criterios de aceptación**:
- [ ] PostgreSQL 16 corriendo en `intellops-db`.
- [ ] Migraciones aplicadas: las 9 entidades creadas con relaciones e índices.
- [ ] `INTELLOPS_DB_PATH`/`DATABASE_URL` leído por la app (hoy se declara en compose pero no se usa).
- [ ] Healthcheck del API verifica conexión a DB.

---

### ISS-S1-05 — Contrato de ingesta RUM (evento + validación)

- **Sprint**: S1
- **Owner**: Federico
- **Etiquetas**: `sprint-1`, `owner:federico`, `telemetria`, `contrato`
- **Dependencias**: ISS-S1-02
- **Prioridad**: Alta

**Descripción**: Definir la estructura del evento RUM y de excepción apoyándose en la investigación existente (`docs/research/rum-agent-deep-dive.md`, `frontend-observability.md`) y en la selección de 5 métricas (TTFB, FCP, XHR Latency, Tasa de Excepciones JS, Rage Clicks).

**Criterios de aceptación**:
- [ ] Esquema del evento RUM versionado (timestamp, session_id, application_id, métricas, metadata).
- [ ] Esquema del evento `JS_EXCEPTION` (error_type, message, stack_trace, session_id, metric_id, timestamp).
- [ ] Esquema de validación definido (obligatorios/opcionales, unidades, rangos).
- [ ] Contrato alineado con el OpenAPI de ISS-S1-02.

---

### ISS-S1-06 — Diseño del pipeline de ingesta

- **Sprint**: S1
- **Owner**: Federico
- **Etiquetas**: `sprint-1`, `owner:federico`, `telemetria`, `arquitectura`
- **Dependencias**: ISS-S1-05
- **Prioridad**: Alta

**Descripción**: Diseñar el flujo `Application → Collector → API Ingestion → Validation → Storage` con ingesta asíncrona y bulk inserts (asyncpg) según la arquitectura de agosto.

**Criterios de aceptación**:
- [ ] Flujo de ingesta documentado.
- [ ] Estrategia de validación y manejo de eventos inválidos definida.
- [ ] Estrategia de persistencia asíncrona (bulk insert) definida.

---

### ISS-S1-07 — Diseño de entidades ML y pipeline conceptual

- **Sprint**: S1
- **Owner**: Romeo
- **Etiquetas**: `sprint-1`, `owner:romeo`, `ml`, `arquitectura`
- **Dependencias**: ISS-S1-02
- **Prioridad**: Alta

**Descripción**: Formalizar el diseño de `ML_MODEL`, `ANOMALY`, `ALERT` (ya esbozado en la trazabilidad DER) y el pipeline `RUM_METRIC → Feature Engineering → Model → Prediction → Anomaly → Alert`, incluyendo el flujo híbrido (ML clásico detecta + Llama 3.2 1B genera mensaje legible).

**Criterios de aceptación**:
- [ ] Entidades ML diseñadas y alineadas con el DDL.
- [ ] Pipeline conceptual documentado.
- [ ] Contrato de entrada/salida del modelo definido.
- [ ] Flujo híbrido ML+LLM documentado (qué hace cada parte).

---

### ISS-S1-08 — Esqueleto del módulo IA (`src/ml/`)

- **Sprint**: S1
- **Owner**: Romeo
- **Etiquetas**: `sprint-1`, `owner:romeo`, `ml`
- **Dependencias**: ISS-S1-07
- **Prioridad**: Media

**Descripción**: Crear la estructura `src/ml/` (base, detectores, pipeline) y un endpoint de estado, preparando el worker `intellops-ai-engine` para consumir el contrato de dataset con datos mock.

**Criterios de aceptación**:
- [ ] Estructura `src/ml/` creada (base, detectors/, pipeline/).
- [ ] Esqueleto del worker ai-engine compila y arranca.
- [ ] Lee datos mock respetando el contrato de dataset.
- [ ] Endpoint/método de status del módulo IA.

---

### ISS-S1-09 — CI real: activar jobs inertes y gate de coverage

- **Sprint**: S1
- **Owner**: Romeo
- **Etiquetas**: `sprint-1`, `owner:romeo`, `qa`, `ci-cd`
- **Dependencias**: ISS-S1-04
- **Prioridad**: Alta

**Descripción**: Los jobs `contract` y `license-scan` de `.github/workflows/ci.yml` existen pero están comentados. Activarlos y hacer cumplir el gate de coverage ≥70% (hoy configurado en pyproject pero no enforceado).

**Criterios de aceptación**:
- [ ] Job `contract` activo (schemathesis contra el OpenAPI de ISS-S1-02).
- [ ] Job `license-scan` activo (chequeo de licencias SSPL/AGPL).
- [ ] Coverage <70% falla el job `test` (`--cov-fail-under`).
- [ ] Badge de coverage en README.
- [ ] Pipeline CI verde en `develop`.

---

## SPRINT 2 — 07/09 al 20/09 · Backend Core + Ingesta

### ISS-S2-01 — CRUD de usuarios (LAB_USER)

- **Sprint**: S2
- **Owner**: Santiago
- **Etiquetas**: `sprint-2`, `owner:santiago`, `backend`
- **Dependencias**: ISS-S1-04, ISS-S1-02
- **Prioridad**: Alta

**Descripción**: Implementar el modelo `LAB_USER`, acceso a datos, CRUD, validaciones, roles y campo `is_active`.

**Criterios de aceptación**:
- [ ] Modelo `LAB_USER` implementado con migración.
- [ ] Acceso a datos y CRUD funcional.
- [ ] Validaciones y roles implementados.
- [ ] Campo `is_active` operativo.

---

### ISS-S2-02 — Autenticación (login/logout/JWT)

- **Sprint**: S2
- **Owner**: Santiago
- **Etiquetas**: `sprint-2`, `owner:santiago`, `backend`, `seguridad`
- **Dependencias**: ISS-S2-01
- **Prioridad**: Alta

**Descripción**: Login, logout, hash de contraseñas, gestión de sesión/token (JWT), middleware de autenticación y manejo de credenciales inválidas. `api_token` por aplicación según arquitectura de agosto.

**Criterios de aceptación**:
- [ ] Login/logout funcionales.
- [ ] Contraseñas hasheadas (nunca en claro).
- [ ] JWT emitido y validado por middleware.
- [ ] Credenciales inválidas manejadas correctamente.

---

### ISS-S2-03 — CRUD de applications (APPLICATION)

- **Sprint**: S2
- **Owner**: Federico
- **Etiquetas**: `sprint-2`, `owner:federico`, `backend`
- **Dependencias**: ISS-S2-01
- **Prioridad**: Alta

**Descripción**: CRUD de `APPLICATION`, validación de permisos, endpoints y asociación aplicación-usuario. Generación de `api_token` para ingesta.

**Criterios de aceptación**:
- [ ] CRUD de `APPLICATION` implementado.
- [ ] Validación de permisos sobre las aplicaciones.
- [ ] `api_token` generado y validado en ingesta.

---

### ISS-S2-04 — API Core v1

- **Sprint**: S2
- **Owner**: Santiago
- **Etiquetas**: `sprint-2`, `owner:santiago`, `backend`, `api`
- **Dependencias**: ISS-S2-02, ISS-S2-03
- **Prioridad**: Alta

**Descripción**: Implementar la primera versión de la API según el OpenAPI acordado en ISS-S1-02: `POST /auth/login`, `POST /auth/logout`, `GET /users`, `GET /users/{id}`, `GET/POST /applications`, `GET/PUT/DELETE /applications/{id}`.

**Criterios de aceptación**:
- [ ] Endpoints de auth implementados.
- [ ] Endpoints de users implementados.
- [ ] Endpoints de applications implementados.
- [ ] API Core operativa y documentada (Swagger).

---

### ISS-S2-05 — Collector de telemetría (ingesta)

- **Sprint**: S2
- **Owner**: Federico
- **Etiquetas**: `sprint-2`, `owner:federico`, `telemetria`, `backend`
- **Dependencias**: ISS-S1-05, ISS-S1-06, ISS-S2-03
- **Prioridad**: Alta

**Descripción**: Implementar el endpoint de ingesta (`POST /telemetry/metrics` o el nombre unificado en S1) con validación, serialización, manejo de errores, persistencia asíncrona y logs de eventos inválidos.

**Criterios de aceptación**:
- [ ] Endpoint de ingesta operativo (recibe eventos RUM).
- [ ] Validación y serialización de eventos.
- [ ] Manejo de errores y logs de eventos inválidos.
- [ ] Persistencia asíncrona (bulk insert) funcional.

---

### ISS-S2-06 — RUM_METRIC

- **Sprint**: S2
- **Owner**: Federico
- **Etiquetas**: `sprint-2`, `owner:federico`, `telemetria`, `rum`
- **Dependencias**: ISS-S2-05
- **Prioridad**: Alta

**Descripción**: Pipeline `ingesta → Validation → Normalization → Database` para las 5 métricas prioritarias (TTFB, FCP, XHR Latency, JS Exceptions, Rage Clicks) persistidas en `RUM_METRIC`.

**Criterios de aceptación**:
- [ ] Métricas recibidas, validadas y normalizadas.
- [ ] Persistidas en `RUM_METRIC` con su aplicación/sesión asociadas.
- [ ] Eventos de las 5 métricas prioritarias cubiertos.

---

### ISS-S2-07 — JS_EXCEPTION

- **Sprint**: S2
- **Owner**: Federico
- **Etiquetas**: `sprint-2`, `owner:federico`, `telemetria`
- **Dependencias**: ISS-S2-05
- **Prioridad**: Alta

**Descripción**: Implementar la ingesta y persistencia de `JS_EXCEPTION`.

**Criterios de aceptación**:
- [ ] Endpoint de excepciones operativo.
- [ ] Excepciones persistidas con stack_trace completo.

---

### ISS-S2-08 — Dataset inicial para ML

- **Sprint**: S2
- **Owner**: Romeo
- **Etiquetas**: `sprint-2`, `owner:romeo`, `ml`, `datos`
- **Dependencias**: ISS-S1-08
- **Prioridad**: Alta

**Descripción**: Generar dataset sintético (si no hay datos reales), notebook/proyecto reproducible, exploración estadística, outliers, distribuciones y correlaciones. Usar como base `openspec/specs/research/benchmarking.md` (datasets GIDAS-Synth-Metrics-2026).

**Criterios de aceptación**:
- [ ] Dataset inicial (real o sintético) disponible en `ml/data/`.
- [ ] Proyecto reproducible (notebook o script).
- [ ] Análisis exploratorio documentado.
- [ ] Outliers, distribuciones y correlaciones analizadas.

---

### ISS-S2-09 — Evaluación preliminar de algoritmos

- **Sprint**: S2
- **Owner**: Romeo
- **Etiquetas**: `sprint-2`, `owner:romeo`, `ml`
- **Dependencias**: ISS-S2-08
- **Prioridad**: Media

**Descripción**: Evaluar métodos estadísticos, thresholds dinámicos, Isolation Forest, modelos de series temporales y enfoques híbridos (alineado con EXP-001 a 004).

**Criterios de aceptación**:
- [ ] Comparación preliminar de enfoques documentada.
- [ ] Recomendación inicial de algoritmo/s justificada.

---

