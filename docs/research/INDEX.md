# Índice de Investigación — IntellOps

- **Versión**: 1.0
- **Fecha**: 2026-06-11
- **Total documentos**: 22 archivos de documentación activa
- **Total líneas**: ~5,338 líneas de documentación técnica y de investigación

---

## Mapa de Documentación

```
docs/research/                          │ openspec/specs/research/
  ├── INDEX.md                          │   ├── spec.md
  ├── RESEARCH.md ← LÍNEA BASE          │   ├── state-of-the-art.md
  ├── frontend-observability.md         │   ├── benchmarking.md
  ├── observability-tools-analysis.md   │   ├── market-analysis.md
  └── rum-agent-deep-dive.md            │   ├── hypotheses.md
                                        │   └── experiments.md
                                        │
openspec/specs/architecture/            │ governance/
  ├── spec.md                           │   ├── plan-trabajo.md
  ├── containers.md                     │   ├── compliance.md
  ├── components.md                     │   └── continuity.md
  ├── interfaces.md                     │
  ├── constraints.md                    │ docs/adr/
  └── quality-attributes.md             │   ├── 0000-template.md
                                        │   └── 0001-reemplazo-elk-grafana.md
```

---

## 1. Documentos de Investigación por Área

### 1.1. Estado del Arte y Mercado

| Documento | Líneas | Propósito | Última actualización |
|-----------|--------|-----------|---------------------|
| **`openspec/specs/research/state-of-the-art.md`** | 153 | SLR de observabilidad: evolución (pre-2018 → 2026), plataformas comerciales vs OSS, estándares, líneas de investigación activas | 2026-05-27 |
| **`openspec/specs/research/market-analysis.md`** | 112 | Análisis de mercado: TAM/SAM/SOM, FODA, mapa de posicionamiento de IntellOps | 2026-05-27 |
| **`openspec/specs/research/benchmarking.md`** | 111 | Benchmarks de plataformas, modelos ML, LLMs, bases de datos y datasets | 2026-05-27 |
| **`docs/research/observability-tools-analysis.md`** | 845 | **NUEVO**. Análisis profundo de 12 plataformas con matrices comparativas, tendencias 2025-2026, 5 campos abiertos de investigación | 2026-06-11 |

#### Hallazgos clave

1. **Grafana LGTM** es el estándar OSS de facto y la base de IntellOps
2. **Ninguna plataforma** cubre el nicho "Bajo Recurso + Alta AI"
3. **Datadog y Dynatrace** lideran en AI/ML pero son prohibitivos para academia
4. **Netdata** es el más eficiente en edge (150MB RAM) pero solo métricas
5. **5 tendencias** de industria: OTel universal, storage unificado, AI obligatorio, RUM integrado, privacidad

---

### 1.2. Observabilidad Frontend y UX

| Documento | Líneas | Propósito | Última actualización |
|-----------|--------|-----------|---------------------|
| **`docs/research/frontend-observability.md`** | 929 | **NUEVO**. Estado del arte de observabilidad UX-céntrica: Core Web Vitals, métricas, RUM vs Synthetic, RED method, OpenTelemetry browser, geolocalización, análisis predictivo | 2026-06-11 |
| **`docs/research/rum-agent-deep-dive.md`** | 1,207 | **NUEVO**. Investigación técnica profunda sobre agentes RUM: APIs del navegador, implementación de métricas, OTel Browser SDK, optimización de bundle, privacidad, arquitectura propuesta para IntellOps | 2026-06-11 |

#### Hallazgos clave

1. **OpenTelemetry Browser es experimental** — el Browser SIG trabaja en estandarización
2. **No existe agente RUM OSS < 30KB** con Core Web Vitals + trazas OTel + errores
3. **INP reemplazó a FID** como Core Web Vital en marzo 2024
4. **CLS requiere lógica de session window** (gap 1s, max 5s) según especificación Google
5. **Grafana Faro** (10KB) es el referente OSS más cercano pero está orientado a Grafana Cloud
6. **Target IntellOps**: agente RUM < 20KB con feature-set completo

---

### 1.3. Hipótesis y Experimentos

