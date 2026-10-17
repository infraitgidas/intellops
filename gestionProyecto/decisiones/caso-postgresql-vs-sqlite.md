# Caso de Cambio — SQLite (WAL) → PostgreSQL en el MVP de IntellOps

**Documento**: `decisiones/caso-postgresql-vs-sqlite.md`
**Fecha**: 2026-09-11
**Autor**: Coordinación InfraIT — Emanuel Rodríguez
**Tipo**: Análisis de caso de decisión técnica (precede al ADR-0002)
**Estado**: Aprobado para su implementación

---

## 1. Contexto y Motivación

El MVP de IntellOps estaba diseñado (brief-v2 §4.1, decisión **D-2026-04**) sobre **SQLite (WAL) con índice
temporal**, migrable a TimescaleDB en una fase posterior. La justificación original era la *ingeniería de
recursos escasos*: hardware legacy del laboratorio (4-8GB RAM, 2-4 cores) sin destino dedicado.

**El contexto cambió**: se dispone de una **VM dedicada Linux Rocky 10** (contenedores Docker/Podman) para
el despliegue del MVP. Esto remueve la restricción que motivó SQLite ("no hay PostgreSQL dedicado") y
habilita reevaluar la decisión de almacenamiento con criterios de ingeniería, no solo de escasez.

**Decisión propuesta**: stack del MVP = **React + TypeScript · FastAPI + SQLModel · PostgreSQL**,
contenedores **Docker/Podman** sobre **VM Rocky 10**.

---

## 2. Comparativa Técnica (contexto IntellOps)

| Criterio | SQLite (WAL) | PostgreSQL |
|---|---|---|
| Concurrencia de escritura | 1 escritor a la vez; `SQLITE_BUSY` con múltiples workers FastAPI (uvicorn `--workers N`) | Multi-writer real (MVCC), sin locks globales |
| Ingesta sostenida | Adecuada para < 1K métricas/s (threshold MVP), degrada > 10K | Muy superior; sobra para el threshold MVP y para picos |
| Consultas temporales | Índice temporal manual; planificador simple | Índices BRIN+time, particionamiento nativo, planificador robusto |
| Transaccionalidad | Liviana; ACID básico | ACID completo, `SELECT ... FOR UPDATE`, foreign keys reales |
| Migración futura | Requiere migrar a PostgreSQL/TimescaleDB (reescribir nada, pero mover datos y validar) | **Cero migración inicial**: TimescaleDB **es** una extensión de PostgreSQL |
| Operación | Un archivo, sin servicio | Un servicio más en el stack (contenedor), backup/restore dedicado (`pg_dump`) |
| Recursos | ~0 adicional (in-process) | ~200-500 MB total con tuning conservador (`shared_buffers` 128MB, `work_mem` bajo) |
| Footprint del sistema | < 2 GB RAM | ~2-3 GB RAM (una pieza más) |
| Multi-tenant futuro (tabla APPLICATION) | Funciona con esfuerzo; bloqueos al crecer | Primera clase: schemas, row-level security, roles por tenant |
| Madurez operativa | Embebida, sin tuning | Servicio maduro, `EXPLAIN ANALYZE`, vacuum, tuning conocido |
| Complejidad de desarrollo | Repositorio propio, SQL crudo | ORM real (SQLModel/SQLAlchemy), migraciones (Alembic) |

## 3. Ventajas del Cambio (argumentos a favor)

1. **Elimina la migración planificada.** TimescaleDB es una extensión de PostgreSQL. Arrancar en Postgres
   convierte "migración a TimescaleDB" en "activar extensión + crear hypertables" cuando el volumen lo
   exija. Es el mismo camino, sin el traslado de datos.

2. **Encaja con la ingesta concurrente.** El MVP de IntelOps recibe métricas de las 3 capas (RUM, producto,
   infra) con batching cada 30s y sampling. Con uvicorn multi-worker, múltiples workers escriben a la vez;
   PostgreSQL maneja esto de forma nativa, SQLite no.

3. **SQLModel es el ORM del ecosistema FastAPI** (mismo autor). Unifica modelos Pydantic ↔ tablas, reduce
   código, y da acceso a Alembic para migraciones versionadas. Con SQLite directo esto no existía.

4. **Multi-tenant sin dolor.** La tabla `APPLICATION` (DER V1.2) habilita entregar observabilidad como
   servicio. PostgreSQL tiene herramientas de primera clase (schemas, RLS) para el crecimiento
   organizacional descrito en el paper §6.2.3.

