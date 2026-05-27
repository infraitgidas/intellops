# 📘 BRIEF TÉCNICO-CIENTÍFICO: IntellOps v2.0
**Observabilidad Predictiva UX-Centrica + AI/LLM Open-Source**  
*Sub-proyecto PI+D+i | Equipo InfraIT – Grupo GIDAS | UTN FrLP*  
**Marco Metodológico:** OpenSpect (Spec-Driven Development) + Dual-Track Agile + GitOps/DevOps  
**Control de Versionado:** GitHub (Branching protegido, CI/CD con validación de contratos, SBOM automatizado)  
**Enfoque:** Continuidad Científica, Reproducibilidad Académica y Viabilidad Comercial

---

## 🔍 1. EXPLORACIÓN EXHAUSTIVA DEL CASO DE NEGOCIO & ESTADO DEL ARTE

### 1.1. Perspectiva de Negocio: Observabilidad centrada en la UX del Usuario Final
| Dimensión | Descripción | Impacto en Negocio/Academia |
|-----------|-------------|-----------------------------|
| **Cambio de Paradigma** | De monitoreo reactivo (CPU/RAM/Errores) a observabilidad proactiva basada en experiencia real (RUM, Core Web Vitals, flujos de usuario, tiempos de carga percibidos) | Reduce churn, mejora SLA/SLO reales, alinea métricas técnicas con KPIs de producto |
| **Métricas UX Críticas** | LCP, INP, CLS, TTFB, Error Rate por journey, Session Replay, Synthetic vs Real User Monitoring | Permite correlacionar degradación técnica con impacto en retención/conversión |
| **Brecha Actual** | Herramientas existentes fragmentan infra, logs y UX; la IA está acoplada a ecosistemas propietarios; alto costo de almacenamiento y cómputo | Oportunidad para stack open-source, ligero, predictivo y comercialmente viable |
| **Valor PI+D+i** | Generar conocimiento transferible, datasets reproducibles, metodologías validadas y software extensible para academia, PYMEs y administración pública | Publicación científica, extensión universitaria, spin-off o modelo SaaS ligero |

### 1.2. Estado del Arte en Observabilidad + AI/ML/GenIA
| Etapa | Enfoque | Limitaciones | Tendencia Actual |
|-------|---------|--------------|------------------|
| **Monitoring** | Thresholds, dashboards estáticos | Reactivo, alto ruido, sin contexto de negocio | ✅ Superado |
| **Observabilidad (Logs/Metrics/Traces)** | OTel, Prometheus, Grafana, ELK | Correlación manual, análisis post-incidente | ✅ Estándar base |
| **AIOps** | Detección de anomalías (Isolation Forest, Prophet, Autoencoders), clustering de logs | Falsos positivos, falta de explicabilidad, alto costo de entrenamiento | 🔄 En madurez |
| **AI-Augmented / GenIA** | LLMs para RCA semántica, query en lenguaje natural, generación de runbooks, resúmenes de incidentes | Licencias restrictivas, latencia, alucinaciones, dependencia de vendor | 🚀 En adopción temprana |
| **Predictive & Prescriptive** | Forecasting de SLO, auto-scaling, remediation guiada por políticas + LLM | Complejidad de integración, gobernanza de datos, drift de modelos | 🔬 Investigación activa |

### 1.3. Marcos, Estándares y Frameworks de la Industria IT
| Estándar/Framework | Aplicación en IntellOps |
|--------------------|-------------------------|
| **OpenTelemetry (CNCF)** | Ingesta vendor-neutral de métricas, logs, traces. Exportadores nativos a Timescale/ML pipeline |
| **SRE / Google** | SLI/SLO definidos por métricas UX. Error budgets para priorizar incidentes predictivos |
| **DORA / DevOps** | MTTR, Lead Time, Deployment Frequency, Change Failure Rate como KPIs del proceso I+D+i |
| **OpenMetrics / Prometheus** | Formato de exportación, scraping ligero, compatibilidad con dashboards existentes |
| **FAIR / CARE Principles** | Datasets académicos: Findable, Accessible, Interoperable, Reusable; respeto a privacidad de UX |
| **MLOps (MLflow + DVC + Evidently)** | Versionado de experimentos, reproducibilidad, detección de drift, CI de modelos |

