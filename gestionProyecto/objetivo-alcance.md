# IntellOps — Objetivo y Alcance (Visión Consolidada)

**Documento**: `objetivo-alcance.md`
**Fecha**: 2026-09-11
**Autor**: Coordinación InfraIT — Emanuel Rodríguez
**Audiencia**: interesados (dirección, GIDAS, UTN), colaboradores, y cualquier persona que se aproxime por primera vez al proyecto.
**Propósito**: responder en 10 minutos *qué es IntellOps, por qué existe, qué cubre (y qué no), y qué va a entregar*.
**Referencias**: marco conceptual (`marco/01-objetivo.md` … `marco/04-especificaciones.md`) · PID (`pid/resumen-pid.md`) · ADR-0001 y ADR-0002 (`docs/adr/`).

---

## 1. ¿Qué es IntellOps? (elevator pitch)

> **IntellOps** es un sistema de **observabilidad predictiva centrada en la experiencia del usuario (UX)**:
> captura, correlaciona y analiza métricas del frontend (performance, errores, uso real) junto con señales
> de producto e infraestructura, y aplica **IA (AIOps)** para **anticipar fallas antes de que el usuario las
> padezca** — con recursos escasos (hardware on-premise + free-tier cloud, **$0/mes de operación**).

La tesis diferencial: el monitoreo clásico responde "¿está el servidor caído?". IntellOps responde
**"¿cómo lo está viviendo el usuario?"** y reconstruye la cadena causal
`experiencia → producto → infraestructura` para explicar y anticipar el impacto.

## 2. ¿Por qué existe? (el problema)

- Las infraestructuras IT son cada vez más híbridas y distribuidas, y la producción de software asistida por IA acelera su complejidad.
- Las herramientas de observabilidad tradicionales (ELK, Datadog...) son caras, complejas y **miran la infraestructura, no al usuario**.
- Los equipos detectan fallas tarde: el usuario ya las padeció cuando el dashboard se enciende.
- Los laboratorios académicos y las pymes **no pueden pagar** las soluciones comerciales (foco del proyecto: transferencia a pymes, empresas y organismos).

**Respuesta del PID**: generar un prototipo de plataforma que combine observabilidad avanzada con IA para optimizar la detección de cuellos de botella, anticipar fallas y mejorar eficiencia/confiabilidad/agilidad (PID TC GIDAS, 2027–2030).

**Respuesta de IntellOps (hoy)**: construir ya la materialización del producto, con estándares abiertos y costo cero, ejecutada por las PPS 2026.

## 3. Objetivo

### 3.1. Objetivo general

> Diseñar e implementar **IntellOps**: plataforma de observabilidad predictiva centrada en el usuario,
> que integre telemetría UX (frontend), señales de producto e infraestructura, procesamiento con IA
> (AIOps) y mecanismos de acción (alertas, dashboards, asistente RCA) — operando en **recursos escasos**,
> generando valor diferencial medible para la organización y aportando metodologías, datos y
> publicaciones científicas al PID de Observabilidad de GIDAS.

### 3.2. Objetivos específicos (resumen)

| # | Objetivo | KPI de éxito |
|---|---|---|
| IO1 | Capturar métricas UX (RUM): LCP, INP, CLS, TTFB, errores, journeys | overhead < 3% · bundle < 30KB |
| IO2 | Pipeline de ingesta/almacenamiento/consulta con estándares abiertos | ingesta ≥ 1K m/s · ≤ 500ms |
| IO3 | Detectar anomalías y anticipar fallas con IA (baseline IF + z-score) | F1 ≥ 0.70 · detección < 10s |
| IO4 | User Health Score + clasificación predictiva de reclamos | correlación r > 0.75 |
| IO5 | Acción: alertas multicanal, dashboards 3 capas, RCA con LLM local+RAG | precisión factual ≥ 80% |
| IO6 | Seguridad por diseño (hardening CIS) + calidad verificable (CI/CD, gates) | Lynis ≥ 70% · coverage ≥ 70% |
| IO7 | Evaluar impacto y documentar resultados publicables | 1+ publicación por fase |

### 3.3. Ondas de señal (las 3 capas)

1. **Experiencia (RUM)**: Core Web Vitals, errores de frontend, sesiones, journeys.
2. **Producto**: latencias p95/p99, throughput, error rate, trazas distribuidas OTel, SLOs.
3. **Infraestructura**: CPU/memoria/red/disco, logs de seguridad (GLP: Grafana+Loki+Prometheus).

Inteligenciadas por IA y disparando acción: alertas, dashboards, asistente conversacional, retroalimentación al backlog.

## 4. Alcance

### 4.1. Dentro de alcance (MVP, PPS 2026)

