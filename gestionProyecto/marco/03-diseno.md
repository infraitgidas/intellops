# IntellOps — Marco Conceptual: Diseño

**Documento**: `03-diseno.md`
**Parte del marco**: Marco Conceptual e Ingenieril de IntellOps
**Versión**: 1.0
**Fecha**: 2026-09-11
**Autor**: Coordinación InfraIT — Emanuel Rodríguez
**Estado**: Borrador para revisión del equipo

---

## 1. Visión de Arquitectura (vista sistémica)

Intelops se diseña como **arquitectura de capas con flujo causal descendente y retroalimentación ascendente**,
materializando el lazo de control definido en el análisis:

```
 ╔══════════════════════════════════════════════════════════════════════╗
 ║  CAPA DE EXPERIENCIA — Frontend del producto software                ║
 ║  Apps web/servicios de GIDAS + apps de organizaciones adoptantes     ║
 ╚═══════════════════════════════╤══════════════════════════════════════╝
                                 │ Agente RUM (JS, <30KB, OTel)
                                 ▼
 ╔══════════════════════════════════════════════════════════════════════╗
 ║  CAPA DE INGESTA Y TRANSPORTE                                        ║
 ║  OTel Collector (recepciona OTLP: trazas, métricas, logs)            ║
 ║  + FastAPI (API de ingesta, validación OpenAPI, batching)            ║
 ╚═══════════════════════════╤══════════════════════════════╤═══════════╝
                             │                             │
          ┌──────────────────▼──────────┐   ┌──────────────▼───────────┐
          │  CAPA DE ALMACENAMIENTO     │   │  CAPA DE SEÑALES DE INFRA │
          │  PostgreSQL + SQLModel      │   │  Métricas: Prometheus     │
          │  (SQLModel/Alembic, time-   │   │  Logs: Loki (Promtail)    │
          │   index; TimescaleDB como   │   │  Seguridad: CIS/hardening │
          │   extensión futura)         │   └──────────────┬───────────┘
          │  + Grafana LGTM:            │                  │
          │   · Trazas → Tempo          │                  │
          │   · Logs   → Loki           │                  │
          │   · Alerts → Alertmanager   │                  │
          └──────────────┬──────────────┘                  │
                         │                                 │
                         └──────────────┬──────────────────┘
                                        ▼
 ╔══════════════════════════════════════════════════════════════════════╗
 ║  CAPA DE INTELIGENCIA (AIOps)                                        ║
 ║  ML Engine (scikit-learn):                                           ║
 ║   · Detection: Isolation Forest + Z-score + seasonal                 ║
 ║   · Forecasting: estadístico (Holt-Winters)                          ║
 ║   · User Health Score (correlación telemetría → experiencia)         ║
 ║  GenIA: LLM local cuantizado (Llama 3.2 1B, llama.cpp)               ║
 ║   · RCA asistido + RAG sobre runbooks/docs GIDAS                     ║
 ║   · Explicación de anomalías en lenguaje natural                     ║
 ╚═══════════════════════════════╤══════════════════════════════════════╝
                                 │
                                 ▼
 ╔══════════════════════════════════════════════════════════════════════╗
 ║  CAPA DE ACCIÓN Y PRESENTACIÓN                                       ║
 ║  Dashboard (React + D3): latencias, heatmap UX, predicciones, chat   ║
 ║  Alertas multicanal: Alertmanager → Mail / Telegram / WhatsApp       ║
 ║  Asistente conversacional (RCA en lenguaje natural)                  ║
 ╚═══════════════════════════════╤══════════════════════════════════════╝
                                 │ Retroalimentación
                                 ▼
 ║  CAPA DE GOBIERNO Y CALIDAD (transversal)                            ║
 ║  CI/CD (GitHub Actions) · tests (unit/integration/E2E/contract)      ║
 ║  Quality gates (coverage ≥70%, lint 0, OTel gates) · ADRs · specs    ║
 ╚══════════════════════════════════════════════════════════════════════╝
```

---

