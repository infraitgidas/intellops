# IntellOps — Guía para Desarrolladores (Onboarding y Arquitectura)

**Documento**: `audiencias/desarrolladores.md`
**Fecha**: 2026-09-11
**Audiencia**: contributors PPS, colaboradores GIDAS, contribuyentes open-source, adoptantes técnicos.
**Objetivo**: que una persona **nueva** en el proyecto (o un bot de CI) sepa *qué hay, cómo se estructura, cómo
colaborar y cómo verificar que su trabajo está bien hecho* — en una sola lectura.

---

## 1. Stack y decisiones (resumen ejecutivo)

| Capa | Tecnología | ¿Por qué? (decisión) |
|---|---|---|
| Frontend | **React + TypeScript** (Vite, static, D3) | D-2026-02 (brief-v2) — dashboard web responsive; PWA futura |
| Backend | **FastAPI** (Python 3.12+) | D-2026-03 — standalone, OCP-friendly, auto-OpenAPI 3.1 |
| Persistencia | **PostgreSQL + SQLModel + Alembic** | **ADR-0002** (2026-09-11) — reemplaza SQLite (D-2026-04 superseded) |
| ORM/Contratos | SQLModel + SQLAlchemy 2.x, Pydantic v2 | ADR-0002 — tipado end-to-end TS↔Python |
| Observabilidad internos | OpenTelemetry SDK + OTLP | ADR-0001 — GLP (Grafana/Loki/Prometheus) en vez de ELK |
| CI/CD | GitHub Actions + quality gates | PPS Santiago · Spec-Driven (SDD) |
| Ejecución | Docker/Podman + VM Rocky 10 | PID contexto §4 · ADR-0002 (VM Rocky 10 elimina restricción) |

> **⚠️ Estado de la implementación**: el MVP está en transición a **PostgreSQL + SQLModel (ADR-0002)**.
> `docker-compose.yml` y `src/api/requirements.txt` aún reflejan el estado SQLite. Si trabajás en esta
> ventana, usá la rama `gestionProyecto` + ADR-0002 como **fuente de verdad transitoria**. La actualización
> del compose/API es un todo del backlog (T-020.3 → E03).

---

## 2. Mapa de directorios

```
gestionProyecto/
├── README.md                       # Índice maestro — empezá por acá
├── objetivo-alcance.md             # Visión consolidada (qué/cuánto/cómo)
├── marco/                          # Marco conceptual e ingenieril
│   ├── 01-objetivo.md              #   Objetivo macro + KPIs
│   ├── 02-analisis.md              #   Problema, mercado, factibilidad, stakeholders
│   ├── 03-diseno.md                #   Arquitectura C4, contenedores, ciclos, ADRs
│   └── 04-especificaciones.md      #   Requisitos RF/RF/*, contratos, DoD sistema, matriz trazabilidad
├── backlog/backlog.md              # Backlog diario del MVP (MoSCoW, sprints)
├── decisiones/                     # Análisis de casos de cambio (antes del ADR)
│   └── caso-postgresql-vs-sqlite.md
├── roadmap/                        # Roadmaps: producto (2026-2030) y MVP-PPS
│   ├── roadmap-producto.md
│   └── roadmap-mvp-pps.md
├── audiencias/                     # Docs por audiencia (interesados/negocio/desarrolladores)
│   ├── interesados.md
│   ├── negocio.md
│   └── desarrolladores.md
├── equipo/                         # Análisis de PPS y acoplamiento
│   └── analisis-pps-acoplamiento.md
├── pid/                            # Resumen del PID (verificado contra fuente)
│   └── resumen-pid.md
└── diagramas/                      # Uso: `make diagrams` → png
    ├── diagrama-macro-actividades.{puml,png}
    ├── diagrama-modulos-paquetes.{puml,png}
    └── diagrama-actividades.{puml,png}

docs/
├── adr/                            # Registro de Decisiones — leé esto primero
│   ├── 0001-reemplazo-elk-por-grafana-loki-prometheus.md
│   └── 0002-reemplazo-sqlite-por-postgresql.md
├── brief-v2.md                     # Brief original de producto (marco conceptual, §4.1 histórico)
└── research/, pid/, papers/        # Estado del arte, PID, divulgación

src/
├── api/                            # FastAPI (contratos OpenAPI en /docs, /openapi.json)
└── frontend/                       # React+TS (Vite) — por crear en backlog
```

---

## 3. Contratos de datos (la columna vertebral)

El desarrollo es **Spec-Driven**: los contratos se definen **antes** del código y CI los valida.

| Contrato | Formato | Ubicación / generación |
|---|---|---|
| API REST | OpenAPI 3.1 | `src/api/main.py` → `/openapi.json` (auto) |
| Eventos asíncronos | AsyncAPI 3.0 | en backlog (contrato de eventos — Santiago/Federico) |
| Esquemas de datos | SQLModel / Pydantic v2 | `src/api` (SQLModel) · migraciones Alembic |
| Trazas | OTLP (OpenTelemetry) | SDK emisor + Tempo/Grafana (ADR-0001) |
| Dashboards | JSON versionados (Grafana provisioning) | GLP — `M-SEG` (Federico) |

**Regla de oro**: si un endpoint cambia su schema, eso es un **cambio de contrato** → requiere versión de spec
publicada y coordinación con los consumidores, no solo un PR.

---

## 4. Definición de Listo (DoD) por módulo

Cada módulo (épica) tiene su DoD verificable — extraído del backlog. Ejemplos nucleares:

