# IntellOps — Marco Conceptual: Diseño

**Documento**: `03-diseno.md`
**Parte del marco**: Marco Conceptual e Ingenieril de IntellOps
**Versión**: 1.1
**Fecha**: 2026-09-11
**Última revisión**: 2026-10-20 (alineación a la arquitectura de 4 contenedores)
**Autor**: Coordinación InfraIT — Emanuel Rodríguez
**Estado**: Borrador para revisión del equipo

---

## 1. Visión de Arquitectura (vista sistémica)

Intelops se diseña como **arquitectura de capas con flujo causal descendente y retroalimentación ascendente**,
materializando el lazo de control definido en el análisis:

```
┌──────────────────────────────────────────────────────────────────────┐
│  CAPA DE EXPERIENCIA — navegador del usuario final                   │
│  Apps web de GIDAS instrumentadas + Agente RUM (JS, cliente)         │
│  SPA React del dashboard (build estático, fuera del compose del MVP) │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ HTTPS · POST /telemetry/metrics
                                │ POST /telemetry/exceptions (batch ≤ 500)
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  intellops-core — FastAPI + Uvicorn (contenedor)                     │
│  Auth por API key · validación · cola asyncio en proceso · workers   │
│  bulk insert · API de gestión y consulta · healthcheck               │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ SQLAlchemy + asyncpg
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  intellops-db — PostgreSQL 16 (contenedor stateful)                  │
│  Único almacén: APPLICATION, LAB_USER, USER_SESSION, RUM_METRIC,     │
│  JS_EXCEPTION, ML_MODEL, ANOMALY, ALERT                             │
└───────────────┬───────────────────────────────┬──────────────────────┘
                │ read batch / write            │ read/update ALERT
                ▼                               ▼
┌───────────────────────────────┐  ┌───────────────────────────────────┐
│ intellops-ai-engine           │  │ intellops-comms                   │
│ scikit-learn + Llama 1B       │  │ dispatcher Telegram / Email       │
│ ANOMALY + ALERT (Pending)     │  │ retry + backoff · Sent/Failed     │
└───────────────────────────────┘  └──────────────────┬────────────────┘
                                                      │ HTTPS saliente
                                                      ▼
                                           Telegram / Email (externo)

Capa transversal: CI/CD (GitHub Actions) · tests (unit/integration/E2E/contract)
· quality gates (coverage ≥70%, lint 0) · ADRs · specs

Fuera del compose del producto: el pipeline GLP de seguridad (Promtail/Loki/Grafana)
es infraestructura separada del módulo M-SEG. Roadmap post-MVP: OTel Collector, Tempo,
Prometheus, Alertmanager, Netdata, RAG/Chroma y LLM server standalone.
```

---

## 2. Arquitectura de Contenedores (C4 nivel container)

Basado en `openspec/specs/architecture/containers.md` (v2.0) y `docker-compose.yml`.
La arquitectura vigente del MVP es un **monolito modular desacoplado de 4 contenedores**;
el agente RUM y la SPA no son contenedores del compose.

| Contenedor | Tecnología | Responsabilidad | Recursos |
|---|---|---|---|
| **intellops-core** | FastAPI + Uvicorn (Python 3.11) | Ingesta `/telemetry/*`, auth por API key, gestión multi-tenant, consulta y healthcheck. Único servicio con puerto publicado (`8000`) | `mem_limit` 250 MB |
| **intellops-db** | PostgreSQL 16 (`postgres:16-alpine`) | Único almacén de estado: esquema completo, volumen `intellops-db-data`. Sin puertos al host | Sin límite explícito |
| **intellops-ai-engine** | Python + scikit-learn + Llama 1B | Worker batch: lee `RUM_METRIC`, escribe `ANOMALY` y `ALERT` en estado Pending. Sin puertos; aislado para que un OOM Kill no afecte la ingesta | `mem_limit` 1000 MB |
| **intellops-comms** | Python | Polling de `ALERT` Pending, despacho por Telegram/Email con retry + backoff, actualización a Sent/Failed. Sin puertos | `mem_limit` 150 MB |

**No son contenedores del MVP:** el **Agente RUM** (JS en el navegador), la **SPA React**
(build estático servido aparte), el **pipeline GLP** (Promtail/Loki/Grafana, módulo M-SEG)
y el **stack LGTM/Netdata/RAG** del producto (roadmap post-MVP).

**Estado de implementación (oct-2026):** `intellops-core` e `intellops-db` están operativos;
`intellops-ai-engine` e `intellops-comms` son placeholders que mantienen el stack vivo.
La detección y el despacho se implementan en las tareas B.4, B.10 y B.11 del plan integral.

