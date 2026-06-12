# Cómo Seguimos — Guía de Continuidad del Proyecto

- **Última sesión**: 2026-06-11
- **Commit final**: `76df9b5`
- **Rama**: `develop`

---

## 1. Si Sos un Contributor (Federico, Romeo, Santiago)

### Paso 1: Bajate los cambios

```bash
git checkout develop
git pull origin develop
```

### Paso 2: Encontrá tu onboarding actualizado

| Vos | Tu guía |
|-----|---------|
| **Federico** | `onboarding/cavallero.md` |
| **Romeo** | `onboarding/monfroglio.md` |
| **Santiago** | `onboarding/montanari.md` |

Cada guía tiene **Fase 1** (lo que ya tenías antes, ampliado) + **Fase 2** (la nueva orientación I+D+i).

### Paso 3: Leé tu plan de trabajo

```bash
# Todas las tareas concretas están acá:
cat governance/plan-trabajo.md
```

Buscá tu nombre. Cada tarea tiene: descripción, entregable medible, criterio de aceptación, dependencias, esfuerzo estimado y rama sugerida.

### Paso 4: Arrancá con tu primer Issue

Seguí el flujo SDD documentado en `CONTRIBUTING.md`:

```
1. Abrí un Issue con template "Change Proposal"
2. Esperá la review del coordinador
3. git checkout -b feat/mi-cambio develop
4. Implementá (spec → código → tests)
5. PR a develop
```

### Referencias Rápidas

```bash
make setup    # Prepara el entorno
make up       # Levanta servicios → http://localhost:8000
make test     # Tests unitarios
make test-cov # Tests con cobertura
```

---

## 2. Si Sos el Coordinador (Emanuel)

### Lo que ya está listo

| Aspecto | Estado |
|---------|--------|
| Hipótesis de investigación (H1-H7) | ✅ `openspec/specs/research/hypotheses.md` |
| Experimentos (24 total) | ✅ `openspec/specs/research/experiments.md` |
| Onboarding Fase 1 + Fase 2 | ✅ `onboarding/{cavallero,monfroglio,montanari}.md` |
| Plan de trabajo con tareas concretas | ✅ `governance/plan-trabajo.md` |
| Arquitectura C4 (13 contenedores) | ✅ `openspec/specs/architecture/containers.md` |
| Brief v2 con visión UX-céntrica | ✅ `docs/brief-v2.md` |
| Frontend observability state of the art | ✅ `docs/research/frontend-observability.md` |
| Tools industry analysis (12 herramientas) | ✅ `docs/research/observability-tools-analysis.md` |
| RUM agent deep dive (implementación) | ✅ `docs/research/rum-agent-deep-dive.md` |
| Publication venues (50+ venues) | ✅ `docs/research/publication-venues.md` |
| README del proyecto | ✅ `README.md` |
| TEAM_CHARTER actualizado | ✅ `TEAM_CHARTER.md` |

### Lo que sigue (priorizado)

```
URGENTE (esta semana)
├── Revisar y aprobar los primeros Issues de cambio de cada contributor
├── Asignar tareas de Fase 1 a cada uno
└── Asegurar que los 3 tienen acceso al repo y pueden correr make setup

CORTO PLAZO (sprint 1-2)
├── Que cada contributor complete su Fase 1
├── Federico: Lynis audit + Ansible hardening
├── Romeo: ML Engine skeleton + Isolation Forest baseline
└── Santiago: Pipeline CI real + quality gates

MEDIANO PLAZO (sprint 3+)
├── Federico: PoC agente RUM (Fase 2)
├── Romeo: Clasificador de reclamos + User Health Score
├── Santiago: Synthetic journeys OTel + quality gates OTel
└── Publicar avances en CLEI Jul-Ago o JAIIO Oct

LARGO PLAZO (sprint 11+)
├── Integración de los 3 módulos
├── Experimentos completos con datos reales
├── Papers para ISSRE, SREcon, JSS, EMSE
└── Release del prototipo funcional
```

### Papers planificados

