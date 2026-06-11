# Plan de Trabajo — Tareas Concretas por Contributor

## Cómo Trabajar con Este Repositorio

Todo cambio en IntellOps sigue el flujo **SDD (Spec-Driven Development)**. No se escribe código sin una spec aprobada primero.

### Flujo SDD en 8 Pasos

```
PASO 1 — IDEA
│  Abrí un Issue con el template "Change Proposal"
│  Título: "[change] nombre-corto-descriptivo"
│  Enlace: https://github.com/infraitgidas/intellops/issues/new?template=02-change-proposal.md
│
PASO 2 — REVIEW DEL COORDINADOR
│  Esperá que el coordinador revise y apruebe la propuesta
│
PASO 3 — RAMA
│  git checkout develop
│  git pull origin develop
│  git checkout -b feat/nombre-cambio develop
│
PASO 4 — SPEC + DESIGN
│  Escribí la spec en openspec/changes/<change-name>/spec.md
│  Si aplica: ADR en docs/adr/XXX-nombre.md
│  git add -A && git commit -m "spec: <descripción>"
│
PASO 5 — IMPLEMENTACIÓN
│  Código + tests (TDD: test rojo → test verde → refactor)
│  git add -A && git commit -m "feat: <descripción>"
│
PASO 6 — VERIFICACIÓN
│  make test          # Tests unitarios
│  make test-cov      # Cobertura (mínimo 70%)
│  make lint          # Linter
│  make up && make test  # Opcional: integración
│
PASO 7 — PULL REQUEST
│  git push origin feat/nombre-cambio
│  Abrí PR en GitHub con el template
│  Asigná al coordinador como reviewer
│
PASO 8 — ARCHIVE (post-merge)
│  Mové la spec a openspec/changes/archive/
│  Actualizá CHANGELOG.md
```

### Reglas de Oro

| Regla | Explicación |
|-------|-------------|
| **Una rama por cambio** | Nunca mezcles cambios distintos en la misma rama |
| **Commits atómicos** | Cada commit hace una sola cosa (spec, feat, test, docs) |
| **Tests antes del código** | Escribí el test que falla, después el código que lo pasa |
| **PR a develop siempre** | `main` solo recibe merges desde `develop` en releases |
| **Sin merge propio** | Siempre necesitás al menos 1 approval |

---

## Contributor 1: Federico Cavallero — User Telemetry & Tracing

### Fase 1: Fundamentos de Infra

#### T1.1 — Auditoría de Seguridad Baseline

| Campo | Detalle |
|-------|---------|
| **Descripción** | Ejecutar Lynis sobre el laboratorio GIDAS, documentar el estado actual de seguridad y generar un informe de baseline |
| **Entregable medible** | `docs/research/exp-201-baseline.md` con: Lynis score inicial, lista de controles CIS aplicables, vulnerabilidades encontradas |
| **Criterio de aceptación** | Documento revisado por el coordinador con ≥ 1 ADR si aplica |
| **Dependencias** | Acceso al laboratorio GIDAS, Lynis instalado |
| **Esfuerzo** | 1 sprint |
| **Rama ejemplo** | `feat/baseline-seguridad-gidas` |

#### T1.2 — Hardening CIS con Ansible

| Campo | Detalle |
|-------|---------|
| **Descripción** | Implementar playbooks de Ansible que automaticen los controles CIS Benchmark Level 1 sobre los servidores del laboratorio |
| **Entregable medible** | `scripts/ansible/hardening-cis.yml` — playbook aplicable. Post-hardening Lynis score ≥ 70% |
| **Criterio de aceptación** | `make hardening` ejecuta el playbook. Lynis score post-ejecución documentado en el PR |
| **Dependencias** | T1.1 completado |
| **Esfuerzo** | 2 sprints |
| **Rama ejemplo** | `feat/hardening-cis-ansible` |

#### T1.3 — Pipeline GLP (Grafana + Loki + Prometheus)

| Campo | Detalle |
|-------|---------|
| **Descripción** | Configurar Promtail + Loki + Grafana como pipeline de logs de seguridad. Crear 4 dashboards de seguridad en Grafana |
| **Entregable medible** | Servicios funcionando en docker-compose. 4 dashboards exportados como JSON en `docs/dashboards/seguridad/` |
| **Criterio de aceptación** | `make up` levanta el stack completo. Los dashboards son importables desde la UI de Grafana. Tiempo de detección de evento simulado < 60s |
| **Dependencias** | T1.2 completado |
| **Esfuerzo** | 2 sprints |
| **Rama ejemplo** | `feat/pipeline-glp-seguridad` |