| Documento | Líneas | Propósito | Última actualización |
|-----------|--------|-----------|---------------------|
| **`openspec/specs/research/spec.md`** | 64 | Marco de investigación científica: metodología Action Research + DSR, criterios de validación | 2026-05-27 |
| **`openspec/specs/research/hypotheses.md`** | 306 | **ACTUALIZADO**. 7 hipótesis formales (H1-H7) con H₀/H₁, variables, criterios de validación, experimentos asociados y riesgos | 2026-06-11 |
| **`openspec/specs/research/experiments.md`** | 143 | **ACTUALIZADO**. 24 experimentos catalogados (EXP-001 a EXP-QA-04) con IDs, responsables y prioridades | 2026-06-11 |
| **`docs/research/RESEARCH.md`** | 74 | **ACTUALIZADO**. Research log vivo: líneas activas (L1-L5), experimentos, publicaciones planificadas (6 papers), datasets, hipótesis abiertas | 2026-06-11 |

#### Hipótesis Activas

| ID | Línea | Título | Responsable | Fase |
|----|-------|--------|-------------|------|
| H1 | L1 | Detección de Anomalías con ML Liviano | Romeo | Fase 1 |
| H2 | L2 | GenIA Local para RCA | TBD | — |
| H3 | L3 | Seguridad con Recursos Cero | Federico | Fase 1 |
| H4 | L4 | DevOps en PI+D+i | Santiago | Fase 1 |
| **H5** | **L5** | **User Telemetry & Tracing** | **Federico** | **Fase 2** |
| **H6** | **L6** | **Agentes IA para UX Predictiva** | **Romeo** | **Fase 2** |
| **H7** | **L7** | **Observability-Driven QA** | **Santiago** | **Fase 2** |

#### Experimentos por Grupo

| Grupo | Cantidad | Responsable | Fase |
|-------|----------|-------------|------|
| EXP-001 a 004 | 4 | Romeo | Fase 1 |
| EXP-101 a 103 | 3 | TBD | — |
| EXP-201 a 203 | 3 | Federico | Fase 1 |
| EXP-301 a 303 | 3 | Santiago | Fase 1 |
| **EXP-OTel-01 a 04** | **4** | **Federico** | **Fase 2** |
| **EXP-AI-01 a 04** | **4** | **Romeo** | **Fase 2** |
| **EXP-QA-01 a 04** | **4** | **Santiago** | **Fase 2** |

---

### 1.4. Arquitectura

| Documento | Líneas | Propósito | Última actualización |
|-----------|--------|-----------|---------------------|
| **`openspec/specs/architecture/spec.md`** | 83 | Visión arquitectónica: principios, C4 Context, 4 personas, decisiones clave | 2026-05-27 |
| **`openspec/specs/architecture/containers.md`** | 226 | **ACTUALIZADO**. C4 Containers con 13 contenedores: OTel Collector, Tempo, Alertmanager agregados. Footprint total ~2.3GB RAM | 2026-06-11 |
| **`openspec/specs/architecture/components.md`** | 186 | Componentes internos + flujos Mermaid de secuencia | 2026-05-27 |
| **`openspec/specs/architecture/interfaces.md`** | 248 | Interfaces: 20 endpoints REST, schemas, AsyncAPI events, puertos | 2026-05-27 |
| **`openspec/specs/architecture/constraints.md`** | 110 | Restricciones técnicas, de proceso, de negocio, principios de diseño | 2026-05-27 |
| **`openspec/specs/architecture/quality-attributes.md`** | 149 | 13 escenarios QA ISO 25010 con targets | 2026-05-27 |
| **`docs/adr/0001-reemplazo-elk-por-grafana-loki-prometheus.md`** | 104 | ADR-0001: reemplazo de ELK por Grafana + Loki + Prometheus | 2026-05-27 |

#### Stack Tecnológico Definido

```
Frontend RUM
  └── OTel JS SDK + web-vitals → Bundle < 20KB

Backend
  └── FastAPI + Uvicorn → < 100MB RAM

OTel Collector → Recepción unificada OTLP → < 100MB RAM

Almacenamiento
  ├── Tempo → Trazas distribuidas → < 256MB RAM
  ├── Loki → Logs → < 256MB RAM
  └── Prometheus/Mimir → Métricas → < 256MB RAM

Dashboard
  └── Grafana → Visualización + Alertas → < 256MB RAM

Alertas
  └── Grafana Alertmanager → Routing multicanal → < 50MB RAM

ML/AI
  ├── scikit-learn → Anomalías + clasificación → < 50MB RAM
  └── Llama 3.2 1B (llama.cpp) → RCA → ~600MB RAM (bajo demanda)

Self-Monitoring
  └── Netdata → Métricas del sistema → ~150MB RAM

Footprint total: ~2.3GB RAM estable | ~1.5GB modo económico
```

---

### 1.5. Plan de Trabajo

