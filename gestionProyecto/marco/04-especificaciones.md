# IntellOps — Marco Conceptual: Especificaciones

**Documento**: `04-especificaciones.md`
**Parte del marco**: Marco Conceptual e Ingenieril de IntellOps
**Versión**: 1.0
**Fecha**: 2026-09-11
**Autor**: Coordinación InfraIT — Emanuel Rodríguez
**Estado**: Borrador para revisión del equipo
**Nota**: este documento es el **nivel de sistema** (qué debe cumplir IntellOps). Las specs detalladas por cambio
viven en `openspec/specs/**` y `openspec/changes/**` (SDD). Ninguna implementación procede sin spec validada.

---

## 1. Alcance

Esta especificación define requisitos funcionales y no funcionales **a nivel de sistema**, derivados del
objetivo (`01-objetivo.md`) y del diseño (`03-diseno.md`). Sirve de:
- **Contrato de aceptación** para el backlog (`05-backlog.md`).
- **Referencia de cumplimiento** para cada PPS (criterios de DoD).
- **Entrada** a specs SDD detalladas.

ID global: `INT-OBS-REQ` · Estándar de referencia: ISO/IEC/IEEE 29148 (estructura de SRS), ISO/IEC 25010 (calidad).

---

## 2. Requisitos Funcionales

### 2.1. RF-CAP · Captura de Telemetría

| ID | Requisito | Prioridad | Criterio de aceptación |
|---|---|---|---|
| RF-CAP-01 | El sistema debe capturar métricas de experiencia de usuario (Core Web Vitals: LCP, INP, CLS) desde el navegador mediante agente RUM | MUST | Bundle < 30KB gzip; overhead Lighthouse < 3% |
| RF-CAP-02 | El agente debe capturar TTFB, errores de frontend, navegación y metadata de sesión | MUST | Evento de error visible en dashboard < 60s |
| RF-CAP-03 | El agente debe exportar en OTLP hacia el OTel Collector | MUST | Trazas RUM visibles en Tempo |
| RF-CAP-04 | El sistema debe capturar métricas de infraestructura (CPU, memoria, red, disco) por scraping Prometheus | MUST | Scrape interval ≤ 15s |
| RF-CAP-05 | El sistema debe capturar logs de sistema y eventos de seguridad (Linux) | MUST | Auditbeat/Promtail envía a Loki |
| RF-CAP-06 | La instrumentación del backend (FastAPI) debe emitir trazas distribuidas OTel | MUST | Trace completa frontend→backend en Tempo |
| RF-CAP-07 | El envío de telemetría debe ser tolerante a fallos de red (buffer + retry) | SHOULD | Pérdida 0 en cortes < 60s |

### 2.2. RF-ING · Ingesta y Almacenamiento

| ID | Requisito | Prioridad | Criterio de aceptación |
|---|---|---|---|
| RF-ING-01 | API de ingesta `POST /metrics/ingest` validada contra OpenAPI 3.1 | MUST | Rechaza payloads inválidos con 400 + detalle |
| RF-ING-02 | Ingesta por batching (batch 30s, sampling 10% configurable) | MUST | Throughput ≥ 1K métricas/s |
| RF-ING-03 | Almacenamiento en PostgreSQL con SQLModel + índice temporal | MUST | Consulta ventana 1h < 500ms |
| RF-ING-04 | Trazas almacenadas en Tempo, logs en Loki, métricas en Prometheus | MUST | Correlación trace→log→metric operativa |
| RF-ING-05 | CORS con echo de origin (nunca `*`) + `Vary: Origin` (sendBeacon y credentials) | MUST | Envíos desde navegador sin bloqueo (ver memoria rum-observability) |
| RF-ING-06 | TimescaleDB como extensión activable de PostgreSQL sin reescribir la capa de consulta | SHOULD | Repositorios abstraídos tras interfaz; `CREATE EXTENSION timescaledb` documentado |

### 2.3. RF-ML · Inteligencia (AIOps)

| ID | Requisito | Prioridad | Criterio de aceptación |
|---|---|---|---|
| RF-ML-01 | Detección de anomalías sobre series temporales de las 3 capas (IF + Z-score + seasonal) | MUST | F1 ≥ 0.70 en dataset de validación |
| RF-ML-02 | Forecasting de degradación (estadístico; LSTM como extensión) | MUST | MAPE < 15% (baseline) |
| RF-ML-03 | User Health Score 0-100 por usuario/sesión con pesos configurables | MUST | Correlación con reclamos reales r > 0.75 |
| RF-ML-04 | Clasificación predictiva de reclamos (complemento del health score) | SHOULD | F1 ≥ 0.75 |
| RF-ML-05 | Reproducibilidad de experimentos (seed fijo, config versionada) | MUST | `make reproduce EXP-XXX` idempotente |
| RF-ML-06 | Las anomalías detectadas deben enriquecerse con contexto (métrica, capa, impacto UX estimado) | SHOULD | Payload de anomalía incluye contexto |
| RF-ML-07 | Tiempo de detección desde la ingesta hasta la marca de anomalía | MUST | < 5s |