## 2. Arquitectura de Contenedores (C4 nivel container)

Basado en `openspec/specs/architecture/containers.md` y la decisión GLP del ADR-0001:

| Contenedor | Tecnología | Responsabilidad | Recursos |
|---|---|---|---|
| **RUM Agent** | JS OTel SDK | Captura LCP/INP/CLS, TTFB, errores, sesiones | < 30KB bundle |
| **Ingest API** | FastAPI + Uvicorn | `/metrics/ingest`, validación, batching, CORS (echo origin) | < 100MB RAM |
| **OTel Collector** | OpenTelemetry Collector | Recepción OTLP, enrutamiento a Tempo/Loki/Prometheus | < 256MB RAM |
| **Trazas** | Grafana Tempo | Almacenamiento y consulta de trazas distribuidas | < 256MB RAM |
| **Logs** | Grafana Loki + Promtail | Logs de sistema y seguridad | bajo |
| **Métricas** | Prometheus (o Mimir si escala) | Scraping y almacenamiento de métricas | bajo |
| **Dashboard** | Grafana + React static | Single pane of glass; dashboards de las 3 capas | < 1MB bundle |
| **Alertas** | Grafana Alertmanager | Routing por severidad → Mail/Telegram/WhatsApp | bajo |
| **ML Engine** | scikit-learn | Detección/forecast/health-score en batch y streaming | < 50MB RAM |
| **LLM Server** | llama.cpp + Llama 3.2 1B GGUF | RCA asistido, RAG, chat | ~600MB RAM |
| **RAG** | sentence-transformers + Chroma | Vectorización de docs/runbooks | < 200MB |
| **PostgreSQL buffer/storage** | PostgreSQL 16+ + SQLModel | Buffer de ingesta + almacenamiento; TimescaleDB como extensión futura | ~200-500MB |
| **Self-monitoring** | Netdata | Monitoreo del propio stack (<5% CPU) | < 150MB |
| **Backup** | Rclone + S3 free-tier | Respaldo incremental diario | 5GB limit |

**Footprint total del sistema**: ~2-3 GB RAM (PostgreSQL incluido) · < 2 cores · < 10GB disco · **$0/mes**.

---

## 3. Ciclo de Control Operacional (cómo funciona el lazo en runtime)

```
1. CAPTURA    Agente RUM en apps + agentes OTel en backend + Promtail en infra
              → envían telemetría (OTLP / Prometheus exposition)
2. INGESTA    OTel Collector normaliza y enruta; FastAPI valida contra OpenAPI
              → almacena en PostgreSQL (SQLModel) + Tempo + Loki + Prometheus
3. ANÁLISIS   ML Engine detecta anomalías (IF + z-score + seasonal) en las 3 capas
              → Health Score por usuario/sesión; forecast de degradación
4. DIAGNÓSTICO LLM+ RAG explica: "qué pasó, por qué, qué impacto en UX" (RCA)
5. ACCIÓN     Alertas con severidad → canal adecuado; dashboard actualizado;
              asistente responde consultas en lenguaje natural
6. APRENDIZAJE Feedback al backlog de desarrollo (incidentes → mejoras);
              datos para papers y experimentos (DVC/MLflow)
```

Cada ciclo apunta a **anticipar** (forecast + health score) antes que a **reaccionar** (alertas).

---

## 4. Módulos de Ingeniería (asignables a contributors)

La arquitectura se organiza en módulos que **mapean 1:1 con las PPS** (acoplamiento buscado):