---

### Fase 2: User Telemetry & Tracing

#### T2.1 — Agente RUM con OpenTelemetry

| Campo | Detalle |
|-------|---------|
| **Descripción** | Implementar un agente JavaScript usando OpenTelemetry JS SDK que capture Core Web Vitals (LCP, INP, CLS), trazas de navegación y errores de frontend, y los exporte vía OTLP al Collector |
| **Entregable medible** | `src/agent/rum.js` — bundle comprimido < 30KB. PoC en página HTML simple que muestre las métricas capturadas |
| **Criterio de aceptación** | Bundle size < 30KB (gzip). LCP, INP, CLS visibles en el Collector. Overhead en Lighthouse < 3% |
| **Dependencias** | OTel Collector configurado (T2.2) |
| **Esfuerzo** | 2 sprints |
| **Hipótesis asociada** | H5 |
| **Rama ejemplo** | `feat/agente-rum-otel` |

#### T2.2 — Pipeline Tempo + OTel Collector

| Campo | Detalle |
|-------|---------|
| **Descripción** | Configurar OpenTelemetry Collector para recibir señales OTLP desde el agente RUM y desde la API FastAPI (instrumentada). Exportar trazas a Tempo y logs a Loki |
| **Entregable medible** | `docker-compose.yml` actualizado con OTel Collector + Tempo. Dashboards en Grafana mostrando trazas correlacionadas con logs |
| **Criterio de aceptación** | `docker compose up` levanta Collector + Tempo. Una traza de request completa (frontend → backend) visible en Grafana Explore. Correlación trace → log funcionando |
| **Dependencias** | T2.1 completado |
| **Esfuerzo** | 2 sprints |
| **Hipótesis asociada** | H5 (EXP-OTel-02) |
| **Rama ejemplo** | `feat/pipeline-tempo-otel` |

#### T2.3 — Sistema de Alertas Multicanal

| Campo | Detalle |
|-------|---------|
| **Descripción** | Implementar Grafana Alertmanager con routing inteligente: alertas de criticidad alta → WhatsApp, media → Telegram, baja → Mail. Incluir templates de mensaje para cada canal |
| **Entregable medible** | Alertmanager configurado en docker-compose. Templates de notificación en `src/alertmanager/templates/`. Demo: alerta de prueba enviada a los 3 canales |
| **Criterio de aceptación** | Alerta de criticidad alta llega a WhatsApp en < 30s. Alerta media a Telegram. Alerta baja a Mail. Routing funciona por severidad y horario |
| **Dependencias** | T2.2 completado |
| **Esfuerzo** | 1 sprint |
| **Hipótesis asociada** | H5 (EXP-OTel-03) |
| **Rama ejemplo** | `feat/alertas-multicanal` |

#### T2.4 — Benchmark de Overhead OTel

| Campo | Detalle |
|-------|---------|
| **Descripción** | Medir el overhead de la instrumentación OpenTelemetry sobre FastAPI: latencia, throughput, consumo de RAM con y sin OTel. Documentar resultados |
| **Entregable medible** | `docs/research/exp-otel-04-benchmark.md` con tabla comparativa: latencia p50/p95/p99, requests/segundo, RAM con/sin OTel |
| **Criterio de aceptación** | Overhead de latencia < 5ms p99. Overhead de RAM < 30MB. Throughput degradación < 10% |
| **Dependencias** | T2.2 completado |
| **Esfuerzo** | 1 sprint |
| **Hipótesis asociada** | H5 (EXP-OTel-04) |
| **Rama ejemplo** | `feat/benchmark-otel-overhead` |

---

## Contributor 2: Romeo Monfroglio — ML / AI Agents

### Fase 1: Fundamentos de Infra

#### T1.1 — Esqueleto del ML Engine

| Campo | Detalle |
|-------|---------|
| **Descripción** | Crear la estructura de `src/ml/` con detector base abstracto, pipeline de entrenamiento/inferencia, y un detector de ejemplo con Isolation Forest |
| **Entregable medible** | `src/ml/` con: `base.py` (clase abstracta Detector), `detectors/isolation_forest.py`, `pipeline.py`, `tests/ml/test_detectors.py`. Endpoint `POST /ml/detect` en FastAPI |
| **Criterio de aceptación** | `make test` pasa. Endpoint `/ml/detect` responde con predicción. Cobertura > 70% en `src/ml/` |
| **Dependencias** | Ninguna |
| **Esfuerzo** | 1 sprint |
| **Rama ejemplo** | `feat/esqueleto-ml-engine` |