### 2.4. RF-GEN · Asistente IA (RCA)

| ID | Requisito | Prioridad | Criterio de aceptación |
|---|---|---|---|
| RF-GEN-01 | Asistente conversacional con LLM local cuantizado (sin APIs externas) | MUST | Inferencia 5-10 tok/s en CPU |
| RF-GEN-02 | RCA asistido: consumir trazas Tempo + logs Loki + métricas para explicar causa raíz | MUST | Precisión factual ≥ 80% (revisión coordinador) |
| RF-GEN-03 | RAG sobre runbooks y documentación GIDAS | MUST | Consulta contextual responde con fuentes |
| RF-GEN-04 | Respuesta a consultas de forecasting/anomalías en lenguaje natural | SHOULD | "¿Por qué subió la latencia?" → explicación accionable |
| RF-GEN-05 | Generación de borradores de runbooks desde incidentes resueltos | SHOULD | Runbook editable post-incidente |

### 2.5. RF-ACT · Acción y Presentación

| ID | Requisito | Prioridad | Criterio de aceptación |
|---|---|---|---|
| RF-ACT-01 | Alertas con routing por severidad: alta→WhatsApp, media→Telegram, baja→Mail | MUST | Entrega < 30s canal configurado |
| RF-ACT-02 | Reglas de alerta combinando umbrales y score ML | MUST | Alerta si health score < 60 o anomalía score > 0.8 |
| RF-ACT-03 | Dashboard con 3 vistas: latencias tiempo real, heatmap UX, predicciones | MUST | Carga < 2s; las 3 vistas funcionales |
| RF-ACT-04 | Vista de seguridad: eventos de autenticación, accesos no autorizados, cambios críticos | MUST (módulo SEG) | 4 dashboards de seguridad |
| RF-ACT-05 | Asistente chat integrado al dashboard | SHOULD | Chat funcional < 1MB extra |
| RF-ACT-06 | Exportación de datos para investigación (CSV/notebook) | SHOULD | Dashboard público read-only anonimizado |

### 2.6. RF-SEG · Seguridad

| ID | Requisito | Prioridad | Criterio de aceptación |
|---|---|---|---|
| RF-SEG-01 | Hardening CIS Benchmark Level 1 sobre servidores Linux | MUST | Lynis ≥ 70% post-hardening |
| RF-SEG-02 | Playbooks Ansible versionados y validados en staging | MUST | `make hardening` idempotente |
| RF-SEG-03 | Observabilidad de eventos de seguridad (logs centralizados GLP) | MUST | Evento simulado detectado < 60s |
| RF-SEG-04 | OWASP Top 10 aplicado a la API | MUST | Sin hallazgos críticos en ZAP |
| RF-SEG-05 | Autenticación en API (API key) + rate limiting | MUST | 401 sin key; 429 al exceder |

### 2.7. RF-QA · Calidad y Proceso

| ID | Requisito | Prioridad | Criterio de aceptación |
|---|---|---|---|
| RF-QA-01 | Suite de tests: unitarios, integración, E2E, contract | MUST | Coverage ≥ 70% módulos críticos |
| RF-QA-02 | Pipeline CI/CD con stages: lint → unit → integration → contract → build → deploy-staging | MUST | Pipeline verde < 10 min |
| RF-QA-03 | Quality gates: coverage < 70% bloquea; lint warnings bloquean; OpenAPI inválido bloquea | MUST | PR bloqueado ante incumplimiento |
| RF-QA-04 | Synthetic user journeys instrumentados OTel (3 journeys críticos) | SHOULD | Trazas completas en Tempo por journey |
| RF-QA-05 | Quality gates OTel en CI: latencia p99 < 200ms, error rate < 0.1% | SHOULD | PR con degradación bloqueado |
| RF-QA-06 | Pruebas de carga: latencia de ingesta ≤ 500ms bajo carga estándar | MUST | k6/Locust reporte |
| RF-QA-07 | Chaos experiments controlados con rollback (latencia, fallo DB) | SHOULD | Reporte de impacto en health score |

### 2.8. RF-OPS · Operación y Sustentabilidad

| ID | Requisito | Prioridad | Criterio de aceptación |
|---|---|---|---|
| RF-OPS-01 | Despliegue con Docker Compose, rebuild < 30 min | MUST | `docker compose up` en máquina limpia |
| RF-OPS-02 | Backup automático diario a S3 free-tier (Rclone) | MUST | Restore probado 1×/mes |
| RF-OPS-03 | Self-monitoring del stack (Netdata) | MUST | Dashboard de salud del propio IntellOps |
| RF-OPS-04 | Costo operativo $0/mes con recursos existentes | MUST | Tracking mensual |
| RF-OPS-05 | SBOM + tag semántico + release notes por release | SHOULD | Release reproducible |

---

## 3. Requisitos No Funcionales (resumen por atributo)