| Documento | Líneas | Propósito | Última actualización |
|-----------|--------|-----------|---------------------|
| **`governance/plan-trabajo.md`** | 392 | **NUEVO**. Tareas concretas y medibles para los 3 contributors: flujo SDD, tareas por fase, entregables, criterios de aceptación, timeline, formato de reporte semanal | 2026-06-11 |
| **`onboarding/cavallero.md`** | — | **ACTUALIZADO**. Onboarding Fase 1 (seguridad GLP) + Fase 2 (User Telemetry) | 2026-06-11 |
| **`onboarding/monfroglio.md`** | — | **ACTUALIZADO**. Onboarding Fase 1 (ML clásico) + Fase 2 (AI Agents) | 2026-06-11 |
| **`onboarding/montanari.md`** | — | **ACTUALIZADO**. Onboarding Fase 1 (QA/CI/CD) + Fase 2 (Observability-Driven QA) | 2026-06-11 |

---

## 2. Campos Abiertos de Investigación (Research Gaps)

Identificados a partir del análisis cruzado de todos los documentos:

| # | Gap | Documento principal | Responsable | Hipótesis |
|---|-----|-------------------|-------------|-----------|
| **G1** | Agente RUM OSS < 20KB con Core Web Vitals + trazas OTel + errores | `rum-agent-deep-dive.md` | Federico (F2) | H5 |
| **G2** | LLM local (< 1B params) para RCA en observabilidad (ningún asistente actual es local) | `observability-tools-analysis.md` | Romeo (F2) | H6 |
| **G3** | User Health Score predictivo open-source (solo existen propietarios) | `frontend-observability.md` | Romeo (F2) | H6 |
| **G4** | Quality gates en CI/CD basados en señales OTel | `frontend-observability.md` | Santiago (F2) | H7 |
| **G5** | Stack completo observabilidad < 2GB RAM (RUM + logs + trazas + métricas + AI) | `tools-analysis.md`, `containers.md` | Todo el equipo | H5-H7 |

---

## 3. Matriz de Correspondencia Contributor ↔ Documentos

### Federico Cavallero

| Leer primero | Luego | Referencia continua |
|-------------|-------|-------------------|
| `onboarding/cavallero.md` | `frontend-observability.md` (secciones 3, 4, 7, 8) | `rum-agent-deep-dive.md` |
| `governance/plan-trabajo.md` (tareas Federico) | `rum-agent-deep-dive.md` (secciones 2, 3, 8, 9) | `hypotheses.md` (H5) |
| `hypotheses.md` (H3 + H5) | `observability-tools-analysis.md` (sección 3.11 Sentry, 3.2 Grafana Faro) | `experiments.md` (EXP-OTel-*) |
| `containers.md` (OTel, Tempo, Alertmanager) | — | `containers.md` |

### Romeo Monfroglio

| Leer primero | Luego | Referencia continua |
|-------------|-------|-------------------|
| `onboarding/monfroglio.md` | `frontend-observability.md` (secciones 5, 6, 10) | `hypotheses.md` (H6) |
| `governance/plan-trabajo.md` (tareas Romeo) | `observability-tools-analysis.md` (sección 3.4 Dynatrace Davis, 3.8 Netdata ML) | `experiments.md` (EXP-AI-*) |
| `hypotheses.md` (H1 + H6) | `rum-agent-deep-dive.md` (secciones 3, 8.4) | `benchmarking.md` |
| `state-of-the-art.md` (sección 2.3 AIOps) | — | — |

### Santiago Montanari

| Leer primero | Luego | Referencia continua |
|-------------|-------|-------------------|
| `onboarding/montanari.md` | `frontend-observability.md` (secciones 6, 7, 11) | `hypotheses.md` (H7) |
| `governance/plan-trabajo.md` (tareas Santiago) | `observability-tools-analysis.md` (sección 3.2 Grafana LGTM, 3.11 Sentry) | `experiments.md` (EXP-QA-*) |
| `hypotheses.md` (H4 + H7) | `rum-agent-deep-dive.md` (sección 3.4 exporter) | `quality-attributes.md` |
| `containers.md` | — | `constraints.md` |

---

### Docs de Referencia
- **Catálogo de venues de publicación**: `docs/research/publication-venues.md` — 50+ conferencias y revistas académicas e industriales

## 4. Timeline de Documentación