- Captura RUM productivo (agente JS, bundle < 30KB).
- Ingesta FastAPI + almacenamiento **PostgreSQL con SQLModel** (ADR-0002) + migraciones Alembic.
- Correlación métricas/logs/trazas (GLP + Tempo) bajo estándares abiertos.
- Detección de anomalías (Isolation Forest + z-score) y User Health Score (0–100).
- Dashboard web React+TS con 3 vistas: resumen, infraestructura, IA/anomalías.
- Alertas multicanal por severidad (mail, Telegram, WhatsApp).
- Seguridad: hardening CIS, pipeline GLP de eventos, dashboards de seguridad (M-SEG, Federico).
- Calidad: CI/CD GitHub Actions, quality gates, tests unit/integration/E2E (M-QA, Santiago).
- Operación en **VM Rocky 10** con Docker/Podman (ADR-0002 contexto).

### 4.2. Fuera de alcance (ahora)

| Excluido | Razón / cuándo entra |
|---|---|
| APM en producción externa | Solo apps/servicios del laboratorio GIDAS |
| GPU / entrenamiento pesado (LSTM, Prophet) | CPU + modelos cuantizados; extensión post-MVP |
| App mobile nativa | Dashboard web responsive; PWA como extensión |
| Logs no estructurados masivos | Foco en métricas y trazas; logs planos fuera del MVP |
| Integraciones enterprise (Jira/ServiceNow) | Webhooks genéricos |
| RCA asistido por LLM (E10) | Post-PPS, F1 2027 (Romeo) |
| Quality gates OTel / synthetic journeys (E11) | Post-PPS, F1 2027 (Santiago) |
| Transferencia externa a pymes/organismos | Fase 3 del roadmap (2029) |

## 5. Entregables clave (macro)

| Categoría | Entregable | Estado/ventana |
|---|---|---|
| Decisiones | ADR-0001 (GLP) · ADR-0002 (PostgreSQL) | ✅ Aceptados (2026-09) |
| Marco | Objetivo · Análisis · Diseño · Especificaciones | ✅ v1.0 (2026-09) |
| Backlog | Épicas E01–E12 priorizadas (MoSCoW) + planificación | ✅ 2026-09 |
| Roadmap | Producto completo (2026–2030) + MVP-PPS | ✅ 2026-09 |
| Diagramas | Actividades (proceso) · Módulos y paquetes (C4) · Macro actividades | ✅ PNG 2026-09 |
| MVP-0 | Entregables F0 del roadmap (PPS: M-SEG, M-ML, M-QA, M-ING) | 🚧 jun–oct 2026 |
| MVP-1 | Validado con SUS > 75 + papers base por módulo | 🚧 ene–jun 2027 |
| Prototipo PID | Implementación inicial (fase E2) → escalable (E3) | 🚧 2028–2029 |
| Comunidad | Release estable Apache-2.0, SBOM, docs vivas | 🚧 2029–2030 |

## 6. Criterios de éxito del sistema (Definition of Done nivel sistema)

Extraídos de `marco/04-especificaciones.md` §6:

1. Contribución PPS de 200hs == **ladrillo verificable** del mismo edificio (módulos acoplados por contratos publicados).
2. Stack MVP verificado por **ADR-0002** (PostgreSQL + SQLModel) funcionando en VM Rocky 10 con Docker/Podman.
3. Reproducibilidad total: `docker compose up` / `podman` con datos seed y **$0/mes**.
4. Cobertura ≥ 70% módulos críticos · CI verde < 10 min · gates bloquean PR.
5. Latencia ingesta ≤ 500ms · time-to-anomaly < 10s · F1 ≥ 0.70 · health score r > 0.75.
6. Datos @: experimentos versionados (DVC/MLflow), EXP-001 reproducible.

## 7. Plan de acción inmediato

1. Publicar contratos (OpenAPI 3.1 + AsyncAPI 3.0) — **junio**.
2. Levantar stack PostgreSQL + SQLModel en VM (compose con servicio `db` + migraciones Alembic) — **junio/julio**.
3. Ejecutar las PPS 2026 según `roadmap/roadmap-mvp-pps.md` (Federico M-SEG, Romeo M-ML, Santiago M-QA).
4. Entrega MVP-0 en laboratorio GIDAS (oct 2026) → plan F1 2027.
5. Cerrar el ciclo de documentación por audiencia (interesados/negocio/desarrolladores) e integrar al README maestro.

## 8. Documentos relacionados

| Documento | Ruta |
|---|---|
| Marco conceptual (objetivo/análisis/diseño/especificaciones) | `marco/01-04` |
| Breve y respaldo institucional | `pid/resumen-pid.md` · `docs/brief-v2.md` |
| Análisis de PPS y acoplamiento | `equipo/analisis-pps-acoplamiento.md` |
| Decisiones | `docs/adr/0001*.md`, `docs/adr/0002*.md`, `decisiones/caso-postgresql-vs-sqlite.md` |
| Backlog y planificación | `backlog/backlog.md` |
| Roadmaps | `roadmap/roadmap-producto.md`, `roadmap/roadmap-mvp-pps.md` |
| Diagramas | `diagramas/*.png` |
| Docs por audiencia | `audiencias/` (ver siguiente sección) |

---

*Documento vivo — revisado en cada hito de fase y por pedido directo del coordinador.*