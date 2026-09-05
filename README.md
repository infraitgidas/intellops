# IntellOps 🔭✨

> **Sistema de Observabilidad Predictiva UX-Céntrica + AI/LLM Open-Source**
>
> PI+D+i | Grupo GIDAS | UTN FrLP | Equipo InfraIT

![Coverage](https://img.shields.io/badge/Coverage-%E2%89%A570%25-brightgreen)

<br>

<div align="center">

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED?logo=docker)](docker-compose.yml)
[![PRs](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow)](https://conventionalcommits.org)

</div>

---

## 📋 Tabla de Contenidos

- [¿Qué es IntellOps?](#-qué-es-intellops)
- [El Problema Real](#-el-problema-real)
- [Stack Tecnológico](#-stack-tecnológico)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Quick Start](#-quick-start)
- [Líneas de Investigación](#-líneas-de-investigación)
- [Equipo](#-equipo)
- [Roadmap](#-roadmap)
- [Cómo Contribuir](#-cómo-contribuir)
- [Publicaciones Científicas](#-publicaciones-científicas)
- [Licencia](#-licencia)

---

## 🔭 ¿Qué es IntellOps?

IntellOps es un proyecto de **Investigación, Desarrollo e Innovación (I+D+i)** que diseña e implementa un sistema de observabilidad predictiva centrado en el **usuario real**, no en el servidor.

### La Pregunta de Investigación

> **¿Cómo anticipamos que un usuario va a tener un problema antes de que lo experimente?**

Para responderla, IntellOps integra:

| Pilar | Tecnología | Propósito |
|-------|-----------|-----------|
| **📊 Métricas de UX** | Core Web Vitals + RUM | Medir la experiencia real del usuario (LCP, INP, CLS) |
| **🔗 Trazas distribuidas** | OpenTelemetry + Tempo | Correlacionar el viaje completo del usuario frontend → backend |
| **📝 Logs de frontend** | OpenTelemetry + Loki | Capturar errores JS y contexto de sesión |
| **🤖 Agentes IA** | Llama 3.2 1B + scikit-learn | Predecir reclamos y analizar causa raíz |
| **📢 Alertas multicanal** | Grafana Alertmanager | Notificar por Mail, Telegram y WhatsApp según severidad |

Todo corriendo en **< 2GB RAM**, **CPU-only**, **$0/mes** de costo operativo.

---

## 🎯 El Problema Real

La observabilidad tradicional monitorea servidores (CPU, RAM, disco). Pero el servidor puede estar perfecto y el usuario frustrado.

```
MONITOREO TRADICIONAL                        OBSERVABILIDAD UX
"El servidor responde en 50ms"               "El usuario en Salta con 4G tuvo LCP de 4.7s"
"CPU al 30%"                                 "El usuario en CABA con fibra tuvo LCP de 1.2s"
"Sin errores 5xx"                            "3 usuarios tuvieron errores JS en checkout"
"Todo verde en Grafana"                      "User Health Score cayó a 45 en la última hora"
```

**La diferencia**: el monitoreo tradicional te dice "está funcionando". La observabilidad UX te dice "cómo funciona para CADA usuario real".

### ¿Por qué es I+D+i?

| Aspecto | Problema abierto |
|---------|-----------------|
| **Agente RUM < 20KB** | No existe un agente RUM OSS que capture Core Web Vitals + trazas OTel + errores con bundle < 20KB |
| **LLM local para RCA** | Todos los asistentes AI de observabilidad (Datadog Bits AI, Dynatrace Davis) son cloud. Ninguno corre en CPU local |
| **User Health Score** | No existe un estándar abierto para sintetizar señales UX en un score predictivo |
| **Quality Gates OTel** | Ninguna herramienta actual permite usar señales OTel como gates de CI/CD |
| **Stack completo < 2GB** | Ninguna plataforma ofrece RUM + logs + trazas + métricas + AI en hardware modesto |

---

## 🏗 Stack Tecnológico

```
[Usuarios Reales]
     │
     ▼
┌──────────────────────────────────────┐
│  Agente RUM IntellOps                │  ← JS < 20KB gzip
│  (OTel JS + web-vitals + errores)    │     Core Web Vitals + trazas
└──────────────┬───────────────────────┘
               │ OTLP HTTP
               ▼
┌──────────────────────────────────────┐
│  OpenTelemetry Collector             │  ← ~100MB RAM
│  (recepción, procesamiento, ruteo)   │     OTLP nativo
└──────┬──────────┬──────────┬─────────┘
       │          │          │
       ▼          ▼          ▼
┌─────────┐ ┌──────────┐ ┌──────────┐
│  Tempo  │ │   Loki   │ │  Mimir   │  ← Stack LGTM
│ (trazas)│ │  (logs)  │ │(métricas)│     ~256MB c/u
└────┬────┘ └────┬─────┘ └────┬─────┘
     │          │          │
     └──────────┼──────────┘
               ▼
┌──────────────────────────────────────┐
│  Grafana                             │  ← ~256MB RAM
│  Dashboards + Alertas + Explore      │     + Alertmanager
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  AI Agents                           │  ← ML < 50MB RAM
│  └→ User Health Score                │     LLM ~600MB (bajo demanda)
│  └→ Clasificador de reclamos         │
│  └→ RCA con LLM local (Llama 1B)     │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  Alertmanager                        │  ← ~50MB RAM
│  └→ Mail (SMTP)                      │     Routing por severidad
│  └→ Telegram (Bot API)               │
│  └→ WhatsApp (API Business)          │
└──────────────────────────────────────┘

🔄 Self-monitoring: Netdata (~150MB RAM, eBPF, ML en edge)
📦 Footprint total estable: ~1.5GB RAM | Pico: ~2.3GB RAM (con LLM)
💰 Costo operativo: $0/mes (self-hosted + free-tier cloud)
```

---

## 📁 Estructura del Proyecto

```
observabilidad/
│
├── openspec/                  ← ❄️ Especificaciones SDD (fuente de verdad)
│   ├── config.yaml            ─ Configuración del proyecto
│   ├── specs/
│   │   ├── architecture/      ─ 6 docs: C4, componentes, APIs, constraints
│   │   └── research/          ─ 6 docs: hipótesis, experimentos, SotA, benchmarks
│   └── changes/               ─ Cambios activos y archivados
│
├── docs/                      ← 📚 Documentación
│   ├── adr/                   ─ Architecture Decision Records
│   ├── research/              ─ Investigación: frontend, tools, RUM agent
│   └── divulgacion/           ─ Material para visitantes del laboratorio
│
├── src/                       ← 💻 Código fuente
│   ├── api/                   ─ FastAPI backend (2 endpoints activos)
│   ├── agent/                 ─ Agente RUM (en desarrollo, Fase 2)
│   └── ml/                    ─ ML Engine (en desarrollo, Fase 2)
│
├── tests/                     ─ 🧪 Suites de pruebas
├── ml/                        ─ Experimentos, datasets, modelos
├── onboarding/                ─ Guías de onboarding por contributor
├── governance/                ─ SBOM, compliance, plan de trabajo
├── scripts/                   ─ Automatización
├── public/                    ─ Assets gráficos (logos UTN, GIDAS)
└── RRHH/                      ─ Documentos administrativos PPS

📄 TEAM_CHARTER.md             → Quién es quién, valores, DoD
📄 CONTRIBUTING.md             → Cómo contribuir (flujo SDD)
📄 CHANGELOG.md                → Registro de versiones
📄 CODE_OF_CONDUCT.md          → Código de conducta
📄 pyproject.toml              → Dependencias y configuración
📄 Makefile                    → Comandos esenciales
📄 Dockerfile                  → Imagen del backend
📄 docker-compose.yml          → Stack de desarrollo
```

---

## 🚀 Quick Start

### Requisitos

- **RAM**: ≥ 4GB (recomendado 8GB)
- **CPU**: Cualquier x86_64 o arm64
- **Disco**: ≥ 10GB libres
- **OS**: Linux (recomendado), macOS, WSL2
- **Dependencias**: Docker ≥ 24, Docker Compose ≥ 2.20, Make ≥ 4.0

### Setup en 30 segundos

```bash
git clone https://github.com/infraitgidas/intellops.git
cd intellops

make setup   # Construye imágenes
make up      # Levanta servicios → http://localhost:8000
make test    # Corre tests → todo verde ✅
```

### Comandos Disponibles

```bash
make setup      # Prepara el entorno
make up         # Levanta servicios
make down       # Detiene servicios
make test       # Tests unitarios
make test-cov   # Tests con cobertura
make lint       # Linters (flake8 + pylint)
make logs       # Logs de servicios
make clean      # Limpia artefactos
```

### Endpoints Activos

| Endpoint | Descripción |
|----------|-------------|
| `GET /health` | Health check → `{"status": "ok"}` |
| `GET /ready` | Readiness check → `{"status": "ready"}` |
| `GET /docs` | Swagger UI |
| `GET /redoc` | Redoc UI |

---

## 🔬 Líneas de Investigación

| Línea | Título | Responsable | Hipótesis |
|-------|--------|-------------|-----------|
| **L1** | Observabilidad Predictiva en Recursos Escasos | Romeo Monfroglio | H1 — ML liviano para anomalías |
| **L2** | GenIA Local para Asistencia en Incidentes | TBD | H2 — LLM 1B para RCA |
| **L3** | Seguridad en Observabilidad Académica | Federico Cavallero | H3 — CIS + GLP en $0 |
| **L4** | DevOps y QA Automatizado en PI+D+i | Santiago Montanari | H4 — CI/CD con quality gates |
| **L5** | User Telemetry con OpenTelemetry | Federico Cavallero (F2) | H5 — RUM + Tempo + alertas |
| **L6** | Agentes IA para UX Predictiva | Romeo Monfroglio (F2) | H6 — clasificador + UHS + RCA |
| **L7** | Observability-Driven QA | Santiago Montanari (F2) | H7 — quality gates OTel |

📄 **Ver**: [`openspec/specs/research/hypotheses.md`](openspec/specs/research/hypotheses.md)

### Experimentos Planificados: 24

| Grupo | Experimentos | Responsable |
|-------|-------------|-------------|
| EXP-001 a 004 | ML clásico (Isolation Forest, ensambles) | Romeo (F1) |
| EXP-101 a 103 | LLM + RAG para RCA | TBD |
| EXP-201 a 203 | Seguridad (hardening, pipeline, dashboards) | Federico (F1) |
| EXP-301 a 303 | QA (CI/CD, contract, benchmarks) | Santiago (F1) |
| **EXP-OTel-01 a 04** | RUM, Tempo, alertas, benchmarks | **Federico (F2)** |
| **EXP-AI-01 a 04** | Clasificador, RCA, UHS, anomalías | **Romeo (F2)** |
| **EXP-QA-01 a 04** | Synthetic journeys, chaos, CBA | **Santiago (F2)** |

📄 **Ver**: [`openspec/specs/research/experiments.md`](openspec/specs/research/experiments.md)

### Documentos de Investigación

| Documento | Líneas | Contenido |
|-----------|--------|-----------|
| [`frontend-observability.md`](docs/research/frontend-observability.md) | 929 | Core Web Vitals, RUM, RED method, OTel browser, geolocalización, análisis predictivo |
| [`observability-tools-analysis.md`](docs/research/observability-tools-analysis.md) | 845 | Análisis de 12 herramientas, tendencias, research gaps |
| [`rum-agent-deep-dive.md`](docs/research/rum-agent-deep-dive.md) | 1,207 | Arquitectura de agente RUM, APIs, bundle optimization, implementación |
| [`state-of-the-art.md`](openspec/specs/research/state-of-the-art.md) | 153 | SLR de observabilidad: evolución, plataformas, estándares |
| [`INDEX.md`](docs/research/INDEX.md) | 291 | Mapa completo de los 22 documentos activos |

---

## 👥 Equipo

| Rol | Nombre | Módulo | Período |
|-----|--------|--------|---------|
| **Coordinador / Arquitecto** | Emanuel Rodriguez | Dirección técnica, SDD, visión I+D+i | 2026-2027 |
| **Director / Sponsor** | Ing. Leopoldo Nahuel | Dirección académica, laboratorio GIDAS | 2026-2027 |
| **Desarrollador — User Telemetry** | Federico Blanco Cavallero | F1: Seguridad / F2: RUM + Tempo + alertas | Jun-Oct 2026 |
| **Desarrollador — ML/AI Agents** | Romeo Lorenzo Monfroglio | F1: ML clásico / F2: UHS + RCA + clasificador | May-Sep 2026 |
| **Desarrollador — QA/Observability** | Santiago Montanari | F1: QA + CI/CD / F2: Quality Gates OTel | Jun-Oct 2026 |

📄 **Ver**: [`TEAM_CHARTER.md`](TEAM_CHARTER.md)

---

## 🗺 Roadmap

```
FASE 0 ─ Discovery    (Sprint 1-2)  ← Completado
  └── Brief, specs, hipótesis, onboarding

FASE 1 ─ Fundamentos (Sprint 1-2)
  ├── Federico: Lynis audit → Ansible hardening → Pipeline GLP
  ├── Romeo:    ML Engine skeleton → IF baseline → Dashboard
  └── Santiago: Pipeline CI real → Quality gates → Contract testing

FASE 2 ─ Observabilidad UX (Sprint 3-10)
  ├── Federico: Agente RUM → Pipeline Tempo → Alertas → Benchmark
  ├── Romeo:    Clasificador → User Health Score → RCA LLM → Anomalías
  └── Santiago: Synthetic journeys → Gates OTel → Chaos → CBA

FASE 3 ─ Validación   (Sprint 11-18)
  └── SUS testing, benchmarks, experimentos completos

FASE 4 ─ Publicación  (Sprint 19-24)
  └── Publicaciones en conferencias y revistas, releases, comunidad
```

📄 **Ver**: [`governance/plan-trabajo.md`](governance/plan-trabajo.md)

---

## 🤝 Cómo Contribuir

1. **Leé el onboarding**: [`onboarding/README.md`](onboarding/README.md)
2. **Encontrá tu guía**: según tu rol (`onboarding/cavallero.md`, `monfroglio.md` o `montanari.md`)
3. **Seguí el flujo SDD**: [`CONTRIBUTING.md`](CONTRIBUTING.md)

```
Idea → Issue (Change Proposal) → Review → Rama → Spec → Código → Tests → PR → Archive
```

**Reglas de oro**:
- Una rama por cambio
- Tests antes del código
- PR a `develop`, no a `main`
- Sin merge propio (mínimo 1 approval)
- Commits en inglés con [Conventional Commits](https://www.conventionalcommits.org/)

---

## 📖 Publicaciones Científicas

| Título Tentativo | Venues Primarios | Autores |
|-----------------|-----------------|---------|
| IntellOps: Observabilidad Predictiva UX-Céntrica en Recursos Escasos | SREcon, CLEI, JSS | Monfroglio, Cavallero, Montanari, Rodriguez, Nahuel |
| Agente RUM Liviano con OpenTelemetry para Monitoreo de Experiencia de Usuario | SREcon, ObservabilityCON, SPE | Cavallero, Rodriguez, Nahuel |
| Predicción de Reclamos de Usuario mediante ML sobre Señales de UX | ISSRE, EMSE, CLEI | Monfroglio, Rodriguez, Nahuel |
| Quality Gates basados en OpenTelemetry para CI/CD en I+D+i | FSE, ASE, JSS | Montanari, Rodriguez, Nahuel |
| Seguridad en Observabilidad Académica con Stack GLP | CACIC, IEEE LATAM, JAIIO | Cavallero, Rodriguez, Nahuel |
| DevOps y QA Automatizado en Proyectos de Investigación: Un Estudio Empírico | EMSE, IST, JAIIO | Montanari, Rodriguez, Nahuel |

📄 **Ver catálogo completo de venues**: [`docs/research/publication-venues.md`](docs/research/publication-venues.md)

---

## 📄 Licencia

```
IntellOps — Sistema de Observabilidad Predictiva UX-Céntrica + AI/LLM Open-Source
Copyright 2026 — Equipo InfraIT GIDAS — UTN FrLP

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0
```

---

<div align="center">

**IntellOps** — Proyecto de I+D+i del Grupo GIDAS — UTN Facultad Regional La Plata

[GitHub](https://github.com/infraitgidas/intellops) · [Docs](https://github.com/infraitgidas/intellops/tree/develop/docs) · [Issues](https://github.com/infraitgidas/intellops/issues)

</div>