5. **Benchmark/paper más honesto.** El paper declara "escala máxima 10K (SQLite) → 100K (TimescaleDB)".
   Con PostgreSQL el punto de partida sube un orden de magnitud sin cambiar de plataforma; el relato
   "progresivo sin reescritura" gana credibilidad.

6. **Ecosistema operativo maduro.** `pg_dump`/`pg_restore`, PgBouncer (si algún día hace falta),
   replicación nativa, tooling de backup estudiado. En una VM dedicada, esto es valor operativo real
   frente al backup por copia de archivo.

## 4. Desventajas del Cambio (argumentos en contra — asumidos)

| Desventaja | Impacto | Mitigación |
|---|---|---|
| **+200-500 MB RAM** en el stack | Mayores recursos; footprint pasa de < 2 GB a ~2-3 GB | VM dedicada; tuning conservador (`shared_buffers` 128MB); monitorear con Netdata |
| **Un servicio más que operar** | Backup/restore, versionado, upgrades de Postgres | Contenedor inmutable + volumen; `pg_dump` diario a S3 free-tier (ya planificado con Rclone) |
| **El paper pierde el claim "SQLite en vez de BD dedicada"** | Se debilita el pilar de innovación por restricción del §4.2 | Reescribir el relato: la innovación pasa a ser "stack completo de observabilidad en una sola VM con PostgreSQL tuneado y $0/mes" — no menos válido, distinto (ver §6) |
| **Más piezas en Docker Compose** | Rebuild tarda un poco más; más superficie de configuración | Compose con servicio `db` estándar; healthchecks; documentación de onboarding |
| **Contradice D-2026-04 (Aceptada)** | Requiere gestionar el cambio de decisión en toda la cadena de artefactos | ADR-0002 que supersede D-2026-04 + actualización de marco/backlog/PPS/paper (este documento y sus consecuencias) |
| **"Recursos escasos" como tesis de marca** | El nicho "Bajo Recurso + Alta IA" del paper puede leerse menos extremo | La restricción sigue: 1 VM, ~2-3 GB, CPU-only, $0/mes. No es Datadog; sigue siendo el cuadrante "bajo recurso + alta IA" |

## 5. Criterios de Aceptación del Cambio (Definition of Done)

1. ✅ ADR-0002 creado en `docs/adr/` declarando PostgreSQL como almacenamiento del MVP y supersediendo D-2026-04.
2. ✅ Marco `03-diseno.md`: tabla de decisiones (D-2026-04 → Superseded; nueva decisión ADR-0002), contenedor buffer, diagrama de capas, módulo M-ING.
3. ✅ Marco `04-especificaciones.md`: RF-ING-03 a "PostgreSQL con SQLModel" + RF-ING-06 ajustado (migración a TimescaleDB como activación de extensión).
4. ✅ Marco `02-analisis.md`: riesgo R3 y stack revisados.
5. ✅ Backlog `T-020.3`: SQLite → PostgreSQL + repositorios SQLModel.
6. ✅ Análisis PPS `H-R1`: re-alineación a PostgreSQL (gira la recomendación previa).
7. ✅ Paper de divulgación editado (secciones 4.2, 4.3, 6.1, 6.2, 6.3, 7 y resumen si aplica).
8. ✅ Roadmaps actualizados (producto y MVP-PPS) con el nuevo stack.

## 6. Narrativa Técnica Actualizada para el Paper

> IntellOps opera un **stack completo de observabilidad en una única VM dedicada (Rocky 10) con
> PostgreSQL relacional** — en lugar de bases de datos dedicadas de escala enterprise — manteniendo un
> costo operativo de $0/mes y un footprint de ~2-3 GB RAM. La innovación no es "evitar una base de datos";
> es **demostrar que la observabilidad profesional (telemetría OTel + GLP + ML + LLM local) cabe en
> hardware modesto** con PostgreSQL fine-tuneado y un single-node containerizado, escalando luego de forma
> transparente a TimescaleDB con la misma plataforma.

## 7. Conclusión y Recomendación

**Recomendado**: adoptar PostgreSQL para el MVP. La VM dedicada remueve la restricción que justificaba
SQLite; PostgreSQL elimina la migración futura, soporta la ingesta concurrente del sistema, habilita
SQLModel/Alembic, y hace más honesto el relato de escalabilidad del paper. El costo (RAM adicional, un
servicio más) es asumible y mitigable. El cambio se gestiona formalmente vía ADR-0002 y la cadena de
artefactos de este caso.

---

*Este documento es el análisis de caso; la decisión formal se registra en `docs/adr/0002-reemplazo-sqlite-por-postgresql.md`.*