### 1.4. Análisis Comparativo: Mercado, Investigación y Open-Source
| Producto/Proyecto | Enfoque | Fortalezas | Debilidades | Brecha que IntellOps cubre |
|-------------------|---------|------------|-------------|----------------------------|
| **Datadog / New Relic / Dynatrace** | Full-stack + AIOps propietario | UX + Infra + AI integrado, RCA automática | Costo elevado, vendor lock-in, licencias cerradas | Open-source, comercializable, sin lock-in |
| **Grafana + Prometheus + Loki** | Ecosistema CNCF estándar | Madurez, comunidad, extensibilidad | AI predictiva nativa limitada, correlación UX/manual | Pipeline ML/LLM integrado, contrato-first |
| **SigNoz / OpenObserve** | Alternativas open-source a Datadog | Ligeros, OTel-native | Features AI en roadmap, madurez UX analytics | Predictivo desde v1, enfoque UX-first, academic-ready |
| **Elastic Stack** | Búsqueda + logs + métricas | Poder de análisis textual, alertas | Consumo alto, licencia SSPL restrictiva para comercial | Apache-2.0/MIT, footprint ≤8GB, cuantización LLM |
| **Investigación Activa (IEEE/ACM)** | LLM para RCA, detección ligera en edge, auto-remediation | Avances en semántica de logs, forecasting multivariado | Poca transferencia a stack productivo, sin documentación comercial | IntellOps puentea investigación ↔ producto con SDD + OpenSpect |

---

## 🎯 2. REDEFINICIÓN DEL PI+D+i

### 2.1. Objetivo General Redefinido
> Desarrollar una plataforma de observabilidad open-source, centrada en la experiencia del usuario final, que integre ingesta de telemetría RUM/infraestructura vía OpenTelemetry, análisis predictivo de anomalías mediante modelos ML ligeros, y un asistente de investigación de incidencias basado en LLM open-source con licencia comercialmente viable. El sistema debe garantizar trazabilidad científica, reproducibilidad académica, portabilidad en entornos de recursos limitados y viabilidad de extensión universitaria o modelo SaaS.

### 2.2. Scope del Producto Final
| Capa | Componentes | Límites |
|------|-------------|---------|
| **Captura** | Agente RUM (TS/JS), OTel Collector, Synthetic probes | Solo métricas UX, traces, logs estructurados. Sin PII sin anonimización |
| **Ingesta & Almacenamiento** | FastAPI Gateway, NATS/RabbitMQ, TimescaleDB (hypertables, compresión) | Retención configurable, políticas de drop/compress automáticas |
| **Analítica Predictiva** | Pipeline ML (Isolation Forest, Prophet, LSTM), Evidently AI, DVC+MLflow | Modelos ligeros, inferencia <500ms, fallback estadístico |
| **GenIA & UX Analytics** | LLM Gateway (Ollama/vLLM, GGUF 4-bit), RAG sobre logs/métricas, NL query engine | Prompt caching, límites de contexto, validación de hallucination |
| **Visualización & Control** | React Dashboard (3 vistas UX: latencias, heatmap de journeys, predicciones), RBAC, export PDF/CSV | API-first, contrato versionado, sin vendor lock-in UI |

### 2.3. Características del Producto
- ✅ **API-First & Contract-Driven:** OpenAPI 3.1, JSON Schema, firmas ML versionadas
- ✅ **UX-Centric SLI/SLO:** Métricas Core Web Vitals + error budgets por journey
- ✅ **Predictivo + Explicable:** Modelos con umbrales de confianza, salidas traducibles a runbooks
- ✅ **Ligero & Portable:** ≤8GB RAM en dev, Docker Compose, compatible K8s/Helm
- ✅ **Comercialmente Viable:** Licencia Apache-2.0/MIT, SBOM automatizado, sin dependencia de SaaS propietario
- ✅ **Academic-Ready:** Datasets sintéticos, experimentos reproducibles, `CITATION.cff`, plantilla LaTeX