#### T1.2 — Isolation Forest Baseline (EXP-001)

| Campo | Detalle |
|-------|---------|
| **Descripción** | Entrenar y evaluar Isolation Forest sobre dataset SWaT o Yahoo S5. Documentar métricas (F1, precisión, recall, latencia) |
| **Entregable medible** | `ml/experiments/EXP-001/` con: `README.md`, `config.yaml`, `run.py`, `results/metrics.json`, `results/plots/`. F1 ≥ 0.70 |
| **Criterio de aceptación** | `make reproduce EXP-001` ejecuta el experimento y reproduce resultados. Seed fijo documentado. MLflow run registrada |
| **Dependencias** | T1.1 completado |
| **Esfuerzo** | 2 sprints |
| **Hipótesis asociada** | H1 (EXP-001) |
| **Rama ejemplo** | `feat/exp-001-if-baseline` |

#### T1.3 — Dashboard 3 Vistas (Latencias + Heatmap + Predicciones)

| Campo | Detalle |
|-------|---------|
| **Descripción** | Implementar dashboard React con D3.js: vista de latencias en tiempo real, heatmap de infraestructura, vista de predicciones con forecasting |
| **Entregable medible** | `src/dashboard/` con componentes React + D3.js. 3 vistas funcionales. Bundle < 1MB |
| **Criterio de aceptación** | `make up` sirve el dashboard. Las 3 vistas cargan datos mock. Bundle size < 1MB. Lighthouse performance > 80 |
| **Dependencias** | T1.2 completado |
| **Esfuerzo** | 3 sprints |
| **Rama ejemplo** | `feat/dashboard-3-vistas` |

---

### Fase 2: Agentes IA para UX Predictiva

#### T2.1 — Clasificador de Reclamos (EXP-AI-01)

| Campo | Detalle |
|-------|---------|
| **Descripción** | Entrenar un clasificador (Random Forest) que prediga si un usuario va a tener un problema basándose en features de OpenTelemetry (latencia p99, error rate, throughput, Core Web Vitals). Usar dataset sintético generado a partir de trazas |
| **Entregable medible** | `src/ml/predictors/complaint_classifier.py` — modelo entrenado. `ml/experiments/EXP-AI-01/` con experimento completo. F1 ≥ 0.75 |
| **Criterio de aceptación** | `make reproduce EXP-AI-01` reproduce resultados. El clasificador expone API `POST /ml/predict/complaint`. F1 documentado |
| **Dependencias** | T1.2 completado, T2.1 de Federico (trazas OTel disponibles) |
| **Esfuerzo** | 2 sprints |
| **Hipótesis asociada** | H6 (EXP-AI-01) |
| **Rama ejemplo** | `feat/clasificador-reclamos` |

#### T2.2 — User Health Score

| Campo | Detalle |
|-------|---------|
| **Descripción** | Diseñar e implementar un algoritmo de User Health Score que combine múltiples señales OTel en un score 0-100. Incluir pesos configurables, thresholds y API REST |
| **Entregable medible** | `src/ml/core/user_health_score.py` — algoritmo. Endpoint `GET /ml/health-score/:userId`. Documentación del diseño en `docs/research/user-health-score.md` |
| **Criterio de aceptación** | Score entre 0 y 100. Correlación con reclamos reales r > 0.75 (demo con datos sintéticos). Pesos configurables vía API |
| **Dependencias** | T2.1 completado |
| **Esfuerzo** | 2 sprints |
| **Hipótesis asociada** | H6 (EXP-AI-03) |
| **Rama ejemplo** | `feat/user-health-score` |

#### T2.3 — Agente RCA con LLM Local (EXP-AI-02)

| Campo | Detalle |
|-------|---------|
| **Descripción** | Implementar un agente de IA que consuma trazas de Tempo + logs de Loki, las procese con un LLM local (Llama 3.2 1B) + RAG sobre runbooks, y genere análisis de causa raíz en lenguaje natural |
| **Entregable medible** | `src/ml/agents/rca_agent.py` — agente funcional. Endpoint `POST /ml/rca` que acepta un incidente ID y devuelve RCA. `ml/experiments/EXP-AI-02/` con experimento |
| **Criterio de aceptación** | RCA generado para 3 incidentes de prueba. Precisión factual ≥ 80% medida por revisión del coordinador. Latencia < 30s por consulta |
| **Dependencias** | T2.2 completado, pipeline OTel funcionando (Federico T2.2) |
| **Esfuerzo** | 3 sprints |
| **Hipótesis asociada** | H6 (EXP-AI-02) |
| **Rama ejemplo** | `feat/agente-rca-llm` |