| Atributo | Requisito | Target | Verificación |
|---|---|---|---|
| Rendimiento | API p95 | < 200ms | k6 (CI) |
| Rendimiento | Ingesta p99 | ≤ 500ms | k6 (CI) |
| Escalabilidad | Throughput | ≥ 1K métricas/s | k6 benchmark |
| Disponibilidad | Uptime del stack | > 99.5% | Netdata |
| Seguridad | Lynis compliance | ≥ 70% | Lynis en CI/semanal |
| Seguridad | OWASP | Sin críticos | ZAP scan |
| Usabilidad | SUS 4 personas | > 75 | Cuestionario |
| Mantenibilidad | Coverage | ≥ 70% | pytest-cov (gate) |
| Portabilidad | Setup | < 30 min | cronometrado |
| Reproducibilidad | Specs/algoritmos | 100% cubiertos | validación CI + DVC |
| Privacidad | Datos de usuarios | Anonimizados en público | revisión + política |

---

## 4. Contratos de Datos (resumen de nivel)

### 4.1. OpenAPI 3.1 (endpoints núcleo)

```
POST /metrics/ingest        → 202, valida MetricBatch (OTLP/Prometheus)
POST /logs/ingest           → 202, valida LogBatch
GET  /metrics/query?metric=&from=&to= → MetricSeries
POST /ml/detect             → AnomalyList (score, contexto, capa)
GET  /ml/health-score/:userId → 0-100 + factores
POST /assistant/query       → RCA/Explanación en lenguaje natural
POST /rca                   → IncidentID → RCA estructurado
GET  /alerts                → lista + estado; POST /alerts/config; PUT /alerts/{id}/ack
GET  /health | /ready       → liveness / readiness (incluye DB)
```

### 4.2. AsyncAPI 3.0 (eventos)

```
anomaly/detected      { metric, capa, score, timestamp, impacto_ux_estimado }
alert/triggered       { alerta_id, severidad, canal, timestamp }
user/health-degraded  { userId, score, factores_contribuyentes }
```

### 4.3. Métricas núcleo (Prometheus exposition + RUM)

| Nombre | Tipo | Fuente | Target |
|---|---|---|---|
| rum_lcp_seconds | gauge | RUM | < 2.5 |
| rum_inp_milliseconds | gauge | RUM | < 200 |
| rum_cls | gauge | RUM | < 0.1 |
| rum_ttfb_milliseconds | gauge | RUM | < 800 |
| http_latency_p95/p99 | histogram | FastAPI/OTel | < 200/500ms |
| http_error_rate | counter | FastAPI/OTel | < 0.1% |
| infra_cpu/mem/net | gauge | Prometheus | por servicio |
| user_health_score | gauge | ML Engine | 0-100 |
| anomaly_score | gauge | ML Engine | alarma > 0.8 |

---

## 5. Matriz de Trazabilidad Requisitos → Objetivos → PPS

| Épica (backlog) | Requisitos | Objetivo IntellOps | PID | Contributor |
|---|---|---|---|---|
| EPIC-RUM | RF-CAP-01..04, RF-ING-05 | IO1 | OE1 | Federico (Fase 2) |
| EPIC-ING | RF-CAP-05..07, RF-ING-01..06 | IO2 | OE1, OE3 | Transversal |
| EPIC-ML | RF-ML-01..07 | IO3, IO4 | OE2 | Romeo |
| EPIC-RCA | RF-GEN-01..05 | IO4 | OE2, OE4 | Romeo (Fase 2) |
| EPIC-SEG | RF-SEG-01..05, RF-CAP-05 | IO6 | OE3, OE4 | Federico |
| EPIC-QA | RF-QA-01..07 | IO6 | OE3, OE4 | Santiago |
| EPIC-DASH | RF-ACT-01..06, RF-ACT-03 | IO5 | OE2, OE4 | Romeo + Ema |
| EPIC-EVAL | IO7, RF-OPS | IO7 | OE4 | Ema/Coordinación |

---

## 6. Criterios de Aceptación del Sistema (Definition of Done — nivel sistema)

| Criterio | Verificación |
|---|---|
| Las 3 capas de telemetría capturan y correlacionan señales | Demo end-to-end: usuario→dashboard |
| ML detecta anomalía simulada y la alerta llega al canal correcto < 30s | Prueba de humo integrada |
| Health Score calculado y correlacionado con datos reales | r > 0.75 en evaluación |
| CI/CD verde con gates en todos los PR del último ciclo | Pipeline log |
| Hardening aplicado con Lynis ≥ 70% | Informe de cumplimiento |
| Documentación completa: ADRs, specs, guías de onboarding | Revisión coordinador |
| Insumo publicable por módulo | Outline de paper por módulo |

---

## 7. Siguiente Documento

→ `05-backlog.md` — backlog de producto priorizado y listo para estimar.

*Documento vivo. Los requisitos detallados viven en openspec; este documento es el contrato de sistema.*