### 2.4. Atributos de Calidad del Software (ISO/IEC 25010)
| Atributo | Especificación |
|----------|----------------|
| **Usabilidad** | Dashboards intuitivos, onboarding <30 min, tooltips contextuales, accesibilidad WCAG 2.1 AA |
| **Confiabilidad** | SLO 99.5%, fallback a modelo estadístico, circuit breakers en ingesta |
| **Eficiencia** | Compresión Timescale, batching en ingesta, inferencia ML <500ms en CPU |
| **Mantenibilidad** | SDD/ADRs, contratos versionados, coverage >85%, Makefile idempotente |
| **Portabilidad** | Docker/K8s, multi-arch (amd64/arm64), sin dependencias OS-specific |
| **Seguridad** | Anonimización UX, RBAC, secretos en Vault/Env, escaneo SAST/DAST |
| **Compatibilidad** | OTel, OpenMetrics, Grafana export, webhook/alertmanager |

### 2.5. Atributos de Calidad del Proceso I+D+i
| Atributo | Implementación |
|----------|----------------|
| **Reproducibilidad** | DVC + MLflow, seeds fijos, `make reproduce`, datasets versionados con DOI |
| **Trazabilidad** | Spec → Código → Experimento → Paper. Cada PR vincula ADR, contrato, métrica |
| **Agilidad** | Dual-Track Agile (Discovery + Delivery), sprints 2 sem, backlog priorizado por SLO/UX |
| **DevOps/GitOps** | CI/CD con gates de spec, IaC (Terraform/Compose), despliegue canary, rollback automático |
| **Gobernanza** | SBOM (Syft/ORT), escaneo de licencias, política Apache-2.0/MIT, auditoría trimestral |
| **Resiliencia Académica** | Onboarding <2d, `knowledge-graph.md`, feature flags, handover obligatorio |

---

## 📐 3. NUEVO BRIEF DEL PROYECTO (Agile + DevOps + SDD/OpenSpect)

### 3.1. Marco Operativo: OpenSpect + Dual-Track Agile + GitOps
| Pilar | Práctica Concreta | Herramienta |
|-------|-------------------|-------------|
| **Spec-First** | Requisitos, arquitectura, contratos API/DB/ML se versionan antes de código | `specs/`, `contracts/`, OpenAPI, Mermaid C4 |
| **Living Contracts** | Validación automática en CI. Merge bloqueado si rompe contrato | `openapi-validator`, `pytest-contract`, `pact` |
| **Dual-Track Agile** | Discovery (UX research, experimentos ML) + Delivery (implementación, deploy) | Jira/GitHub Projects, roadmap 2 sem, backlog refinado |
| **DevOps/GitOps** | CI/CD pipeline con gates, IaC, observabilidad del propio sistema | GitHub Actions, Docker, Compose/K8s, OTel self-monitor |
| **Git Strategy** | `main` (release), `develop` (integración), `spec/`, `feat/`, `exp/` (ML) | Protected branches, required reviews, PR templates |

### 3.2. Flujo de Trabajo en GitHub (Multidisciplinario & Rotativo)
```
issue/scope-change → spec/update.md → CI validates contracts → PR → 2 reviews → merge to develop → deploy staging → acceptance → main
```
- **PR Template:** Exige `spec-link`, `adr-ref`, `contract-checklist`, `ml-metrics`, `license-scan`
- **Labels:** `ux-impact`, `ml-experiment`, `contract-break`, `doc-scientific`, `onboarding-ready`
- **CI Gates:** 
  - `spec-validation.yml` (OpenAPI, DB schema, ML signature)
  - `contract-tests.yml` (payloads, edge cases, latency SLO)
  - `license-scan.yml` (SBOM, alerta SSPL/AGPL)
  - `ml-reproducibility.yml` (re-run con seed, compara baseline)

