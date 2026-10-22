# ADR 0010: Arquitectura de 4 contenedores para el MVP (monolito modular desacoplado)

- **Estado**: Aceptado
- **Fecha**: 2026-08-12 (decisión del equipo)
- **Registrado**: 2026-10-20
- **Autores**: Equipo InfraIT GIDAS (Coordinación: Emanuel Rodriguez)
- **Decisión relacionada**: Minuta 12-08-2026 (`docs/meetings/13-08-2026.md` §2.1), Issue #19 (ISS-S1-03), PR #26 (C4 de 4 contenedores) y PR #31 (docker-compose multicontenedor).
- **Reemplaza**: El diseño aspiracional de 13 contenedores del stack LGTM completo (Prometheus, Loki, Grafana, Tempo, Alertmanager, Netdata, RAG, LLM Server standalone, etc.), que no refleja el MVP.

## Contexto

El repositorio convivía con tres descripciones arquitectónicas incompatibles:

1. La **spec OpenSpec de 13 contenedores**, con el stack LGTM completo (OTel Collector, Tempo, Loki, Prometheus, Grafana, Alertmanager, Netdata) más RAG/Chroma y un LLM Server standalone.
2. Un **C4 v1 desactualizado** (`docs/infrastructure/c4_container_v1.puml`) con backend, ML, frontend, notificaciones, DB y tres "servidores" genéricos.
3. La **decisión de agosto de 2026** (minuta 12-08): 4 contenedores + PostgreSQL 16.

El MVP tiene restricciones concretas: **menos de 2 GB de RAM**, CPU-only, costo operativo **$0/mes**, equipo de tres practicantes y despliegue en una **VM Linux Rocky 10** con Docker/Podman. El stack LGTM completo no entra en ese presupuesto y agrega operación que el equipo no puede sostener en la ventana de las PPS.

El riesgo técnico central es la asimetría de carga: la ingesta RUM debe ser liviana y estar siempre disponible, mientras que el motor de ML y la inferencia de un LLM local consumen CPU y RAM de forma intensiva y pueden provocar un **OOM Kill**. Si ambos dominios comparten proceso, un pico del motor analítico deja al sistema sin ingesta.

## Decisión

Se adopta un **monolito modular desacoplado en 4 contenedores** sobre `docker-compose`, con una única base de datos transaccional y límites de responsabilidad (CRUD) explícitos por contenedor:

| Contenedor | Tecnología | Responsabilidad | Límite de memoria |
|---|---|---|---|
| `intellops-core` | FastAPI + Uvicorn (Python 3.11) | Ingesta `/telemetry/*`, auth por API key, gestión multi-tenant, consulta y healthcheck. Único servicio con puerto publicado (`8000`) | 250 MB |
| `intellops-db` | PostgreSQL 16 (`postgres:16-alpine`) | Único almacén de estado (stateful): esquema completo, volumen `intellops-db-data` | Sin límite explícito |
| `intellops-ai-engine` | Python + scikit-learn + Llama 1B | Worker batch: lee `RUM_METRIC`, detecta anomalías y escribe `ANOMALY`/`ALERT` en estado Pending. Sin puertos | 1000 MB |
| `intellops-comms` | Python | Polling de `ALERT` Pending, despacho por Telegram/Email con retry + backoff, actualización a Sent/Failed. Sin puertos | 150 MB |

**Reglas de la decisión:**

- Los 4 contenedores comparten la red bridge `intellops-net`. Solo `intellops-core` publica puertos al host.
- `intellops-db` es el único punto de almacenamiento. El resto de los módulos declara únicamente los esquemas ORM de las tablas que le corresponden y no hace cross-imports.
- `intellops-core` implementa la cola de ingesta **en proceso** (`asyncio.Queue` + workers), sin broker externo, según ADR-0002.
- `intellops-db` usa **PostgreSQL 16** como fuente de verdad, según ADR-0009.
- **No son contenedores del MVP:** el agente RUM (JavaScript en el navegador del usuario final) y la SPA React (build estático servido aparte).
- **Fuera del compose del producto:** el pipeline GLP de seguridad (Promtail/Loki/Grafana, módulo M-SEG). Es infraestructura de seguridad separada; ADR-0001 sigue vigente para esa decisión.
- **Roadmap post-MVP:** OTel Collector, Tempo, Prometheus, Alertmanager, Netdata, RAG/Chroma y LLM Server standalone. Incorporarlos exige un ADR nuevo y una revisión del presupuesto de RAM.

La referencia normativa es `openspec/specs/architecture/containers.md` (v2.0); el diagrama vigente es `docs/infrastructure/Diagrama-C4-V2.puml`.

## Consecuencias

### Positivas

- **Aislamiento de fallos del motor analítico:** un OOM Kill del `ai-engine` reinicia solo ese contenedor; la ingesta de `intellops-core` sigue respondiendo.
- **Ingesta siempre disponible:** el core no compite por CPU/RAM con el LLM ni con el procesamiento batch.
- **Footprint acotado:** ~1.4 GB de límites + PostgreSQL, dentro del objetivo de < 2 GB y $0/mes.
- **Consistencia transaccional:** una sola base de datos evita sincronización entre almacenes y aprovecha MVCC/JSONB de PostgreSQL.
- **Superficie de ataque reducida:** solo el core expone puertos; DB, AI y comms son alcanzables únicamente dentro de `intellops-net`.
- **Ownership claro:** la matriz DER → contenedores asigna operaciones por tabla y evita deadlocks entre ingesta y análisis.
- **Operación simple:** `docker compose up` en una máquina limpia, sin orquestador ni broker.
- **Camino de evolución:** el compose puede reemplazarse por manifiestos de Kubernetes sin reescribir los módulos.