```
MAYO 2026
├── docs/adr/0001-reemplazo-elk-por-grafana-loki-prometheus.md
├── openspec/specs/{architecture,research}/* (12 documentos)
├── docs/research/RESEARCH.md
└── onboarding/*.md (versión original)

JUNIO 2026 — REORIENTACIÓN I+D+i
├── ACTUALIZADOS:
│   ├── openspec/specs/research/hypotheses.md (+H5, H6, H7)
│   ├── openspec/specs/research/experiments.md (+EXP-OTel, AI, QA)
│   ├── openspec/specs/architecture/containers.md (+OTel, Tempo, Alertmanager)
│   ├── onboarding/{cavallero,monfroglio,montanari}.md (Fase 1 + Fase 2)
│   ├── onboarding/README.md
│   ├── docs/brief-v2.md (visión UX-céntrica)
│   ├── TEAM_CHARTER.md (roles + DoD)
│   └── docs/research/RESEARCH.md (L5 + papers)
│
├── NUEVOS:
│   ├── governance/plan-trabajo.md (392 líneas)
│   ├── docs/research/frontend-observability.md (929 líneas)
│   ├── docs/research/observability-tools-analysis.md (845 líneas)
│   ├── docs/research/rum-agent-deep-dive.md (1,207 líneas)
│   └── docs/research/INDEX.md ← ESTE DOCUMENTO
│
└── TOTAL NUEVA DOCUMENTACIÓN EN SESIÓN: ~5,338 líneas
```

---

## 5. Papers Planificados

| # | Título tentativo | Venues primarios | Autores | Basado en |
|---|-----------------|-----------------|---------|-----------|
| 1 | IntellOps: Observabilidad Predictiva UX-Céntrica en Recursos Escasos | SREcon, CLEI, JSS | Monfroglio, Cavallero, Montanari, Rodriguez, Nahuel | L1 |
| 2 | Agente RUM Liviano con OTel para Monitoreo de Experiencia de Usuario | SREcon, ObservabilityCON, SPE | Cavallero, Rodriguez, Nahuel | H5, L5 |
| 3 | Predicción de Reclamos de Usuario mediante ML sobre Señales de UX | ISSRE, EMSE, CLEI | Monfroglio, Rodriguez, Nahuel | H6, L6 |
| 4 | Quality Gates basados en OpenTelemetry para CI/CD en I+D+i | FSE, ASE, JSS | Montanari, Rodriguez, Nahuel | H7, L7 |
| 5 | Seguridad en Observabilidad Académica con Stack GLP | CACIC, IEEE LATAM, JAIIO | Cavallero, Rodriguez, Nahuel | H3, L3 |
| 6 | DevOps y QA Automatizado en PI+D+i: Estudio Empírico | EMSE, IST, JAIIO | Montanari, Rodriguez, Nahuel | H4, L4 |

📄 **Ver catálogo completo de venues**: [`docs/research/publication-venues.md`](../docs/research/publication-venues.md)

---

## 6. Glosario de Términos Clave

| Término | Definición |
|---------|------------|
| **RUM** | Real User Monitoring — monitoreo basado en usuarios reales en producción |
| **Core Web Vitals** | Conjunto de métricas Google: LCP (carga), INP (interactividad), CLS (estabilidad) |
| **LCP** | Largest Contentful Paint — tiempo hasta que el contenido principal es visible |
| **INP** | Interaction to Next Paint — latencia de interacciones del usuario |
| **CLS** | Cumulative Layout Shift — estabilidad visual de la página |
| **TTFB** | Time to First Byte — tiempo hasta el primer byte del servidor |
| **FCP** | First Contentful Paint — tiempo hasta primer contenido renderizado |
| **OTel / OpenTelemetry** | Framework CNCF de instrumentación vendor-neutral |
| **LGTM** | Loki + Grafana + Tempo + Mimir — stack de observabilidad Grafana |
| **RED Method** | Rate, Errors, Duration — metodología de monitoreo de servicios |
| **UHS** | User Health Score — score compuesto de salud de experiencia de usuario |
| **RCA** | Root Cause Analysis — análisis de causa raíz de incidentes |
| **OTLP** | OpenTelemetry Protocol — formato de export de datos OTel |

---

## 7. Estadísticas de Investigación

| Métrica | Valor |
|---------|-------|
| **Documentos activos** | 22 |
| **Hipótesis de investigación** | 7 (H1-H7) |
| **Experimentos planificados** | 24 |
| **Papers planificados** | 6 |
| **Plataformas analizadas** | 12 |
| **Líneas de documentación** | ~5,338 |
| **Referencias bibliográficas** | 40+ (W3C, IEEE, ACM, O'Reilly) |
| **Browser APIs documentadas** | 10 |
| **Campos abiertos de investigación** | 5 |
| **Tendencias de industria identificadas** | 6 |

---

*Documento vivo. Versión 1.0 — Junio 2026. Equipo InfraIT GIDAS — UTN FrLP.*