### 3.3. Documentación Científica & Continuidad PI+D+i
| Artefacto | Ubicación | Estándar | Propósito |
|-----------|-----------|----------|-----------|
| `RESEARCH.md` | `/docs/research/` | FAIR + CARE | Hipótesis, metodología, ética, limitaciones |
| `EXPERIMENTS/` | `/ml/` | MLflow + DVC | Runs, hiperparámetros, prompts, artefactos |
| `VALIDATION.md` | `/specs/` | ISTQB + OpenSpect | Criterios aceptación, umbrales ML, tests regresión |
| `ADR/` | `/docs/adr/` | Nygard Format | Decisiones técnicas, trade-offs, contexto |
| `SBOM.md` | `/compliance/` | SPDX/CycloneDX | Licencias, dependencias, aptitud comercial |
| `CONTINUITY.md` | `/governance/` | OpenSpect Handover | Snapshot de specs, contratos, modelos, responsables |

**Publicación Open Science:** Cada release mayor genera `CITATION.cff`, dataset en Zenodo/OSF con DOI, y plantilla LaTeX para paper técnico. Resultados ML incluyen `report/` con drift analysis, confusion matrix, explicabilidad SHAP/LIME.

### 3.4. Gestión de Cambios & Resiliencia Académica
- **Caso de Negocio Cambia:** Issue `scope-change` → actualiza `REQUIREMENTS.md` → CI ejecuta `spec-diff` → ADR registra decisión → versionado API (`/v1/`, `/v2/`) → código adapta sin romper contratos.
- **Rotación de Equipo:** Contrato > Código. `make setup` levanta entorno en ≤15 min. `knowledge-graph.md` mapea specs → código → experimentos. Handover obligatorio vía `docs/handover/<user>.md`.
- **Fallback & Estabilidad:** Feature flags (`Unleash`), modelos `stable` vs `experimental`, alertas automáticas si F1 < umbral o latencia > SLO.

### 3.5. Roadmap Incremental (5 Fases Validadas por OpenSpect)
| Hito | Duración | Entregable SDD | Criterio de Éxito |
|------|----------|----------------|-------------------|
| **H1: Cimentación & Specs** | 3 sem | `REQUIREMENTS.md`, `ARCHITECTURE.md`, CI/CD, `docker-compose`, OTel baseline | CI verde, 2 reviews, spec index completo, onboarding <2d |
| **H2: Ingesta & Storage** | 4 sem | Agente RUM, FastAPI gateway, Timescale schema, OpenAPI contract | Contract tests >95%, query <1s en 10k rows, compresión activa |
| **H3: Pipeline ML Predictivo** | 5 sem | DVC+MLflow, Isolation Forest + Prophet, serving API, Evidently drift monitor | F1 >0.85, MAPE <15%, reproducibilidad verificada, report generado |
| **H4: GenIA & UX Analytics** | 4 sem | LLM gateway (Ollama/vLLM GGUF 4-bit), 3 vistas dashboard, NL query engine | Respuestas <3s, precisión >80%, SBOM validado, prompt cache activo |
| **H5: Validación & Extensión** | 3 sem | Deploy GIDAS, stress test, paper técnico, manual comercial, `v1.0` | Aceptación PO, 2+ equipos internos usando, licencia Apache-2.0/MIT confirmada |

### 3.6. Aprobación & Firma
Este brief establece el contrato operativo, científico y técnico del sub-proyecto **IntellOps v2.0**. Toda iteración, cambio de alcance o rotación de equipo se gestionará bajo los principios OpenSpect, garantizando trazabilidad, reproducibilidad y continuidad PI+D+i.

| Rol | Nombre | Fecha | Firma |
|-----|--------|-------|-------|
| PO / Investigador Lead |  |  |  |
| Tech Lead / Arquitecto |  |  |  |
| ML/Data Engineer |  |  |  |
| Responsable Documentación Científica |  |  |  |

---
📎 **Anexos Inmediatos Disponibles (bajo solicitud):**
1. `specs/REQUIREMENTS.md` + `contracts/openapi.yaml` (OpenAPI 3.1, validación CI lista)
2. `docker-compose.yml` optimizado ≤8GB RAM + `Makefile` de onboarding & continuidad
3. Plantilla GitHub PR/Issue con validación SDD + escaneo de licencias automatizado
4. Estructura `ml/` con DVC+MLflow + Evidently + reportes científicos automáticos
5. Matriz de licencias compatibles con comercialización (LLM, DB, UI, ML, Agentes)