**Footprint total estimado**: ~1.4 GB RAM con límites + PostgreSQL · CPU-only · **$0/mes**.

---

## 3. Ciclo de Control Operacional (cómo funciona el lazo en runtime)

```
1. CAPTURA    Agente RUM en el navegador (Core Web Vitals, TTFB, errores JS)
              → POST /telemetry/metrics | /telemetry/exceptions (batch ≤ 500)
2. INGESTA    intellops-core valida contra OpenAPI, encola en asyncio.Queue
              y persiste en PostgreSQL por chunks (bulk insert + retry)
3. ANÁLISIS   intellops-ai-engine lee ventanas batch de RUM_METRIC
              → Isolation Forest + Z-score (+ seasonal en fases posteriores)
              → escribe ANOMALY
4. DIAGNÓSTICO El LLM local (Llama 3.2 1B) redacta la explicación y crea
              ALERT en estado Pending (post-MVP; hoy el worker es placeholder)
5. ACCIÓN     intellops-comms hace polling de ALERT Pending, despacha por
              Telegram/Email con retry + backoff y actualiza Sent/Failed;
              el dashboard consulta intellops-core
6. APRENDIZAJE Feedback al backlog y dataset etiquetado para experimentos
              (DVC/MLflow)
```

Cada ciclo apunta a **anticipar** (forecast + health score) antes que a **reaccionar** (alertas).
El stack de observabilidad del producto (LGTM) y Netdata se incorporan en fases posteriores;
el pipeline GLP de seguridad corre fuera del compose del producto.

---

## 4. Módulos de Ingeniería (asignables a contributors)

La arquitectura se organiza en módulos que **mapean 1:1 con las PPS** (acoplamiento buscado):

| Módulo | Alcance | Contributor natural (PPS) | Backlog épica |
|---|---|---|---|
| **M-SEG** Seguridad & Eventos | Hardening CIS, observabilidad de eventos (GLP), dashboards de seguridad | Federico (PPS Módulo Seguridad) | EPIC-SEG |
| **M-RUM** Telemetría UX | Agente RUM, correlación UX, journeys | Federico (Fase 2) + Ema | EPIC-RUM |
| **M-ML** IA / AIOps | Detección anomalías, forecast, health score, clasificación reclamos | Romeo (PPS ML) | EPIC-ML |
| **M-RCA** Asistente IA | LLM local, RAG, RCA, chat (post-MVP) | Romeo (Fase 2) | EPIC-ML / EPIC-RCA |
| **M-QA** Calidad & CI/CD | Tests, pipeline, quality gates, synthetic journeys, chaos | Santiago (PPS QA) | EPIC-QA |
| **M-ING** Ingesta & Storage | API de ingesta/consulta, cola asíncrona, PostgreSQL 16 (SQLModel/Alembic) | Transversal (todos tocan) | EPIC-ING |
| **M-DASH** Dashboard | Vistas latencias/heatmap/predicciones, chat (SPA React static, no es contenedor) | Romeo + Ema | EPIC-DASH |

**Principio de asignación**: cada PPS entrega un módulo funcional completo con DoD cumplido → el
producto final emerge de la integración de módulos independientes y ordenados (no de un monstruo
compartido).

---

## 5. Decisiones Arquitectónicas Clave (resumen + ADRs)

| # | Decisión | Estado | Referencia |
|---|---|---|---|
| ADR-0001 | Reemplazo ELK → Grafana + Loki + Prometheus (licencia SSPL). Aplica al pipeline GLP de seguridad; el stack LGTM no integra el compose del MVP | Aceptado | `docs/adr/0001-reemplazo-elk-por-grafana-loki-prometheus.md` |
| D-2026-02 | Agente RUM con OTel JS SDK, bundle < 30KB, CORS con echo origin + Vary | Aceptado | specs + memoria rum-observability |
| D-2026-03 | Salud del usuario: User Health Score 0-100 con pesos configurables | Propuesto | backlog EPIC-ML |
| D-2026-04 | ~~Almacenamiento SQLite (WAL) con migración planificada a TimescaleDB~~ | **Superseded** por ADR-0009 | brief §4.1 |
| ADR-0009 | **Almacenamiento PostgreSQL + SQLModel en el MVP** (VM Rocky 10, Docker/Podman); TimescaleDB = extensión futura | **Aceptado** | `docs/adr/0009-postgresql-16-como-base-de-datos.md` |
| ADR-0010 | **Arquitectura de 4 contenedores** (`intellops-core`, `intellops-db`, `intellops-ai-engine`, `intellops-comms`); LGTM/Netdata/RAG fuera del MVP | **Aceptado** | `docs/adr/0010-arquitectura-de-4-contenedores.md` |
| D-2026-05 | ML baseline = Isolation Forest + Z-score + seasonal; LSTM como extensión | Aceptado (brief-v2) | brief §4.3 |
| D-2026-06 | GenIA = LLM local cuantizado 1B (privacidad, $0, reproducción) | Aceptado (brief-v2) | brief §5.2 |
| D-2026-07 | QA con quality gates OTel en CI/CD (latencia p99, error rate, trazas) | Propuesto | backlog EPIC-QA |
| D-2026-08 | Metodología: SDD + Scrum/Kanban híbrido + DevOps | Aceptado | TEAM_CHARTER, CONTRIBUTING |

