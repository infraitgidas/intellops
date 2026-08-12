# Informe de Avance 1 — rodriguezemautn (Emanuel Rodriguez)

> **Rol**: Investigador principal / Arquitecto de software
> **Período**: 27 de mayo — 11 de junio de 2026
> **Commits**: 14
> **Líneas de contenido generado**: ~4.800+

---

## 1. Actividades de Investigación

### 1.1. Reorientación I+D+i hacia Observabilidad UX-Céntrica
Lideró el cambio de paradigma del proyecto: de una visión centrada en infraestructura (monitorear servidores) a una centrada en el usuario real (observabilidad de experiencia). Esto implicó:
- Reformulación de hipótesis de investigación (agregó H5: User Telemetry, H6: AI Agents, H7: Obs-Driven QA)
- Definición de 12 nuevos experimentos organizados en EXP-OTel, EXP-AI, EXP-QA
- Reestructuración del onboarding en Fase 1 (fundamentos de infra) + Fase 2 (UX-céntrica)
- Actualización del plan de trabajo con tareas concretas por contributor

### 1.2. Estado del Arte de Frontend Observability
Documento de investigación de **929 líneas** que cubre:
- Core Web Vitals (LCP, INP, CLS) y métricas complementarias (TTFB, FCP, TBT, Long Tasks)
- RED method (Rate, Errors, Duration) adaptado a frontend
- RUM (Real User Monitoring) vs Synthetic Monitoring — cuándo y cómo usar cada uno
- Correlación de señales frontend-backend mediante tracing distribuido
- Análisis predictivo con User Health Score
- Geolocalización de métricas para detectar problemas regionales
- **30+ referencias bibliográficas** formales (W3C, Google Chrome Team, papers académicos)
- Catálogo de herramientas del mercado (Datadog RUM, Grafana Faro, OpenTelemetry Browser SDK)

### 1.3. Investigación de Agentes RUM
Documento técnico de **1.207 líneas** — el más extenso del proyecto:
- Anatomía completa de un agente RUM runtime JavaScript
- 10+ Browser APIs analizadas con implementación (`PerformanceObserver`, `Navigation Timing`, `Paint Timing`, `Event Timing`, `Layout Instability`, `Long Tasks`, `Network Information`, `sendBeacon`, `Page Visibility`, `Device Memory`)
- Cálculo detallado de cada métrica con código de implementación real
- Arquitectura interna del OpenTelemetry Browser SDK
- Análisis de bundles existentes (Datadog RUM ~50KB, Dynatrace RUM ~35KB, Grafana Faro ~25KB, OpenTelemetry ~12KB base)
- Estrategias de optimización: tree-shaking, lazy loading, custom exporter
- Arquitectura propuesta para el agente RUM de IntellOps con estructura de archivos y plan de implementación en 5 fases

### 1.4. Análisis de Herramientas de Observabilidad
Documento de **845 líneas** con:
- Análisis detallado de 12 plataformas (Datadog, Grafana LGTM, New Relic, Dynatrace, Splunk, SigNoz, OpenObserve, Netdata, Uptrace, HyperDX, Sentry, Elastic)
- Matrices comparativas avanzadas (general, RUM/frontend, AI/ML)
- 6 tendencias de industria 2025-2026 identificadas
- 5 campos abiertos de investigación con preguntas formales
- Posicionamiento de IntellOps en el nicho **"Bajo Recurso + Alta AI"**

### 1.5. Catálogo de Venues de Publicación
Documento de **189 líneas** con:
- 50+ conferencias y revistas organizadas por tipo: nacionales/regionales (JAIIO, CACIC, CLEI), internacionales (ICSE, FSE, ISSRE, ASE), revistas con referato (TSE, CSUR, JSS, EMSE)
- Estrategia de publicación por tipo de paper
- Matriz de elegibilidad y roadman sugerido

---

## 2. Actividades de Análisis y Diseño de Software

### 2.1. Especificaciones Formales (OpenSpec)
Creación de **12 specs formales** que constituyen la fuente de verdad del proyecto:

**Investigación (6):**
- `openspec/specs/research/spec.md` — Spec principal de investigación
- `openspec/specs/research/hypotheses.md` — Hipótesis + 12 experimentos
- `openspec/specs/research/experiments.md` — Diseño experimental detallado
- `openspec/specs/research/state-of-the-art.md` — Estado del arte
- `openspec/specs/research/benchmarking.md` — Benchmarks y métricas de evaluación
- `openspec/specs/research/market-analysis.md` — Análisis de mercado

**Arquitectura (6):**
- `openspec/specs/architecture/spec.md` — Spec principal de arquitectura
- `openspec/specs/architecture/components.md` — Componentes del sistema
- `openspec/specs/architecture/containers.md` — Contenedores y despliegue
- `openspec/specs/architecture/interfaces.md` — Interfaces y contratos
- `openspec/specs/architecture/constraints.md` — Restricciones técnicas
- `openspec/specs/architecture/quality-attributes.md` — Atributos de calidad

### 2.2. Decisión Arquitectónica: Reemplazo de ELK Stack
Documentó y ejecutó el ADR `0001-reemplazo-elk-por-grafana-loki-prometheus`:
- **Problema**: Elasticsearch >7.10 usa licencia SSPL incompatible con Apache-2.0 del proyecto; además requiere >4GB RAM, violando la restricción de <2GB
- **Solución**: Migración a Grafana + Loki + Prometheus + Tempo + Alertmanager
- **Impacto**: Stack unificado, menor consumo de recursos, licencias 100% compatibles

