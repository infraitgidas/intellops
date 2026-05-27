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

Cada integrante tiene una guía personalizada con sus primeros pasos específicos:

| Integrante | Módulo | Guía |
|------------|--------|------|
| Federico Cavallero | Seguridad (hardening CIS + Grafana/Loki/Prometheus) | `onboarding/cavallero.md` |
| Romeo Monfroglio | ML / Detección de Anomalías | `onboarding/monfroglio.md` |
| Santiago Montanari | QA / Testing / CI/CD | `onboarding/montanari.md` |

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

*Tiempo estimado de onboarding: ≤ 30 minutos.*
*Si te tomó más, abrí un issue para mejorar esta guía.*
