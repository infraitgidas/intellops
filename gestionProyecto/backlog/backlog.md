# IntellOps — Backlog de Producto Priorizado

**Documento**: `05-backlog.md`
**Parte del marco**: Marco Conceptual e Ingenieril de IntellOps
**Versión**: 1.0
**Fecha**: 2026-09-11
**Autor**: Coordinación InfraIT — Emanuel Rodríguez
**Estado**: Listo para estimar (planning poker a coordinar con el equipo)

---

## 1. Cómo Leer Este Backlog

- **Épicas** (E##): grandes cuerpos de trabajo que generan valor por sí mismos; mapean a módulos del diseño.
- **Historias (US-##)**: requisitos funcionales de usuario con criterio de aceptación.
- **Tareas (T-##)**: unidades implementables (≈ 0.5-2 días de un PPS de 10 hs/semana).
- **Prioridad**: MoSCoW — M(Must) / S(Should) / C(Could) / W(Won't-esta-fase).
- **Estimación**: **no asignada** (se estimará en planning poker). Columna "Talla sugerida" = referencia (S<8hs, M<16hs, L<40hs, XL>40hs) — NO es estimación final.
- **Owner sugerido**: F=Federico, R=Romeo, S=Santiago, X=transversal/coordinación.
- **Valor**: deriva de los objetivos IO1-IO7 del `01-objetivo.md`.

**Nota de priorización (WSJF cualitativo)**: Must = alta probabilidad de riesgo si no está (CVaR), Source de
bloqueo para otras épicas, y/o valor diferencial núcleo. El orden de ejecución sugerido es el del tablero,
pero el equipo decide.

---

## 2. Épicas

| ID | Épica | Módulo | Objetivo | Prioridad | Tallas totales (ref.) | Owner |
|---|---|---|---|---|---|---|
| E01 | Fundaciones: repo, CI base, infraestructura de desarrollo | — | IO6 | M | M | X |
| E02 | Captura UX (RUM) | M-RUM | IO1 | M | XL | F+X |
| E03 | Ingesta y almacenamiento | M-ING | IO2 | M | XL | X |
| E04 | Detección de anomalías y health score | M-ML | IO3, IO4 | M | XL | R |
| E05 | Dashboard 3 vistas + correlación | M-DASH | IO5 | M | L | R+X |
| E06 | Alertas multicanal | M-ACT | IO5 | S | M | X |
| E07 | Seguridad: hardening CIS + eventos | M-SEG | IO6 | M | XL | F |
| E08 | Quality gates + pipeline CI/CD real | M-QA | IO6 | M | L | S |
| E09 | Testing automatizado (unit/integration/contract) | M-QA | IO6 | M | XL | S |
| E10 | Asistente GenIA + RCA (LLM local + RAG) | M-RCA | IO4 | S | XL | R |
| E11 | Observability-Driven QA (synthetic journeys + gates OTel) | M-QA | IO6 | S | M | S |
| E12 | Evaluación de impacto y transferencia (papers, docs) | — | IO7 | S | L | X |

---

## 3. Historias y Tareas por Épica

### E01 — Fundaciones (Must)
> Prep: `make` targets, CI base, convenciones, estructura de repo. El plan de trabajo existente ya la deja esbozada.

| ID | Historia / Tarea | Prioridad | Talla ref. | Owner | Depende de |
|---|---|---|---|---|---|
| US-001 | Como contributor, quiero clonar el repo y levantar el stack con `make up` para empezar a trabajar sin fricción | M | M | X | — |
| T-001.1 | Definir estructura de carpetas estándar (ya documentada en docs/infrastructure) y `.env.example` | M | S | X | — |
| T-001.2 | Makefile con targets: `make up`, `make test`, `make lint`, `make test-cov`, `make hardening`, `make reproduce` | M | M | X | T-001.1 |
| T-001.3 | GitHUb Actions base: lint + unit test verdes en todo PR | M | M | X | T-001.2 |
| US-002 | Como coordinador, quiero ADR-0001 reflejado en toda la documentación y planes para que el stack sea consistente (GLP) | M | S | X | — |
| T-002.1 | Auditoría de referencias "ELK" en docs/ y RRHH/ y unificación a GLP | M | S | X | — |

### E02 — Captura UX / RUM (Must) — IO1
> El agente RUM ya tiene prototipo funcional (memoria rum-observability: CORS echo origin, flush manual, tests core). Aquí se productiviza.

| ID | Historia / Tarea | Prioridad | Talla ref. | Owner | Depende de |
|---|---|---|---|---|---|
| US-010 | Como usuario web de una app GIDAS, el sistema debe medir mi experiencia (LCP, INP, CLS, TTFB) sin que yo note nada (overhead < 3%) | M | XL | F | E01 |
| T-010.1 | Productivizar agente RUM: bundle < 30KB gzip, configuración vía script tag | M | M | F | prototipo existente |
| T-010.2 | Colectores: web-vitals, navigation (TTFB), errors, session | M | M | F | T-010.1 |
| T-010.3 | Transporte OTLP con batching 30s y retry; sendBeacon+credentials con CORS echo origin | M | M | F+X | T-010.1 |
| T-010.4 | Test suite del agente (unit + browser) con fixtures | M | M | F | T-010.2 |
| US-011 | Como desarrollador, quiero ver las métricas RUM en el dashboard para monitorear UX en tiempo real | S | M | X | T-010.2, E05 |
| US-012 | Como investigador, quiero exportar datos RUM crudos para análisis | C | S | X | E03 |

### E03 — Ingesta y Almacenamiento (Must) — IO2

| ID | Historia / Tarea | Prioridad | Talla ref. | Owner | Depende de |
|---|---|---|---|---|---|
| US-020 | Como sistema, debo aceptar métricas/logs/trazas OTLP y Prometheus de las 3 capas validando contra OpenAPI | M | XL | X | E01 |
| T-020.1 | `POST /metrics/ingest` con validación OpenAPI 3.1 + batching | M | M | X | E01 |
| T-020.2 | `POST /logs/ingest` (logs estructurados; GLP via Promtail) | M | M | X/S | T-020.1 |
| T-020.3 | PostgreSQL + SQLModel + Alembic (migraciones versionadas); repositorios con interfaz para TimescaleDB como extensión; índice temporal | M | M | X | T-020.1 |
| T-020.4 | OTel Collector: recepción OTLP, enrutamiento a Tempo/Loki/Prometheus | M | M | X | T-020.1 |
| T-020.5 | CORS echo origin + Vary: Origin; auth API key + rate limiting | M | S | X | T-020.1 |
| T-020.6 | Contract tests (schemathesis) ≥ 80% endpoints | M | M | S | T-020.1, E08 |
| US-021 | Como analista, quiero consultar series temporales por rango con agregación (< 500ms) | M | M | X | T-020.3 |
| US-022 | Como sistema, debo tolerar cortes de red del agente (buffer + retry) | S | S | X | T-020.1 |

### E04 — Detección de Anomalías y Health Score (Must) — IO3/IO4
> Es el corazón del valor diferencial. Baseline liviano primero (IF+z-score+seasonal); health score como "moneda" de valor de negocio.

| ID | Historia / Tarea | Prioridad | Talla ref. | Owner | Depende de |
|---|---|---|---|---|---|
| US-030 | Como SRE, quiero detectar anomalías en métricas de las 3 capas (F1 ≥ 0.70) para anticipar fallas | M | XL | R | E03 |
| T-030.1 | Esqueleto ML Engine: `base.py` (Detector abstracto), pipeline train/predict/eval | M | M | R | E01 |
| T-030.2 | Detector Isolation Forest sobre series de las 3 capas | M | L | R | T-030.1 |
| T-030.3 | Detector Z-score dinámico + seasonal decomposition; ensamble (voting) | M | M | R | T-030.2 |
| T-030.4 | Endpoint `POST /ml/detect` → `AnomalyList` (metric, capa, score, timestamp, impacto_ux_estimado) | M | M | R | T-030.2 |
| T-030.5 | EDA sobre datos reales del laboratorio + experimento versionado EXP-001 (seed fijo, `make reproduce`) | M | M | R | T-030.2 |
| US-031 | Como organización, quiero un User Health Score (0-100) por usuario para traducir telemetría en valor de negocio | M | L | R | T-030.4 |
| T-031.1 | Algoritmo health score: pesos configurables (CWV, latencia, error rate, infra) | M | M | R | T-030.4 |
| T-031.2 | Endpoint `GET /ml/health-score/:userId` + persistencia | M | M | R | T-031.1 |
| T-031.3 | Validación de correlación con reclamos reales (r > 0.75) + doc | S | M | R | T-031.2 |
| US-032 | Como investigador, quiero reproducibilidad de experimentos (config versionada, resultados exportables) | M | M | R | E01 |
| US-033 | [Extensión] Como SRE, quiero forecasting de degradación (MAPE < 15%) para anticipar mañana | C | L | R | T-030.3 |

### E05 — Dashboard 3 Vistas (Must) — IO5

| ID | Historia / Tarea | Prioridad | Talla ref. | Owner | Depende de |
|---|---|---|---|---|---|
| US-040 | Como usuario del dashboard, quiero ver latencias en tiempo real (vista 1) | M | L | R+X | E03 |
| US-041 | Como usuario, quiero heatmap UX de comportamiento (vista 2) | M | M | R+X | US-010, E03 |
| US-042 | Como usuario, quiero panel de predicciones/anomalías (vista 3) | M | M | R+X | T-030.4 |
| T-040.1 | React static build + Vite + D3; bundle < 1MB | M | M | R+X | — |
| T-040.2 | Vistas + servicios API (polling) + estados de carga skeleton | M | L | R+X | T-040.1 |
| T-040.3 | Dashboard público read-only anonimizado (extensión/visita) | C | M | X | T-040.2 |

### E06 — Alertas Multicanal (Should) — IO5

| ID | Historia / Tarea | Prioridad | Talla ref. | Owner | Depende de |
|---|---|---|---|---|---|
| US-050 | Como SRE, quiero alertas por severidad: alta→WhatsApp, media→Telegram, baja→Mail (< 30s) | S | M | X | E04 |
| T-050.1 | Grafana Alertmanager con routing por severidad + templates | S | M | X | E03 |
| T-050.2 | Reglas combinadas: umbral + health score < 60 / anomaly score > 0.8 | S | M | X | E04, T-050.1 |
| T-050.3 | Demo de alerta a los 3 canales + medición de latencia | S | S | X | T-050.1 |

### E07 — Seguridad (Must, PPS Federico) — IO6

| ID | Historia / Tarea | Prioridad | Talla ref. | Owner | Depende de |
|---|---|---|---|---|---|
| US-060 | Como administrador, quiero el laboratorio endurecido según CIS Level 1 (Lynis ≥ 70%) | M | L | F | — |
| T-060.1 | Auditoría baseline: Lynis + OpenSCAP + informe (documento) | M | S | F | — |
| T-060.2 | Hardening CIS con playbooks Ansible versionados; validación staging | M | L | F | T-060.1 |
| T-060.3 | Informe post-hardening (Lynis score antes/después) — insumo paper | M | S | F | T-060.2 |
| US-061 | Como SOC (equipo), quiero logs de seguridad centralizados y dashboards (autenticación, accesos no autorizados, cambios críticos) | M | XL | F | ADR-0001 |
| T-061.1 | Pipeline GLP seguridad: Promtail/auditbeat → Loki; etiquetas estándar (`event.type`, `host`, `severity`) | M | L | F | ADR-0001, E03 |
| T-061.2 | 4 dashboards Grafana de seguridad exportados como JSON versionados | M | L | F | T-061.1 |
| T-061.3 | Contrato de datos de eventos (schema) publicado para consumo por E04 | M | S | F | T-061.1 |
| T-061.4 | Prueba de detección de evento simulado (< 60s) + benchmark de herramientas sobre GLP | M | M | F | T-061.1 |
| US-062 | Como desarrollador de IntellOps, quiero la API protegida (API key, rate limit, OWASP) | S | M | X | E03, E07 |

### E08 — Quality Gates + Pipeline CI/CD Real (Must, PPS Santiago) — IO6

| ID | Historia / Tarea | Prioridad | Talla ref. | Owner | Depende de |
|---|---|---|---|---|---|
| US-070 | Como equipo, quiero CI verde real en GitHub Actions con stages: lint → unit → integration → contract → build (pipeline < 10 min) | M | L | S | E01 |
| T-070.1 | Corregir/habilitar `.github/workflows/ci.yml` completo | M | M | S | E01 |
| T-070.2 | Jobs: contract testing + license-scan (reutilizando lo existente) + coverage artifact | M | M | S | T-070.1 |
| US-071 | Como equipo, quiero quality gates que bloqueen PRs (coverage < 70%, lint warnings, OpenAPI inválido) | M | L | S | T-070.1 |
| T-071.1 | Implementar gates con reporte automático + badges en README | M | M | S | T-070.2 |
| T-071.2 | Entornos de testing reproducibles (Docker Compose) por PR | M | M | S | T-070.1 |
| US-072 | Como coordinador, quiero informe de rendimiento baseline del sistema | S | M | S | E03, E08 |

### E09 — Testing Automatizado (Must, PPS Santiago) — IO6

| ID | Historia / Tarea | Prioridad | Talla ref. | Owner | Depende de |
|---|---|---|---|---|---|
| US-080 | Como equipo, quiero tests unitarios y de integración de la API (coverage ≥ 70% módulos críticos) | M | XL | S | E08 |
| T-080.1 | Suite unitaria: normalización de métricas, lógica de ingesta, transformaciones | M | L | S | E08 |
| T-080.2 | Integración API REST: contratos, bordes, manejo de errores, mocks | M | L | S | T-080.1 |
| T-080.3 | E2E del flujo completo: captura → ingesta → almacenamiento → consulta → dashboard (≥ 3 escenarios) | M | L | S | E02, E03, E05 |
| T-080.4 | Pruebas de carga: latencia ingesta ≤ 500ms bajo carga estándar (k6/Locust) | M | M | S | T-080.3 |

### E10 — Asistente GenIA + RCA (Should, PPS Romeo Fase 2) — IO4

| ID | Historia / Tarea | Prioridad | Talla ref. | Owner | Depende de |
|---|---|---|---|---|---|
| US-090 | Como SRE, quiero que IntellOps me explique "qué pasó y por qué" en lenguaje natural (RCA) | S | XL | R | E04, E03 |
| T-090.1 | LLM local cuantizado (Llama 3.2 1B, llama.cpp, ~600MB) vía servicio | S | L | R | — |
| T-090.2 | RAG: vectorización de runbooks/docs GIDAS (Chroma + sentence-transformers) | S | M | R | T-090.1 |
| T-090.3 | Agente RCA: consumo de trazas Tempo + logs Loki + métricas → respuesta estructurada (precisión ≥ 80%) | S | L | R | T-090.2, E04 |
| T-090.4 | Endpoint `POST /rca` y `POST /assistant/query` + evaluación | S | M | R | T-090.3 |
| T-090.5 | Generación de borradores de runbooks desde incidentes | C | S | R | T-090.4 |

### E11 — Observability-Driven QA (Should, PPS Santiago Fase 2) — IO6

| ID | Historia / Tarea | Prioridad | Talla ref. | Owner | Depende de |
|---|---|---|---|---|---|
| US-100 | Como equipo, quiero synthetic journeys instrumentados OTel que generen trazas validadas en Tempo | S | M | S | E02, E03, E08 |
| T-100.1 | 3 journeys (login+consulta, carga dashboard, reporte de error) con Locust+OTel | S | M | S | E02, E03 |
| T-100.2 | Validación de trazas completas en Tempo por journey | S | S | S | T-100.1 |
| US-101 | Como equipo, quiero gates OTel en CI: latencia p99 < 200ms, error rate < 0.1% bloquean PRs | S | M | S | T-100.1, E04 |
| US-102 | Como investigador, quiero experimentos de caos controlados (latencia, fallo DB) con reporte de impacto en health score | C | L | S | T-031.1, T-100.2 |

### E12 — Evaluación y Transferencia (Should) — IO7

| ID | Historia / Tarea | Prioridad | Talla ref. | Owner | Depende de |
|---|---|---|---|---|---|
| US-110 | Como dirección GIDAS, quiero documentar impacto y metodología para publicar | S | L | X | Todo |
| T-110.1 | Paper base por módulo (F: seguridad GLP; R: ML+health score; S: QA+observability) | S | M | F/R/S | E07/E04/E11 |
| T-110.2 | Informe de impacto (antes/después, métricas) para el PID | S | M | X | E12 |
| T-110.3 | Guías de onboarding actualizadas + wiki | S | S | X | — |
| T-110.4 | CBA de observabilidad (dashboard de costo-beneficio: incidentes evitados, MTTR) | C | M | S | E04, E06 |

---

## 4. Orden de Ejecución Sugerido (por oleadas)

```
OLEADA 1 — Cimientos (sem 1-4)          E01, E03 (parcial), E08, E07 (parcial)
OLEADA 2 — Núcleo de valor (sem 5-10)   E02, E04, E09, E07 (cierre)
OLEADA 3 — Presentación (sem 11-16)     E05, E06, E11
OLEADA 4 — IA y transferencia (17-20)   E10, E12
```

**Lógica**: primero infraestructura y contratos (para que todos desarrollen contra specs), luego el
núcleo de valor (RUM + anomalías + health score + QA), luego la presentación/acción, y finalmente la
capa GenIA (que es la de mayor incertidumbre, por eso se difiere).

---

## 5. Notas de Estimación

- **Unidad**: horas efectivas de PPS (10 hs/semana por contributor). Talla ref.: S ≤ 8hs, M ≤ 16hs, L ≤ 40hs, XL > 40hs.
- Estimación formal: **planning poker** en el taller de alineación (acción #6 del `../equipo/analisis-pps-acoplamiento.md`).
- Los ítems **Must** suman el MVP-0/MVP-1 del brief; los **Should** el MVP-2; los **Could** son extensión.
- Validar al estimar: dependencia de prototipos existentes (agente RUM en rum-observability), no contarlos como desde cero.

---

## 6. Definición de Listo (Ready para Sprint)

Un ítem está *listo* cuando:
- [ ] Tiene criterio de aceptación verificable (de `04-especificaciones.md`)
- [ ] Su contrato de datos (consumido/producido) está publicado
- [ ] Owner asignado y dependencias despejadas
- [ ] Está estimado (puntos/horas de consenso)
- [ ] Su spec SDD puede escribirse en < 1 día (si aplica)

---

*Documento vivo. La priorización se revalida cada sprint review.*