### 2.3. Brief y Plan de Trabajo
- Actualización de `docs/brief-v2.md` con el nuevo enfoque UX-céntrico
- Creación de `governance/plan-trabajo.md` (392 líneas) con tareas medibles por contributor
- Actualización de `TEAM_CHARTER.md` con roles y responsabilidades

---

## 3. Contribuciones a la Ingeniería de Software

### 3.1. Gestión de Versiones (SCM)
- **Inicialización del repositorio**: estructura completa con `.gitignore`, templates de issues (bug-report, change-proposal, ml-experiment), PR template, `CHANGELOG.md`
- **Estructura de branching**: estableció convención main/develop con ramas por feature
- **Conventional Commits**: definió e implementó el estándar de mensajes de commit
- **CODE_OF_CONDUCT.md**: documento de convivencia para el equipo

### 3.2. Gestión de Configuración y CI/CD
- **Pipeline CI**: archivo `.github/workflows/ci.yml` base con tests y linting
- **Configuración del proyecto**: `pyproject.toml` con dependencias, `Makefile` con comandos estandarizados
- **Docker Compose**: definición de servicios para desarrollo local

### 3.3. Gestión de Conocimiento
- **Onboarding individual**: 3 documentos personalizados (`onboarding/cavallero.md`, `monfroglio.md`, `montanari.md`) con guía de setup específica para cada rol
- **Research INDEX.md**: mapa completo de los 22 documentos de investigación con matriz contributor-documentos
- **COMO-SEGUIMOS.md**: guía de continuidad para que cualquier contributor retome el proyecto
- **SESION-2026-06-11.md**: registro y conclusiones de la sesión de investigación que reorientó el proyecto

### 3.4. Esqueleto del Proyecto
- **FastAPI**: aplicación base en `src/api/main.py` con endpoint de health check
- **Tests**: test unitario base en `tests/test_health.py`
- **Estructura de directorios**: `src/`, `tests/`, `ml/`, `scripts/` con `.gitkeep`

---

## 4. Entregables

| # | Entregable | Tipo | Líneas |
|---|-----------|------|--------|
| 1 | `docs/research/frontend-observability.md` | Documento de investigación | 929 |
| 2 | `docs/research/rum-agent-deep-dive.md` | Documento de investigación | 1.207 |
| 3 | `docs/research/observability-tools-analysis.md` | Documento de investigación | 845 |
| 4 | `docs/research/INDEX.md` | Índice de investigación | 296 |
| 5 | `docs/research/RESEARCH.md` | Documento base de investigación | 25 (+5) |
| 6 | `docs/research/publication-venues.md` | Catálogo de venues | 189 |
| 7 | `docs/research/SESION-2026-06-11.md` | Minuta de investigación | 180 |
| 8 | `docs/research/COMO-SEGUIMOS.md` | Guía de continuidad | 227 |
| 9 | `README.md` | README del proyecto | 362 |
| 10 | `governance/plan-trabajo.md` | Plan de trabajo | 392 |
| 11 | `TEAM_CHARTER.md` | Carta del equipo | (+13/-4) |
| 12 | `docs/brief-v2.md` | Brief del proyecto | (+21/-9) |
| 13 | `onboarding/cavallero.md` | Onboarding individual | (+91/-50) |
| 14 | `onboarding/monfroglio.md` | Onboarding individual | (+88/-52) |
| 15 | `onboarding/montanari.md` | Onboarding individual | (+90/-50) |
| 16 | `onboarding/README.md` | Onboarding general | (+31/-6) |
| 17 | `openspec/specs/research/experiments.md` | Spec: experimentos | (+27) |
| 18 | `openspec/specs/research/hypotheses.md` | Spec: hipótesis | (+146) |
| 19 | `openspec/specs/architecture/containers.md` | Spec: contenedores | (+54/-7) |
| 20 | `openspec/specs/research/market-analysis.md` | Spec: mercado | (+1/-1) |
| 21 | `docs/adr/0001-reemplazo-elk-por-grafana-loki-prometheus.md` | ADR | — |
| 22 | `src/api/main.py` + `tests/test_health.py` | Código base | Esqueleto FastAPI |
| 23 | `docker-compose.yml` + `Dockerfile` + `Makefile` | Infraestructura | Setup local |
| 24 | `.github/workflows/ci.yml` | Pipeline CI | Base |
| 25 | `CONTRIBUTING.md` | Guía de contribución | Inicial |
| 26 | `.github/PULL_REQUEST_TEMPLATE.md` + templates de issues | Gestión de cambios | Templates SDD |

---

## 5. Tiempo de Dedicación Estimado

| Actividad | Horas estimadas |
|-----------|----------------|
| Inicialización del proyecto (estructura, CI, templates, governance) | 10 |
| Reemplazo ELK → Grafana/Loki/Prometheus (investigación + ADR + actualización docs) | 6 |
| Esqueleto del proyecto (FastAPI, Docker, onboarding) | 12 |
| Creación de 12 specs OpenSpec (investigación + arquitectura) | 14 |
| Investigación: Frontend Observability State of the Art | 20 |
| Investigación: RUM Agent Deep Research & Architecture | 25 |
| Investigación: Observability Tools Industry Analysis | 15 |
| Investigación: Publication Venues Catalog | 6 |
| Documentos de consolidación (INDEX, README, COMO-SEGUIMOS, SESION) | 10 |
| Reorientación I+D+i (brief, plan-trabajo, hypotheses, TEAM_CHARTER) | 8 |
| **Total estimado** | **~126 horas** |

> **Nota**: Este tiempo incluye investigación, lectura de documentación técnica, redacción, revisión y ajustes. No incluye reuniones de equipo ni comunicación asíncrona.

---

*IntellOps — Informe de Avance 1 · 2026-07-30*
