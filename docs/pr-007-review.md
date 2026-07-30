# PR #7 Review: Develop → Main

> **Fecha de análisis**: 2026-07-30
> **Repositorio**: `infraitgidas/intellops`
> **Rama origen**: `develop`
> **Rama destino**: `main`

---

## Resumen Ejecutivo

PR con **+5.399 líneas / -191 eliminadas** en **44 archivos** a través de **25 commits** de **4 contributors**. Esencialmente es la **campaña de documentación inicial** del proyecto: investigación académica, definiciones de negocio, arquitectura de datos, infraestructura, y organización del equipo.

**Estado**: ❌ Sin reviews aún.

---

## Contributors y Aportes

### 1. rodriguezemautn (Emanuel Rodriguez) — Investigación I+D+i

**Commits**: 9 · **Rol**: Investigador principal — reorientación del proyecto hacia observabilidad UX-céntrica

| Archivo | Líneas | Aporte |
|---------|--------|--------|
| `docs/research/rum-agent-deep-dive.md` | +1.207 | Anatomía completa de agentes RUM: 10+ Browser APIs, cálculo de métricas (LCP, INP, CLS, TTFB, FCP), arquitectura OTel Browser SDK, optimización, privacidad, plan de implementación en 5 fases |
| `docs/research/frontend-observability.md` | +929 | Estado del arte: Core Web Vitals, RED method para frontend, RUM vs Synthetic, geolocalización, análisis predictivo con User Health Score, 30+ referencias bibliográficas |
| `docs/research/observability-tools-analysis.md` | +845 | Análisis de 12 plataformas (Datadog, Grafana LGTM, New Relic, Dynatrace, Splunk, SigNoz, OpenObserve, Netdata, Uptrace, HyperDX, Sentry, Elastic), matrices comparativas, 6 tendencias 2025-2026, 5 campos abiertos de investigación, posicionamiento IntellOps en nicho "Bajo Recurso + Alta AI" |
| `README.md` | +362 | README completo del proyecto con enfoque UX-céntrico I+D+i |
| `docs/research/INDEX.md` | +296 | Organización de 22 documentos activos (~5.338 líneas): mapa por área, hallazgos clave, matriz contributor-documentos, timeline, 6 papers planificados, glosario |
| `docs/research/COMO-SEGUIMOS.md` | +227 | Guía de continuidad del proyecto para el equipo |
| `docs/research/publication-venues.md` | +189 | Catálogo de 50+ venues académicos e industriales (JAIIO, CACIC, CLEI, ICSE, FSE, ISSRE, TSE, CSUR, etc.), estrategia de publicación por tipo de paper |
| `docs/research/SESION-2026-06-11.md` | +180 | Resumen y conclusiones de la sesión de investigación que reorientó el proyecto |
| `openspec/specs/research/hypotheses.md` | +146 | Nuevas hipótesis H5 (User Telemetry), H6 (AI Agents), H7 (Obs-Driven QA) + 12 experimentos |
| `governance/plan-trabajo.md` | +392 | Plan de trabajo detallado con tareas concretas por contributor |
| `openspec/specs/architecture/containers.md` | +47 | Containers actualizados: OTel Collector, Tempo, Alertmanager en C4 |
| `TEAM_CHARTER.md`, `docs/brief-v2.md`, `onboarding/*` | +75 | Documentos de equipo y onboarding |

**🎯 Impacto**: Define el **norte académico y técnico** del proyecto. La reorientación de infraestructura-centrica a UX-céntrica es el cambio de paradigma fundamental. Sin este trabajo, el proyecto sería "monitoreo de servidores" en vez de "observabilidad de experiencia de usuario real".

---

### 2. BlancoCavallero (Federico Blanco Cavallero) — Business + Organización + CI

**Commits**: 11 · **Rol**: Líder de negocio y organización del equipo

| Archivo | Líneas | Aporte |
|---------|--------|--------|
| `CONTRIBUTING.md` | +112 | Guía de contribución: conventional commits, flujo de trabajo, estándares del proyecto |
| `docs/business/Análisis de Caso de NegocioV2.pdf` | — | Análisis de caso de negocio del proyecto (versión 2) |
| `docs/business/Especificación de Historias de Usuario v1.2.pdf` | — | HU corregidas y actualizadas |
| `docs/business/Especificación de Historias de Usuario.pdf` | — | HU versión base |
| `RRHH/Federico Cavallero/Cronograma_IntellOps_Blanco_Cavallero_v3.*` | — | Cronograma personal de trabajo |
| `RRHH/Federico Cavallero/Solicitud_Inicio_IntellOps_Blanco_Cavallero_v3.pdf` | — | Solicitud formal de inicio |
| `docs/meetings/20-07-2026` | +35 | Minuta de reunión del equipo |
| `.github/workflows/ci.yml` | +3/-2 | Fix de pipeline CI |
| `src/api/main.py`, `pyproject.toml`, `tests/test_health.py` | +5/-5 | Fixes de health check y configuración de FastAPI |

**🎯 Impacto**: Conecta la **investigación técnica con el negocio**. Las Historias de Usuario son el puente entre "qué investigamos" y "qué construimos". El CONTRIBUTING.md es la base para que el equipo opere con consistencia. Los fixes de CI destrabaron la integración continua.

---

### 3. RomeKai (Romeo L. Monfroglio) — Arquitectura de Datos + Métricas RUM

**Commits**: 4 · **Rol**: Arquitecto de datos e investigación de métricas