#### T2.4 — Detección de Anomalías en Trazas (EXP-AI-04)

| Campo | Detalle |
|-------|---------|
| **Descripción** | Implementar detección de anomalías sobre trazas OTel: latencia outlier, error burst, degradación de throughput. Integrar con el pipeline de alertas |
| **Entregable medible** | `src/ml/detectors/trace_anomaly_detector.py`. Endpoint `POST /ml/detect/traces`. Alertas generadas ante anomalías detectadas |
| **Criterio de aceptación** | Detecta latencias outlier (p99 > 3 desvíos). Detecta error burst (> 5% en ventana 5min). Falso positivos < 15% |
| **Dependencias** | T2.3 completado, pipeline Tempo funcionando |
| **Esfuerzo** | 2 sprints |
| **Hipótesis asociada** | H6 (EXP-AI-04) |
| **Rama ejemplo** | `feat/anomalias-trazas` |

---

## Contributor 3: Santiago Montanari — QA / Observability-Driven QA

### Fase 1: Fundamentos de Infra

#### T1.1 — Pipeline CI/CD Real

| Campo | Detalle |
|-------|---------|
| **Descripción** | Hacer que el CI workflow de `.github/workflows/ci.yml` funcione de verdad. Descomentar y corregir los jobs de contract testing y license-scan. Agregar quality gates |
| **Entregable medible** | CI pipeline verde en GitHub Actions. Jobs: lint → test → test-cov → contract → license-scan. Coverage report como artefacto |
| **Criterio de aceptación** | Push a cualquier rama dispara el CI completo. Coverage report publicado. Lint warnings = 0. Pipeline time < 10 min |
| **Dependencias** | Ninguna |
| **Esfuerzo** | 1 sprint |
| **Rama ejemplo** | `feat/pipeline-ci-real` |

#### T1.2 — Quality Gates en CI

| Campo | Detalle |
|-------|---------|
| **Descripción** | Implementar quality gates reales: coverage threshold (fail si < 70%), lint score (fail si warnings > 0), validación de OpenAPI contract |
| **Entregable medible** | CI job que falla si coverage < 70%. Badge de coverage en README.md. OpenAPI contract validado en CI |
| **Criterio de aceptación** | PR con coverage < 70% es bloqueado. PR con lint warnings es bloqueado. PR con OpenAPI inválido es bloqueado |
| **Dependencias** | T1.1 completado |
| **Esfuerzo** | 1 sprint |
| **Rama ejemplo** | `feat/quality-gates` |

#### T1.3 — Contract Testing con Schemathesis

| Campo | Detalle |
|-------|---------|
| **Descripción** | Implementar contract testing con schemathesis contra la OpenAPI spec. Validar que la API cumple el contrato en cada PR |
| **Entregable medible** | `tests/contract/test_openapi.py` con schemathesis. Job `test-contract` en CI. Reporte de cobertura de endpoints |
| **Criterio de aceptación** | El job de contract testing cubre ≥ 80% de los endpoints. Falla si hay discrepancias entre spec y código |
| **Dependencias** | T1.1 completado |
| **Esfuerzo** | 1 sprint |
| **Rama ejemplo** | `feat/contract-testing` |

---

### Fase 2: Observability-Driven QA

#### T2.1 — Synthetic User Journeys con OTel (EXP-QA-01)

| Campo | Detalle |
|-------|---------|
| **Descripción** | Implementar scripts de Locust que simulen usuarios reales con instrumentación OpenTelemetry. Cada journey genera una traza completa validable en Tempo |
| **Entregable medible** | `tests/synthetic/journeys/` con 3 journeys: login + consulta, carga de dashboard, reporte de error. Trazas completas visibles en Tempo |
| **Criterio de aceptación** | Cada journey genera una traza completa (frontend → backend → DB). Tempo muestra la traza con todos los spans. Locust reporta métricas de latencia por journey |
| **Dependencias** | Pipeline OTel funcionando (Federico T2.2) |
| **Esfuerzo** | 2 sprints |
| **Hipótesis asociada** | H7 (EXP-QA-01) |
| **Rama ejemplo** | `feat/synthetic-journeys-otel` |

