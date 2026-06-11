# Onboarding — IntellOps

Bienvenido al equipo IntellOps. Este documento te guía en los primeros pasos para que puedas contribuir al proyecto en menos de 30 minutos.

## 0. Aceptar la Invitación de GitHub

Antes que nada: aceptá la invitación al repositorio que te llegó por mail o en https://github.com/infraitgidas/intellops/invitations

Una vez aceptada, clonás el repo:

```bash
git clone https://github.com/infraitgidas/intellops.git
cd intellops
```

## Requisitos del Sistema

- **RAM**: ≥ 4GB (recomendado 8GB)
- **CPU**: Cualquier x86_64 o arm64
- **Disco**: ≥ 10GB libres
- **OS**: Linux (recomendado), macOS, WSL2 en Windows
- **GPU**: No necesaria (todo corre en CPU)

## Dependencias

### Esenciales

```bash
git --version       # >= 2.30
docker --version    # >= 24
docker compose version  # >= 2.20
make --version      # >= 4.0
```

### Python (Backend + ML)

```bash
python --version    # >= 3.11
pip --version       # >= 24
```

### Node.js (Agente RUM + Dashboard — solo si te toca frontend)

```bash
node --version      # >= 20 LTS
npm --version       # >= 10
```

## Setup en 5 Pasos

### 1. Pararse en la Rama Correcta

El desarrollo se hace en `develop`. Los cambios individuales van en ramas `feat/` o `spec/`.

```bash
git checkout develop
```

### 2. Leer la Documentación Clave

Antes de escribir código, entendé el contexto:

| Documento | Qué te va a dar |
|-----------|-----------------|
| `TEAM_CHARTER.md` | Quién es quién, valores del equipo, Definition of Done |
| `openspec/config.yaml` | Cómo está configurado el proyecto SDD |
| `docs/brief-v2.md` | El brief completo del proyecto (estado del arte, stack, roadmap) |
| `openspec/specs/research/hypotheses.md` | Las hipótesis de investigación (encontrá tu línea) |
| `openspec/specs/architecture/containers.md` | Cómo está compuesto el sistema |
| `docs/adr/0001-*.md` | Decisiones arquitectónicas activas |

### 3. Revisar tu Guía de Onboarding Individual

Cada integrante tiene una guía personalizada con **dos fases secuenciales**:

| Integrante | Fase 1 — Fundamentos de Infra | Fase 2 — Observabilidad UX-Céntrica |
|------------|-------------------------------|-------------------------------------|
| Federico Cavallero | Seguridad (CIS, GLP, hardening) | User Telemetry & Tracing (RUM, OTel, Tempo, alertas multicanal) |
| Romeo Monfroglio | ML / Detección de Anomalías (Isolation Forest, forecasting) | Agentes IA para UX Predictiva (RCA, User Health Score, clasificador reclamos) |
| Santiago Montanari | QA / Testing / CI/CD (pipeline, quality gates) | Observability-Driven QA (synthetic journeys OTel, chaos engineering, CBAs) |

Cada guía incluye el checklist completo de ambas fases:

| Integrante | Guía |
|------------|------|
| Federico Cavallero | `onboarding/cavallero.md` |
| Romeo Monfroglio | `onboarding/monfroglio.md` |
| Santiago Montanari | `onboarding/montanari.md` |

### 4. Primer Cambio SDD

Cada cambio en IntellOps sigue el flujo SDD documentado en `CONTRIBUTING.md`. En criollo:

```
1. Abrí un Issue con "Change Proposal" (template en .github/ISSUE_TEMPLATE/)
2. Esperá la review del coordinador
3. Cread la rama:   git checkout -b feat/mi-cambio develop
4. Implementá siguiendo Spec → Design → Tasks → Code
5. PR a develop con mínimo 1 approval
```

### 5. Pedir Ayuda Si Te Trabas

- **Setup no funciona**: Abrí un issue con label `setup`
- **Duda técnica**: Buscá en `docs/adr/` o preguntá en un Discussion de GitHub
- **Urgente**: Contactá al coordinador

## Estructura del Proyecto

```
observabilidad/
├── openspec/              ← Artefactos SDD (specs, changes, config)
│   ├── config.yaml
│   ├── specs/research/    ← Specs de investigación (6 documentos)
│   ├── specs/architecture/ ← Specs de arquitectura (6 documentos)
│   └── changes/           ← Cambios activos y archivados
├── src/
│   ├── api/               ← Backend FastAPI
│   ├── agent/             ← Agente RUM (futuro)
│   ├── dashboard/         ← React frontend (futuro)
│   └── ml/                ← ML Engine (futuro)
├── ml/                    ← Experimentos, datasets
├── tests/                 ← Tests
├── docs/
│   ├── adr/               ← Architecture Decision Records
│   ├── research/          ← Research log
│   └── divulgacion/       ← Notas para público
├── .github/               ← CI/CD, templates
└── governance/            ← SBOM, compliance, continuidad
```

---

## 6. Plan de Trabajo Detallado

Después del onboarding, cada contributor sigue las tareas concretas definidas en:

📋 **`governance/plan-trabajo.md`**

Ese documento contiene:
- El flujo SDD paso a paso con comandos exactos
- Las tareas de **Fase 1** y **Fase 2** para cada contributor
- Entregables medibles y criterios de aceptación por tarea
- Timeline sugerido sprint a sprint
- Formato de reporte semanal de avance

Leelo después de completar este onboarding. Es tu hoja de ruta para todo el proyecto.

---

*Tiempo estimado de onboarding: ≤ 30 minutos.*
*Si te tomó más, abrí un issue para mejorar esta guía.*