| Archivo | Líneas | Aporte |
|---------|--------|--------|
| `docs/der/DER intellops v1.2.pdf` + explicación | — | Diagrama Entidad-Relación V2 con soporte multi-tenant y MLOps — evolución del modelo de datos |
| `docs/der/DER intellops V1.pdf` + explicación | — | DER V1 base |
| `docs/research/Estrategia de Observabilidad — Elección de métricas fundamentales para el MVP.pdf` | — | Investigación y selección de 5 métricas frontend clave para el MVP: **TTFB, FCP, XHR Latency, JS Exceptions, Rage Clicks** |

**🎯 Impacto**: Traduce la investigación de Emanuel a **decisiones concretas de implementación**. La selección de métricas para MVP es el "por dónde empezamos". El DER define cómo se persisten y relacionan los datos de observabilidad, incluyendo soporte multi-tenant que es clave para la arquitectura.

---

### 4. Monta702 (Santiago Montanari) — Infraestructura + Documentación Técnica

**Commits**: 8 (3 merges) · **Rol**: Documentador de infraestructura

| Archivo | Líneas | Aporte |
|---------|--------|--------|
| `docs/infrastructure/Estructura-de-Carpetas-V1.1.2.pdf` | — | Estructura de carpetas del proyecto versionada (V1.1.2) |
| `docs/infrastructure/Estructura-de-Carpetas.V1.pdf` | — | Versión base de la estructura |
| `docs/infrastructure/Investigacion-base-de-datos.pdf` | — | Investigación sobre la base de datos del proyecto |
| `docs/infrastructure/Diagrama-C4.png` | — | Diagrama C4 de contenedores de la arquitectura |
| `docs/meetings/23-07-2026` | +30 | Minuta de la reunión del equipo |
| `docs/infrastructure/Estructura-de-Carpetas.pdf` | — | Versión inicial sin versionado |

**🎯 Impacto**: Pone sobre papel **dónde vive cada cosa** en el proyecto. El diagrama C4 es la representación visual de la arquitectura. La investigación de base de datos y la estructura de carpetas son la base para que cualquier nuevo contributor sepa orientarse.

---

## Estadísticas del PR

```
Total:      44 archivos, +5.399 / -191 líneas
Commits:    25
Autores:    4

Por autor (commits):
  BlancoCavallero   11  (44%)
  Monta702           8  (32%) — incluye 3 merges
  rodriguezemautn    9  (36%)
  RomeKai            4  (16%)

Por tipo de archivo:
  Markdown           ~20 archivos  (~3.500 líneas)
  PDF                ~14 archivos  (binarios, sin diff)
  PNG                ~1 archivo    (Diagrama C4)
  DOCX               ~1 archivo    (Cronograma)
  Código/Python      ~4 archivos   (~10 líneas, fixes)
  YAML               ~1 archivo    (CI)
  TOML               ~1 archivo    (pyproject)
```

---

## Observaciones y Riesgos

### 🟢 Fortalezas

1. **Cobertura completa de dominios**: El PR cubre investigación (Emanuel), negocio (Federico), datos (Romeo) e infraestructura (Santiago) — exactamente las 4 patas que necesita un proyecto I+D+i.
2. **Base académica sólida**: 3 documentos de investigación pesados (+2.900 líneas) con referencias formales, hipótesis y experimentos definidos.
3. **Organización del equipo**: TEAM_CHARTER, onboarding individualizado, plan de trabajo, convención de commits — el equipo está aceitado para arrancar desarrollo.

### 🟡 Debilidades

1. **CERO reviews**: 25 commits y +5.399 líneas sin una sola review. Esto es preocupante para la calidad y para la dinámica de equipo. Si no se reviewn entre ellos ahora con docs, menos lo harán cuando haya código.
2. **Concentración de conocimiento técnico**: ~74% de las líneas de contenido técnico profundo son de un solo contributor (rodriguezemautn). Si él se ausenta, el equipo pierde contexto crítico.
3. **Archivos binarios sin trazabilidad**: 14 PDFs + 1 DOCX + 1 PNG. No se puede hacer diff, no se puede reviewr contenido, no hay historial de cambios real. Riesgo de que queden desactualizados y nadie lo note.

### 🔴 Riesgos

1. **Commits de merge en el PR**: 4 merges de ramas intermedias (`docs/actualizacion`, `docs/HU`, `docs/diagrama-der`). El historial se empieza a enredar. Sugerencia: usar squash merge o rebase antes de mergear a main.
2. **Sin spec link ni ADR**: El template SDD del PR está incompleto: spec link y ADR están en `N/A`. Para un proyecto que arrancó con SDD, esto debería estar correcto.
3. **Template de PR mal usado**: Los checklists de tests, cobertura, licencia, contract tests están vacíos. Si no aplican, deberían marcarse como N/A o eliminarse del template para este tipo de PR.

---

## Veredicto

### ¿Aprobar? → Con condiciones

El PR es **sólido en contenido** pero **débil en proceso**. Mi recomendación:

| Acción | Responsable |
|--------|-------------|
| ✅ **Agregar al menos 1 review** de cualquier otro contributor antes de mergear | Todo el equipo |
| ⚠️ **Reemplazar PDFs críticos con Markdown + Mermaid/PlantUML** (DER, C4, estructura de carpetas) | RomeKai / Santiago |
| ⚠️ **Llenar los campos del template SDD** o al menos marcarlos explícitamente como "No aplica por ser PR de documentación" | Federico (autor del PR) |
| ℹ️ **Considerar squash merge** para mantener el historial de main limpio | Al mergear |
| 🔮 **Agregar una tarea** para distribuir el conocimiento técnico (sesión de transferencia de Emanuel al equipo) | Emanuel |

Una vez resuelto lo mínimo (review + template), **aprobá sin miedo**. La documentación es excelente para arrancar la fase de implementación.

---

*Documento generado a partir del análisis del PR #7 — 2026-07-30*