#### T2.2 — Quality Gates OTel en CI/CD (EXP-QA-02)

| Campo | Detalle |
|-------|---------|
| **Descripción** | Extender el CI/CD con quality gates basados en señales OTel: latencia p99 < 200ms, error rate < 0.1%, trazas completas validadas. El pipeline falla si las métricas OTel no cumplen thresholds |
| **Entregable medible** | CI job que corre synthetic journeys + valida métricas OTel. Gate que bloquea si latencia p99 > 200ms o error rate > 0.1% |
| **Criterio de aceptación** | PR con degradación de performance es bloqueado. PR con error rate alto es bloqueado. Overhead del gate < 3 min |
| **Dependencias** | T2.1 completado |
| **Esfuerzo** | 2 sprints |
| **Hipótesis asociada** | H7 (EXP-QA-02) |
| **Rama ejemplo** | `feat/quality-gates-otel` |

#### T2.3 — Chaos Engineering para UX (EXP-QA-03)

| Campo | Detalle |
|-------|---------|
| **Descripción** | Diseñar experimentos de caos controlados: inyectar latencia en la API, simular fallos de DB, medir impacto en User Health Score |
| **Entregable medible** | `tests/chaos/` con experimentos: latencia +50ms, +200ms, +500ms; fallo de DB por 30s. Reporte de impacto en User Health Score |
| **Criterio de aceptación** | Cada experimento tiene setup → ataque → medición → rollback. User Health Score degrada proporcionalmente a la severidad del caos. Reporte publicado |
| **Dependencias** | T2.2 completado, User Health Score funcionando (Romeo T2.2) |
| **Esfuerzo** | 2 sprints |
| **Hipótesis asociada** | H7 (EXP-QA-03) |
| **Rama ejemplo** | `feat/chaos-ux` |

#### T2.4 — CBA de Observabilidad (EXP-QA-04)

| Campo | Detalle |
|-------|---------|
| **Descripción** | Crear un dashboard de Costo-Beneficio de observabilidad: incidentes evitados, MTTR, costo del stack, efectividad de alertas. Métricas de ROI del sistema |
| **Entregable medible** | Dashboard en Grafana con: incidentes detectados vs evitados, MTTR semanal, costo acumulado ($0), alertas por canal, User Health Score promedio |
| **Criterio de aceptación** | Dashboard importable desde JSON. Datos históricos desde el inicio del proyecto. Refresco automático cada 5 min |
| **Dependencias** | T2.2 completado, pipeline de alertas (Federico T2.3) |
| **Esfuerzo** | 1 sprint |
| **Hipótesis asociada** | H7 (EXP-QA-04) |
| **Rama ejemplo** | `feat/cba-observabilidad` |

---

## Timeline Consolidado

```
Sprint 1-2 │ Federico: T1.1 → T1.2
           │ Romeo:    T1.1 → T1.2
           │ Santiago: T1.1 → T1.2
           │
Sprint 3-4 │ Federico: T1.3 → T2.1
           │ Romeo:    T1.3 → T2.1
           │ Santiago: T1.3 → T2.1
           │
Sprint 5-6 │ Federico: T2.2
           │ Romeo:    T2.2
           │ Santiago: T2.2
           │
Sprint 7-8 │ Federico: T2.3
           │ Romeo:    T2.3
           │ Santiago: T2.3
           │
Sprint 9-10│ Federico: T2.4
           │ Romeo:    T2.4
           │ Santiago: T2.4
           │
Sprint 11-20│ Desarrollo continuo, integración, papers
```

---

## Cómo Reportar Avance

Cada contributor reporta su avance **todos los viernes** en un comment del issue de su cambio activo:

```markdown
## Avance Semanal — [Nombre] — Semana [X]

### Tarea activa: [ID de tarea]

### Completado esta semana
- [ ] Checklist item 1
- [ ] Checklist item 2

### Bloqueantes
- [ ] Dependencia X no está lista
- [ ] Problema Y con la herramienta Z

### Métricas de la tarea
- Coverage: XX%
- Pipeline time: XX min
- [Otra métrica relevante]

### Próxima semana
- [ ] Siguiente paso planificado
```

El coordinador revisa los avances y actualiza el tablero de proyecto en GitHub.

---

*Este plan es un documento vivo. Las tareas pueden re-priorizarse según avances y descubrimientos durante la investigación.*