### M-ING (ingesta — coordinación)
- Ingesta ≥ 1K m/s en VM legacy · latencia P95 < 500ms.
- PostgreSQL + SQLModel + Alembic (ADR-0002) — migraciones versionadas.
- Data model alineado a `docs/research/Estrategia...` (señales núcleo).
- CI verde, coverage ≥ 70%, healthcheck.

### M-SEG (seguridad — Federico)
- Hardening CIS (Lynis ≥ 70%), antes/después documentado.
- Dashboards GLP con eventos de seguridad (JSON versionados).
- Detección evento simulado < 60s · contrato de eventos publicado.

### M-ML (anomalías + health score — Romeo)
- Baseline Isolation Forest + z-score (F1 ≥ 0.70).
- Health Score 0-100 (pesos configurables) correlacionado r > 0.75.
- Reproducible: `make reproduce` (seeds + experimento versionado EXP-001).

### M-QA (calidad — Santiago)
- Pipeline GA (< 10 min): lint → unit → integration → contract → build.
- Gates: coverage < 70% bloquea · warnings bloquean.
- Suite unitaria + integración + E2E (3 escenarios) + informe de carga.

---

## 5. Flujo de trabajo y VCS

1. **Rama por épica**: `E0X/descripcion` desde `gestionProyecto` (o `main` una vez consolidado).
2. **Spec primero**: si tocás un contrato, primero actualizá la spec y *después* el código.
3. **PR mínimo y revisable**: < 400 líneas de diff salvo excepción documentada; PR con tests.
4. **Gates de CI**: unit → integration → contract → build. *Nada entra a `main` con gate en rojo.*
5. **Conventional commits**: `feat:` · `fix:` · `docs:` · `refactor:` · `test:` · `chore:` · `docs(adr):`.
6. **Experimentación versionada**: datos y modelos en DVC; resultados reproducibles (`make reproduce`).

---

## 6. Convenciones de código

| Ámbito | Convención |
|---|---|
| Python | Black formatter · Ruff lint · type hints estrictas (mypy en CI) · docstrings módulo |
| Python (dominio) | Interfaces en raíz de módulo, implementaciones en `impl/` — testeo por contrato |
| TypeScript | ESLint + Prettier · tipos estrictos · componentes presentacionales/container |
| Migraciones | Alembic — **una migración por cambio de schema**, nunca editar una ya aplicada |
| Datos | Seeds versionados · schemas públicos · sin datos sensibles en repo |
| Docs | Markdown, un doc por tema, tablas, DoD verificable, ADR para decisiones |

---

## 7. Arranque rápido (estado transitorio — ver §1)

Con la dependencia de PostgreSQL ya aprobada (ADR-0002), el arranque canónico queda:

```bash
# 1. Clonar / situarse en la rama de trabajo
git clone <repo> && cd intellops && git checkout gestionProyecto

# 2. Fundaciones
docker compose up -d db            # PostgreSQL (ADR-0002) — servicio db
docker compose up -d api           # FastAPI (compila sobre el código)

# 3. Aplicar migraciones y seed
alembic upgrade head && python -m seeds.seed_all

# 4. Verificar
curl http://localhost:8000/health  # → {"status":"ok"}
open http://localhost:8000/docs    # OpenAPI vivo (contracto auto-publicado)
```

> El `docker-compose.yml` actual se actualizará al ADR-0002 en el backlog **T-020.3 → Épica E03**.
> Mientras tanto, tratá la definición anterior como el estado objetivo.

---

## 8. Definición de Terminado (Definition of Done) del contribuidor

Para que un entregable PPS (o contribución OSS) se considere **cerrado**:

- [ ] Especificación del módulo ↔ backlog actualizadas.
- [ ] Código mergeado con CI verde + coverage ≥ 70%.
- [ ] Tests unit + integration + (si aplica) E2E.
- [ ] Contratos (OpenAPI/AsyncAPI) publicados y consumibles.
- [ ] ADR/Decisión documentada si hubo cambio de stack.
- [ ] Doc de módulo actualizado (qué hace, cómo se usa, cómo se prueba).
- [ ] Demo/validación (donde aplique: dashboards, health score, jailbreak test).
- [ ] Metadata del PID: correlación experimento ↔ objetivo específico ↔ KPI.

---

## 9. Seguridad por diseño (lo que todo dev debe respetar)

- Hardening CIS con Lynis como gate (verde solo si ≥ 70%) — **M-SEG**.
- Logs de seguridad al GLP (ADR-0001), nunca a un archivo local sin correlación.
- **Cero secretos en repo**: `.env` ignorado; secretos vía compose/config externa.
- GenIA corre **local** (LLM cuantizado) — no se envían datos fuera de la VM por defecto ✅ ADR-0002.
- Dependencias auditadas (SBOM generado en CI) · repositorios públicos Apache-2.0.

---

## 10. Recursos / referencias para profundizar

| Recurso | Para qué |
|---|---|
| `marco/03-diseno.md` | Arquitectura C4 completa + decisiones |
| `docs/adr/0001` y `0002` | El "porqué" de cada elección de stack (leelos antes de opinar sobre stack) |
| `marco/04-especificaciones.md` §6 | DoD sistema + criterios de aceptación |
| `backlog/backlog.md` | Qué se está haciendo ahora y qué sigue (legend: Must/Should/Could) |
| `roadmap/roadmap-mvp-pps.md` | Quién entrega qué y cuándo (contratos de las PPS) |
| `decisiones/caso-postgresql-vs-sqlite.md` | El análisis de caso que llevó al ADR-0002 |

*Documento vivo — actualizalo cuando cambies algún contrato o convención que acá se describe.*