**Regla**: toda decisión técnica nueva requiere ADR (`docs/adr/NNNN-titulo.md`). Sin ADR, la decisión no existe.

---

## 6. Atributos de Calidad (ISO/IEC 25010) — Target

| Atributo | Definición en IntellOps | Target | Métrica |
|---|---|---|---|
| Disponibilidad | Sistema 24/7 en hardware modesto | > 99.5% | Healthchecks + Netdata (post-MVP) |
| Escalabilidad | 1K → 10K métricas/s | Threshold 1K/s MVP | k6 benchmark |
| Seguridad | OWASP Top 10, CIS hardening | Sin vuln. críticas | Lynis ≥ 70%, ZAP |
| Usabilidad | SUS para 4 personas definidas | > 75 | Cuestionario n=10 |
| Mantenibilidad | Código limpio y testeable | Coverage ≥ 70% (80% ideal) | pytest + coverage |
| Portabilidad | Rebuild < 30 min | `docker compose up` | timing |
| Reproducibilidad | Specs cubren el 100% | ADRs + OAS + AsyncAPI | validación CI |
| Costo-eficiencia | Operación | $0/mes | tracking |
| Performance | Latencia de ingesta, detección | ingesta ≤ 500ms; detección < 5s | k6/Locust |
| Experiencia | Dashboard usable y comprensible | SUS > 75; Time-to-anomaly < 10s | UX testing |

---

## 7. Esquema de Datos y Contratos (resumen)

- **API**: OpenAPI 3.1 — núcleo implementado: `POST /telemetry/metrics`,
  `POST /telemetry/exceptions`, `GET /metrics/query`, `GET /metrics/list`, `/auth/*`,
  `/users`, `/applications`, `/alerts`, `/dashboard/*`, `/health`, `/ready`.
  Previstos post-MVP: `/anomalies`, `/predictions`, `/assistant/query`, `/rca`.
- **Eventos**: AsyncAPI 3.0 — `anomaly/detected`, `alert/triggered`, `user/health-degraded` (post-MVP).
- **Formato de métricas**: contadores internos (`snapshot()`) en el MVP; Prometheus exposition
  + OTLP quedan para post-MVP.
- **Trazado distribuido**: W3C Trace Context (post-MVP).
- **DDL** v1.0 (Federico): contrato de datos de ingesta RUM — ver `feat(specs)` en git history.

### 7.1. Métricas núcleo (definidas en `docs/research/Estrategia...`)

| Capa | Métrica | Target sugerido |
|---|---|---|
| UX | LCP | < 2.5s |
| UX | INP | < 200ms |
| UX | CLS | < 0.1 |
| UX | TTFB | < 800ms |
| Producto | Latencia API p95/p99 | < 200ms / < 500ms |
| Producto | Error rate | < 0.1% |
| Infra | CPU/Memoria hosts | umbrales por servicio |
| Infra | Disponibilidad | > 99.5% |
| Negocio | User Health Score | 0-100, alerta < 60 |
| IA | F1 anomalías | ≥ 0.70 |

---

## 8. Diagramas Complementarios

- `docs/der/derPlantUml.puml` — modelo entidad-relación (V2 multi-tenant, MLOps).
- `docs/infrastructure/Diagrama-C4-V2.puml` — **C4 de contenedores vigente (4 contenedores)**.
- `docs/infrastructure/c4_container_v1.puml` — versión histórica, conservada solo como referencia.
- Render: `plantuml -tpng`.

---

## 9. Siguiente Documento

→ `04-especificaciones.md` — requisitos funcionales, no funcionales y criterios de aceptación.

*Documento vivo.*