| # | Título | Venue target | Responsable |
|---|-------|-------------|-------------|
| 1 | IntellOps: Observabilidad Predictiva UX-Céntrica en Recursos Escasos | SREcon, CLEI, JSS | Equipo completo |
| 2 | Agente RUM Liviano con OTel para Monitoreo de Experiencia de Usuario | SREcon, ObservabilityCON, SPE | Federico |
| 3 | Predicción de Reclamos de Usuario mediante ML sobre Señales de UX | ISSRE, EMSE, CLEI | Romeo |
| 4 | Quality Gates basados en OpenTelemetry para CI/CD en I+D+i | FSE, ASE, JSS | Santiago |
| 5 | Seguridad en Observabilidad Académica con Stack GLP | CACIC, IEEE LATAM, JAIIO | Federico |
| 6 | DevOps y QA Automatizado en PI+D+i: Estudio Empírico | EMSE, IST, JAIIO | Santiago |

📄 Catálogo completo de venues: `docs/research/publication-venues.md`

### Timeline consolidado

```
Sprint 1-2 │ FASE 1 — Fundamentos de Infra
           │ Federico: Auditoría Lynis → Hardening Ansible
           │ Romeo:    ML Engine skeleton → Isolation Forest
           │ Santiago: Pipeline CI real → Quality gates
           │
Sprint 3-4 │ FASE 2 — Arranque
           │ Federico: Pipeline GLP → PoC agente RUM
           │ Romeo:    Dashboard 3 vistas → Clasificador reclamos
           │ Santiago: Contract testing → Synthetic journeys OTel
           │
Sprint 5-6 │
           │ Federico: Pipeline Tempo OTel → Alertas multicanal
           │ Romeo:    User Health Score → Agente RCA
           │ Santiago: Quality gates OTel → Chaos engineering
           │
Sprint 7-10│
           │ Federico: Benchmark overhead → Optimización bundle
           │ Romeo:    Anomalías en trazas → Benchmark UHS
           │ Santiago: Dashboard CBA → Chaos experiments
           │
Sprint 11-20 │ Integración, experimentos completos, papers, releases
```

---

## 3. Si Sos Nuevo en el Proyecto

### Lectura recomendada (en orden)

```
1. README.md                          → Qué es IntellOps (5 min)
2. onboarding/README.md               → Setup + contexto (10 min)
3. TEAM_CHARTER.md                    → Equipo, valores, DoD (5 min)
4. docs/brief-v2.md                   → Brief completo del proyecto (15 min)
5. docs/research/INDEX.md             → Mapa de toda la investigación (10 min)
6. governance/plan-trabajo.md         → Tareas concretas por rol (15 min)
7. openspec/specs/research/hypotheses.md → Hipótesis de investigación (15 min)
8. openspec/specs/architecture/containers.md → Stack tecnológico (10 min)
```

Tiempo total estimado: ~1.5 horas de lectura.

### Documentos clave por área

| Si te interesa... | Leé |
|-------------------|-----|
| Observabilidad frontend / UX | `docs/research/frontend-observability.md` |
| Herramientas de la industria | `docs/research/observability-tools-analysis.md` |
| Cómo funciona un agente RUM | `docs/research/rum-agent-deep-dive.md` |
| Dónde publicar resultados | `docs/research/publication-venues.md` |
| Arquitectura del sistema | `openspec/specs/architecture/containers.md` |
| Experimentos planificados | `openspec/specs/research/experiments.md` |

---

## 4. Comandos Útiles para el Día a Día

```bash
# Entorno
make setup        # Construye imágenes Docker
make up           # Levanta servicios
make down         # Detiene servicios
make logs         # Logs de servicios

# Calidad
make test         # Tests unitarios
make test-cov     # Tests con cobertura
make lint         # Linters (flake8 + pylint)

# Git
git checkout develop && git pull   # Actualizarse
git checkout -b feat/mi-cambio     # Rama nueva
git add -A && git commit -m "tipo: mensaje"  # Commit convencional
git push origin feat/mi-cambio     # Subir rama

# Documentación
# Los docs están en docs/research/, openspec/specs/, onboarding/, governance/
# Para agregar documentación nueva, crear .md en la carpeta que corresponda
```

---

## 5. Si Vuelvo Después de un Tiempo

Para recuperar contexto rápido:

```bash
# 1. Ver últimos commits
git log --oneline -10

# 2. Ver qué cambió en la última sesión
git diff --stat <commit-anterior>..HEAD

# 3. Leer el resumen de la última sesión
cat docs/research/SESION-2026-06-11.md

# 4. Revisar el índice general
cat docs/research/INDEX.md

# 5. Estado del proyecto
cat README.md
```

---

*Documento vivo. Creado: 2026-06-11. Último commit: 76df9b5.*