| Módulo | Alcance | Contributor natural (PPS) | Backlog épica |
|---|---|---|---|
| **M-SEG** Seguridad & Eventos | Hardening CIS, observabilidad de eventos (GLP), dashboards de seguridad | Federico (PPS Módulo Seguridad) | EPIC-SEG |
| **M-RUM** Telemetría UX | Agente RUM, correlación UX, journeys | Federico (Fase 2) + Ema | EPIC-RUM |
| **M-ML** IA / AIOps | Detección anomalías, forecast, health score, clasificación reclamos | Romeo (PPS ML) | EPIC-ML |
| **M-RCA** Asistente IA | LLM local, RAG, RCA, chat | Romeo (Fase 2) | EPIC-ML / EPIC-RCA |
| **M-QA** Calidad & CI/CD | Tests, pipeline, quality gates, synthetic journeys, chaos | Santiago (PPS QA) | EPIC-QA |
| **M-ING** Ingesta & Storage | API, PostgreSQL (SQLModel), OTel Collector, Tempo/Loki/Prometheus | Transversal (todos tocan) | EPIC-ING |
| **M-DASH** Dashboard | Vistas latencias/heatmap/predicciones, chat | Romeo + Ema | EPIC-DASH |

**Principio de asignación**: cada PPS entrega un módulo funcional completo con DoD cumplido → el
producto final emerge de la integración de módulos independientes y ordenados (no de un monstruo
compartido).

---

## 5. Decisiones Arquitectónicas Clave (resumen + ADRs)

| # | Decisión | Estado | Referencia |
|---|---|---|---|
| ADR-0001 | Reemplazo ELK → Grafana + Loki + Prometheus (licencia SSPL) | Aceptado | `docs/adr/0001-reemplazo-elk-por-grafana-loki-prometheus.md` |
| D-2026-02 | Agente RUM con OTel JS SDK, bundle < 30KB, CORS con echo origin + Vary | Aceptado | specs + memoria rum-observability |
| D-2026-03 | Salud del usuario: User Health Score 0-100 con pesos configurables | Propuesto | backlog EPIC-ML |
| D-2026-04 | ~~Almacenamiento SQLite (WAL) con migración planificada a TimescaleDB~~ | **Superseded** por ADR-0002 | brief §4.1 |
| ADR-0002 | **Almacenamiento PostgreSQL + SQLModel en el MVP** (VM Rocky 10, Docker/Podman); TimescaleDB = extensión futura | **Aceptado** | `docs/adr/0002-reemplazo-sqlite-por-postgresql.md` |
| D-2026-05 | ML baseline = Isolation Forest + Z-score + seasonal; LSTM como extensión | Aceptado (brief-v2) | brief §4.3 |
| D-2026-06 | GenIA = LLM local cuantizado 1B (privacidad, $0, reproducción) | Aceptado (brief-v2) | brief §5.2 |
| D-2026-07 | QA con quality gates OTel en CI/CD (latencia p99, error rate, trazas) | Propuesto | backlog EPIC-QA |
| D-2026-08 | Metodología: SDD + Scrum/Kanban híbrido + DevOps | Aceptado | TEAM_CHARTER, CONTRIBUTING |

**Regla**: toda decisión técnica nueva requiere ADR (`docs/adr/NNNN-titulo.md`). Sin ADR, la decisión no existe.

---

## 6. Atributos de Calidad (ISO/IEC 25010) — Target

| Atributo | Definición en IntellOps | Target | Métrica |
|---|---|---|---|
| Disponibilidad | Sistema 24/7 en hardware modesto | > 99.5% | Netdata uptime |
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

- **API**: OpenAPI 3.1 — `POST /metrics/ingest`, `POST /logs/ingest`, `GET /metrics/query`,
  `POST /ml/detect`, `GET /ml/health-score/:userId`, `POST /assistant/query`, `POST /rca`.
- **Eventos**: AsyncAPI 3.0 — `anomaly/detected`, `alert/triggered`, `user/health-degraded`.
- **Formato de métricas**: Prometheus exposition + OTLP (OpenTelemetry).
- **Trazado distribuido**: W3C Trace Context.
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
- `docs/infrastructure/c4_container_v1.puml` — C4 de contenedores.
- `../diagramas/diagrama-actividades.puml` — **diagrama de actividades del proceso de desarrollo** (este marco).
- Render: `plantuml -tpng`.

---

## 9. Siguiente Documento

→ `04-especificaciones.md` — requisitos funcionales, no funcionales y criterios de aceptación.

*Documento vivo.*