### Negativas / Trade-offs

- **PostgreSQL es un punto único de fallo:** requiere volumen persistente, backup (`pg_dump`) y prueba de restore.
- **Los 4 contenedores son un monolito modular, no microservicios independientes:** no escalan por separado y comparten el mismo host.
- **Sin cola durable:** los eventos en la cola en proceso se pierden ante un reinicio abrupto (limitación aceptada en ADR-0002).
- **Observabilidad limitada en el MVP:** healthchecks y contadores internos; sin trazas Tempo ni logs Loki del producto.
- **El motor de IA/LLM sigue siendo pesado:** 1000 MB puede ser ajustado según mediciones reales; el LLM se ejecuta en CPU y puede degradar la latencia del batch.
- **El compose de desarrollo monta el código fuente:** no es una configuración endurecida para producción.

### Riesgos

- **Presión de RAM:** medir con `docker stats` en M1; tuning conservador de PostgreSQL (`shared_buffers`, `work_mem`, `max_connections`) y revisión de límites por contenedor.
- **OOM Kill del AI engine:** esperado y contenido por `mem_limit`; el core no se ve afectado, pero se pierde el batch en curso.
- **Caída de PostgreSQL:** mitigación con volumen, backup diario a S3 free-tier y restore probado.
- **Fallas de Telegram/Email:** `intellops-comms` implementa retry con backoff exponencial y estados Sent/Failed.
- **Scope creep hacia LGTM:** agregar Prometheus/Loki/Grafana/Tempo al compose del producto rompería el presupuesto de RAM; cualquier incorporación requiere ADR y medición previa.

## Alternativas Consideradas

### Alternativa 1: Un solo contenedor (monolito tradicional)

- **Descripción**: core, ML, notificaciones y DB en un único proceso/imagen.
- **Razón de descarte**: un OOM del LLM o un pico de ML tumba también la ingesta; no cumple el objetivo de disponibilidad del core.

### Alternativa 2: Stack LGTM completo de 13 contenedores

- **Descripción**: OTel Collector, Tempo, Loki, Prometheus, Grafana, Alertmanager, Netdata, RAG/Chroma y LLM Server standalone, además del core y la DB.
- **Razón de descarte**: footprint estimado > 2.3 GB, complejidad operativa alta para tres practicantes y servicios que el MVP no necesita. Queda como roadmap post-MVP.

### Alternativa 3: Microservicios con broker externo (Redis/AMQP/Celery)

- **Descripción**: cola durable y workers independientes para ingesta, ML y notificaciones.
- **Razón de descarte**: agrega contenedor(es), RAM y operación; el MVP no justifica durabilidad ante reinicios. Se prefiere la cola en proceso de ADR-0002 y se deja la interfaz `IngestQueue` para migrar a un broker en el futuro.

### Alternativa 4: Contenedores separados para frontend y agente RUM

- **Descripción**: empaquetar la SPA React y el agente RUM como servicios del compose.
- **Razón de descarte**: la SPA es un build estático y el agente RUM se ejecuta en el navegador del usuario final; ninguno es un servicio stateful del backend. Se sirven fuera del compose.

### Alternativa 5: Mantener el C4 v1

- **Descripción**: conservar el diagrama con backend, ML, frontend, notificaciones, DB y tres servidores genéricos.
- **Razón de descarte**: no modela autenticación, multi-tenancy, ingesta asíncrona ni los límites de responsabilidad del MVP. Se marca como histórico y se reemplaza por `Diagrama-C4-V2.puml`.

## Recursos / Compatibilidad

- **Stack existente**: FastAPI + Uvicorn, PostgreSQL 16, SQLModel/Alembic, scikit-learn, llama.cpp (Llama 3.2 1B), Docker Compose sobre VM Rocky 10.
- **Recursos**: ~1400 MB de límites (core 250 + ai 1000 + comms 150) + PostgreSQL; CPU-only; sin broker ni orquestador.
- **Licencias**: proyecto Apache-2.0; PostgreSQL (PostgreSQL License), FastAPI (MIT), scikit-learn (BSD-3-Clause), llama.cpp (MIT). El stack LGTM (AGPL-3.0) queda fuera del MVP y debe revisarse en el SBOM si se incorpora.
- **Compatibilidad**: Docker/Podman; el compose usa `mem_limit` y healthchecks, por lo que no depende de Docker Swarm.

## Referencias

- Minuta de la decisión: `docs/meetings/13-08-2026.md` §2.1
- Spec canónica: `openspec/specs/architecture/containers.md` (v2.0)
- Diagrama C4 vigente: `docs/infrastructure/Diagrama-C4-V2.puml`
- Compose: `docker-compose.yml`
- Trazabilidad DER → contenedores: `docs/der/Trazabilidad DER a Contenedores.md`
- Justificación arquitectónica: `docs/infrastructure/Justificación Arquitectónica_ IntellOps MVP a SaaS.md`
- Diseño del marco: `gestionProyecto/marco/03-diseno.md` §2
- ADR-0001: `docs/adr/0001-reemplazo-elk-por-grafana-loki-prometheus.md` (pipeline GLP de seguridad)
- ADR-0002: `docs/adr/0002-pipeline-ingesta-async.md` (cola en proceso, sin broker)
- ADR-0009: `docs/adr/0009-postgresql-16-como-base-de-datos.md` (PostgreSQL 16)
- Issue #19 (ISS-S1-03) y PRs #26 y #31
- [ADR Template](0000-template.md)

---

*Este ADR formaliza una decisión ya implementada en el repositorio. No habilita por sí mismo la incorporación de nuevos contenedores: cualquier cambio en el número o los límites de los contenedores requiere un ADR nuevo.*
