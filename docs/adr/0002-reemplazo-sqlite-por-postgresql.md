# ADR 0002: PostgreSQL como Almacenamiento del MVP (reemplazo de SQLite WAL)

- **Estado**: Aceptado
- **Fecha**: 2026-09-11
- **Autores**: Emanuel Rodriguez (Coordinación InfraIT)
- **Decisión relacionada**: Supersede **D-2026-04** (SQLite WAL migrable a TimescaleDB, brief-v2 §4.1). Análisis de caso completo en `gestionProyecto/decisiones/caso-postgresql-vs-sqlite.md`.

## Contexto

El MVP de IntellOps se diseñó originalmente (brief-v2 §4.1 / D-2026-04) con **SQLite (WAL) + índice temporal**,
migrable a TimescaleDB en una fase posterior. La justificación era la *ingeniería de recursos escasos*:
hardware legacy del laboratorio GIDAS (4-8GB RAM, 2-4 cores), sin destino dedicado para una base de datos.

**El contexto cambió**: la Coordinación dispone de una **VM dedicada Linux Rocky 10** con contenedores
**Docker/Podman** para el despliegue del MVP. Esto remueve la restricción que motivó SQLite ("no hay
PostgreSQL dedicado") y habilita reevaluar la decisión de almacenamiento con criterios de ingeniería.

La decisión de stack del MVP queda consolidada como:

| Capa | Tecnología |
|---|---|
| Frontend | **React + TypeScript** (Vite, static build, D3.js) |
| Backend | **FastAPI** (Python 3.11+) |
| ORM | **SQLModel** (SQLAlchemy + Pydantic, mismo autor que FastAPI) |
| Base de datos | **PostgreSQL** |
| Contenedores | **Docker / Podman** |
| Sistema operativo | **VM Linux Rocky 10** |

## Decisión

**Reemplazar SQLite (WAL) por PostgreSQL como almacenamiento del MVP**, con SQLModel como capa de acceso
a datos. La migración a **TimescaleDB queda definida como activación de extensión** (TimescaleDB **es**
PostgreSQL) cuando el volumen de datos lo requiera, sin migración de plataforma.

## Consecuencias

### Positivas

- **Migración futura eliminada**: TimescaleDB = extensión de PostgreSQL. "Migrar" pasa a ser `CREATE EXTENSION timescaledb` + crear hypertables, sin traslado de datos ni cambio de plataforma.
- **Ingesta concurrente real**: uvicorn multi-worker escribe en paralelo; PostgreSQL (MVCC) lo soporta de forma nativa, SQLite (1 escritor) no.
- **ORM de primera clase**: SQLModel unifica modelos Pydantic ↔ tablas y habilita Alembic para migraciones versionadas.
- **Multi-tenant sin dolor**: la tabla `APPLICATION` (DER V1.2) escala a schemas/RLS de PostgreSQL cuando se ofrezca observabilidad como servicio.
- **Narrativa de escalabilidad más honesta**: el paper pasa de "10K métricas/s (SQLite) → 100K (TimescaleDB)" a "PostgreSQL desde el día 1 → TimescaleDB sin reescritura".
- **Operación madura**: `pg_dump`/`pg_restore`, `EXPLAIN ANALYZE`, tuning documentado, ecosistema robusto.

### Negativas / Trade-offs

- **+200-500 MB RAM** en el stack: footprint total pasa de < 2 GB a ~2-3 GB.
- **Un servicio más que operar** (backup, upgrades, tuning).
- **El paper pierde el claim "SQLite en vez de base de datos dedicada"** — se reescribe el argumento: la innovación pasa a ser "observabilidad profesional completa en una sola VM con PostgreSQL tuneado y $0/mes" (ver caso de cambio §6).
- **Contradice una decisión aceptada (D-2026-04)** — gestionado por este ADR y la cadena de artefactos.

### Riesgos

- **RAM insuficiente en la VM**: mitigación = tuning conservador (`shared_buffers` 128MB, `work_mem` bajo, `max_connections` ajustado) + monitoreo Netdata.
- **Migración de datos si ya hubiera telemetría en SQLite**: en la práctica no hay datos productivos aún; la capa de repositorios (interfaz) debe mantenerse para el caso.
- **Complejidad de learning curve del equipo**: SQLModel/Alembic son nuevos para el equipo; mitigación = onboarding + ejemplos en repo.

## Alternativas Consideradas

### Alternativa 1: Mantener SQLite (WAL) en el MVP

- **Razón de descarte**: single-writer se convierte en cuello de botella con ingesta de 3 capas y multi-worker; la migración a TimescaleDB sigue pendiente; multi-tenant futuro más costoso. El único argumento a favor (footprint mínimo) perdió peso al existir VM dedicada.

### Alternativa 2: PostgreSQL + TimescaleDB desde el día 1

- **Descripción**: activar TimescaleDB ya en el MVP.
- **Razón de descarte**: agregar la extensión sin necesidad real de hypertables agrega complejidad sin beneficio al volumen esperado (< 1K métricas/s, ~500MB/año). PostgreSQL puro es suficiente; TimescaleDB se activa cuando la retención/compresión lo exija.

### Alternativa 3: PostgreSQL + SQLAlchemy (sin SQLModel)

- **Descripción**: ORM SQLAlchemy crudo.
- **Razón de descarte**: SQLModel aporta la integración Pydantic (validación OpenAPI nativa) que encaja con FastAPI y reduce boilerplate. SQLAlchemy queda disponible por debajo de SQLModel para casos avanzados.

## Referencias

- Análisis de caso completo: `gestionProyecto/decisiones/caso-postgresql-vs-sqlite.md`
- Decisión superseded: D-2026-04 (`gestionProyecto/marco/03-diseno.md` §5)
- Brief del proyecto: `docs/brief-v2.md` §4.1
- ADR de stack de señales: `docs/adr/0001-reemplazo-elk-por-grafana-loki-prometheus.md`
- [ADR Template](0000-template.md)

---

*Este ADR formaliza el cambio de almacenamiento aprobado por Coordinación. La cadena de artefactos
(marco, backlog, PPS, paper, roadmaps) se actualiza en consecuencia.*