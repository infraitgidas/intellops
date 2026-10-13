# RESEARCH — ISS-S3-04: Dataset operativo para ML

- **Contrato**: `gentle-ai.sdd-research/v1`
- **Revisión**: 1
- **Resultado**: `done`
- **Cambio**: ISS-S3-04 (GitHub #43 — "Dataset operativo para ML")
- **Base**: `feat/ISS-S3-04` sobre `origin/develop @ 1a46eb4`
- **Fecha de acceso a fuentes**: 2026-10-13
- **Almacén de artefactos**: openspec → `openspec/changes/ISS-S3-04/research.md`
- **Idioma**: español neutro técnico
- **Owners**: Federico (Dataset) + Romeo (ML)
- **Entradas fijas (no se re-abren)**: mecanismo = **E1** (pull HTTP del read path); alcance del dataset = **key por aplicación**; alcance funcional = **dataset + reader validado, sin entrenamiento**; consumo = **pull bajo demanda**.

---

## 0. Admisión y grants observados

| Clase | Grant declarado | Estado | Uso efectivo |
|---|---|---|---|
| `documentation` | `context7` | concedido | usado (Feast, OpenAPI Specification) |
| `open-web` | `websearch`, `webfetch` | concedido | `websearch` usado; `webfetch` disponible, no requerido |

- La admisión valida **solo** las clases declaradas y concedidas para este lane. No se infirió capacidad de evidencia a partir de Bash, MCP genérico, tools de persistencia ni nombres de archivo.
- No hubo denegaciones ni fallos de admisión. Todas las fuentes citadas pertenecen a `documentation` u `open-web`.
- **Resultado de admisión**: admitido.

---

## 1. Preguntas de investigación (RQ)

- **RQ1 — Desacoplamiento productor/consumidor.** ¿Qué patrón de integración corresponde a cada enfoque (E1 pull HTTP del read path, E2 export materializado, E3 lectura directa de DB) y bajo qué condiciones cada uno es apropiado (estabilidad del contrato, acoplamiento, autenticación, footprint)?
- **RQ2 — Identidad de una serie agregada.** Cuando la unidad de análisis es un bucket agregado `(application_id, metric_type_id, timestamp, value, session_count)` y no una fila cruda, ¿cómo debe la anomalía emitida referenciar su serie fuente: clave compuesta/series key, id sintético determinista, o FK nullable a una fila cruda?
- **RQ3 — Contrato-first y acceso multi-tenant.** ¿Cómo se define un contrato de dataset versionado entre servicios (OpenAPI/JSON Schema) y cómo se delimita el acceso al dataset (API key por aplicación vs credencial de servicio transversal)?
- **RQ4 — Estándares aplicables.** ¿Qué aportan OpenAPI 3.1, las convenciones semánticas de OpenTelemetry (métricas/excepciones) y las prácticas de contrato de dataset/feature store?

---

## 2. Fuentes

`class`: `documentation` = context7; `open-web` = websearch/webfetch. `accessed_at` = 2026-10-13.

| id | class | Título | Publisher | URL | Excerpt |
|---|---|---|---|---|---|
| S1 | open-web | Pattern: Database per service | microservices.io (Chris Richardson) | https://microservices.io/patterns/data/database-per-service.html | "Keep each microservice's persistent data private to that service and accessible only via its API. […] It cannot be accessed directly by other services." |
| S2 | open-web | Database-per-service pattern | AWS Prescriptive Guidance | https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/database-per-service.html | "individual data stores cannot be directly accessed by other microservices, and persistent data is accessed only by APIs." |
| S3 | open-web | Database per Service — What It Really Costs (and Why It's Worth It) | Yaroslav Kladko | https://yaroslavkladko.dev/database-per-service | "Each service has its own database. No other service reads or writes it directly. If service B needs data from service A, it asks A over an API or subscribes to A's events." |
| S4 | open-web | Why is it so bad to read data from a database "owned" by a different microservice | Software Engineering Stack Exchange | https://softwareengineering.stackexchange.com/questions/263735 | "What is more important and significant about a microservice: its API or its database schema? The API, because that is its contract… The rest of the world cares when the API changes." |
| S5 | open-web | Database Per Microservice — Coupling Tradeoffs | ADHDecode | https://adhdecode.com/databases/data-modeling-advanced-patterns/database-per-microservice-pattern/ | "The temptation to have OrderService directly query CustomerService's database is strong. Don't. […] This requires careful design. What data do you replicate? How often? How do you handle schema changes in the source data?" |
| S6 | open-web | Should one service access the data of another service directly | Stack Overflow | https://stackoverflow.com/questions/67349081 | "Directly reading from the DB doesn't make them independently deployable: it actually makes their deployment depend on each other, because changes to how one service wants to use the data will tend to require that the other be changed and redeployed." |
| S7 | open-web | Best practices for choosing a Time Series ID | Microsoft (Azure Time Series Insights) | https://docs.azure.cn/en-us/time-series-insights/how-to-select-tsid | "You can also select up to three key properties as your Time Series ID. Their combination will be a composite key that represents the Time Series ID." |
| S8 | open-web | Data Modeling: Part 2 — Method for Time Series Databases | InfluxData | https://www.influxdata.com/blog/data-modeling-part-2-method-time-series-databases/ | "the entity's primary key may be composite; in that case, the TSDB counterpart should preserve the identifying nature of the attribute." |
| S9 | open-web | Composite Keys | Chalk | https://docs.chalk.ai/docs/composite-keys | "Use the source system's stable identifier when one exists. Use a computed composite key only when the source system does not already provide a durable id." / "The expression must be deterministic and must produce exactly the same value everywhere the key is used." |
| S10 | open-web | SlipStream (referencia de formato de salida de anomalía) | GitHub (wesleyscholl) | https://github.com/wesleyscholl/SlipStream | Output: `{ "transaction_id": …, "is_anomaly": true, …, "original_transaction": { … }, "features_used": { … } }` — la anomalía conserva una referencia al registro fuente. |
| S11 | open-web | Generating Data Vault Hubs with complex Business Keys using standard SQL | Roelant Vos | https://roelantvos.com/blog/handling-complex-business-keys-using-standard-sql/ | Distingue **composición** (clave compuesta por varias columnas) de **concatenación** (derivar un valor único) al construir identificadores estables. |
| S12 | documentation | OpenAPI Specification v3.1.2 | OpenAPI Initiative | https://spec.openapis.org/oas/v3.1.html | "The OpenAPI Specification is versioned using a `major`.`minor`.`patch` versioning scheme." / `deprecated` (boolean): "Declares this operation to be deprecated. Consumers SHOULD refrain from usage." |
| S13 | open-web | Upgrading from OpenAPI 3.0 to 3.1 | Learn OpenAPI | https://learn.openapis.org/upgrading/v3.0-to-v3.1.html | "OpenAPI 3.1 achieves full compatibility with JSON Schema Draft 2020–12… Replace `nullable` with type arrays". |
| S14 | open-web | API Versioning & Deprecation | API Contract | https://www.api-contract.com/versioning-and-deprecation/ | "Additive changes — a new optional field, a new endpoint… — are safe. Removals, renames, tightened validation, changed defaults, and altered error codes are breaking and require a new major version." |
| S15 | open-web | API Versioning & Deprecation in OpenAPI | API Docs Hub | https://www.api-documentation-hub.com/openapi-asyncapi-schema-authoring/api-versioning-deprecation/ | "`Deprecation` (RFC 9745) says this endpoint is deprecated as of that instant. `Sunset` (RFC 8594) says when it stops working." |
| S16 | open-web | OpenAPI Breaking Changes: The Complete List of Rules | oasdiff | https://www.oasdiff.com/docs/breaking-changes | "Narrowing a request is breaking… Widening a response is breaking: the API can now return something clients were never written to handle." |
| S17 | documentation | Feast — Feature view | Feast (docs.feast.dev) | https://docs.feast.dev/master/getting-started/concepts/feature-view | "A feature view is an object representing a logical group of time-series feature data as it is found in a data source." |
| S18 | documentation | Feast — Feature retrieval | Feast (docs.feast.dev) | https://docs.feast.dev/master/getting-started/concepts/feature-retrieval | "Feature views contain the schema of data and a reference to where data can be found (through its data source). Datasets are the actual data manifestation of querying those data sources." |
| S19 | documentation | Feast — Offline store format spec | Feast (GitHub) | https://github.com/feast-dev/feast/blob/master/docs/specs/offline_store_format.md | "One or more Entity columns. Together they compose an Entity Key… One Entity timestamp column… One or more feature value columns." |
| S20 | documentation | Feast — SDK `feature_view.py` (versión/owner) | Feast (GitHub) | https://github.com/feast-dev/feast/blob/master/sdk/python/feast/feature_view.py | `FeatureView(..., version: str = "latest", owner: str, org: str, ttl, …)` — la definición de la serie es versionada y tiene owner explícito. |
| S21 | open-web | Multi-Tenant Application Security Cheat Sheet | OWASP | https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html | "Bind API credentials to explicit tenant sets, environments, and permission scopes. An intentionally cross-tenant service identity must be separately authorized and least privileged." |
| S22 | open-web | Multi-tenant SaaS authorization and API access control | AWS Prescriptive Guidance | https://docs.aws.amazon.com/pdfs/prescriptive-guidance/latest/saas-multitenant-api-access-authorization/saas-multitenant-api-access-authorization.pdf | "resource access is always provided on behalf of a given tenant. That is, users of Tenant A cannot view the data of Tenant B, even if that data is logically or physically collocated." |
| S23 | open-web | Tenant-Scoped API Keys: Secure Enrollment in Multi-Tenant Systems | VectraOps | https://www.vectraops.com/blogs/implement-tenant-scoped-api-keys-and-enrollment/ | "downstream services should not accept tenant context from user-provided fields (query parameters, body fields, path segments) unless that context is validated against the key's tenant binding." |
| S24 | open-web | API Key Scopes | Hopsworks | https://docs.hopsworks.ai/latest/user_guides/projects/api_key/api_key_scopes/ | "Every API key carries a set of scopes. A scope unlocks a group of REST endpoints; a request made with a key that lacks the scope an endpoint requires is rejected before it reaches the endpoint." |
| S25 | open-web | Metrics semantic conventions | OpenTelemetry | https://opentelemetry.io/docs/specs/semconv/general/metrics/ | "the same attribute values used to record an increment SHOULD be used to record any associated decrement, otherwise those increments and decrements will end up as different timeseries." |
| S26 | open-web | Semantic conventions for exceptions | OpenTelemetry | https://opentelemetry.io/docs/specs/semconv/exceptions/ | Convenciones de excepciones: `exception.type`, `exception.message`, `exception.escaped`, `exception.stacktrace`; "no longer recommended to record exceptions that are handled". |
| S27 | open-web | Semantic Conventions (overview) | OpenTelemetry | https://opentelemetry.io/docs/specs/semconv/ | "The Semantic Conventions define a common set of (semantic) attributes which provide meaning to data when collecting, producing and consuming it." |
| S28 | documentation | OpenAPI Specification (latest) — Versions & Deprecation | OpenAPI Initiative (vía context7) | https://spec.openapis.org/oas/latest.html | "Certain fields or features may be marked Deprecated… OpenAPI Description authors should use newer fields and features documented to replace the deprecated ones." |

### 2.1. Fuentes internas del proyecto (contexto vinculante)

| id | Ruta | Rol |
|---|---|---|
| P1 | `openspec/changes/ISS-S3-04/exploration.md` | Estado, E1/E2/E3, M1–M4, D1–D6, R1–R7 |
| P2 | `openspec/specs/architecture/containers.md` (§2.3, §5.1) | C4 declara `Rel(ai, db, "Read batch", "RUM_METRIC (read)")`; §5.1 prohíbe cross-imports core ↔ ai-engine |
| P3 | `docs/adr/0003-ownership-tenant-read-path.md` | Read path app-scoped; ML consume `/metrics/query`; "el read path devuelve el shape agregado sin `metric_id`" |
| P4 | `src/ml/schemas.py` | `MetricBatchInput.metric_id: UUID4` **requerido** |
| P5 | `src/api/domain/repositories/query_repository.py` | `MetricAggregate = (application_id, metric_type_id, timestamp, value, session_count)` |
| P6 | `src/ml/mock_data.json` | 2 registros con `metric_id` presente |
| P7 | `docs/architecture/IsolationForest/ContratoEntradaSalida.md` | Entrada requiere `metric_id`; ANOMALY persiste `metric_id` |
| P8 | `openspec/specs/database/ddl_v1.0.sql:258-277` | `anomaly.metric_id UUID NOT NULL` + `FK (metric_id) REFERENCES rum_metric(metric_id) ON DELETE RESTRICT` |
| P9 | `openspec/specs/openapi.yaml:1054-1070` | `MetricAggregate` required `[application_id, metric_type_id, timestamp, value, session_count]` (sin `metric_id`) |
| P10 | `docs/business/EDT intellops.md:1219-1251` | Mandato **contract-first** ("se definirá un contrato de dataset en S1–S3"); ejemplo con drift (`metric_type` por nombre, `error_count`) |

---

## 3. Hallazgos y claims validados

Cada claim mapea a IDs de fuente. Los claims son de evidencia externa; su aplicación al proyecto se separa en §5 y §7.

### 3.1. Desacoplamiento productor/consumidor (RQ1)

- **C1.** El patrón "database per service" establece que los datos persistentes de un servicio son privados y accesibles **solo por su API**; el esquema de la base es parte de la implementación del servicio (S1, S2, S3).
- **C2.** La consecuencia práctica de permitir lectura directa de la DB de otro servicio es **acoplamiento de despliegue y de esquema**: un cambio de esquema del dueño obliga a coordinar/redeployar al consumidor (S3, S4, S5, S6). Un cambio de API, en cambio, se gobierna por su contrato (S4).
- **C3.** El patrón admite **excepciones acotadas**: vistas de solo lectura o réplicas de datos "master" se usan legítimamente para **reporting o procesamiento batch** que necesita grandes volúmenes (S4), y los enfoques de réplica/materialización (eventos, CQRS, vistas materializadas) existen precisamente para casos de lectura intensiva (S3, S5). No son el camino por defecto y agregan estado/latencia de refresco.
- **C4.** La vía de menor acoplamiento y el contrato que el mundo externo observa es la **API**, no la tabla (S1, S3, S4). Cita representativa: "The API is the contract" (S4).

> **Correspondencia con el cambio**: E1 (pull HTTP del read path) = C1/C4 (consumo vía API pública). E2 (export materializado) = C3 (excepción para batch/reproducibilidad, con staleness y estado nuevo). E3 (lectura directa de `rum_metric`) = el antipatrón de C2 (acopla ML al esquema de almacenamiento y al interno de la ingesta).

### 3.2. Identidad de una serie agregada y anclaje de la anomalía (RQ2)

- **C5.** En almacenes de series temporales, la identidad de una serie es su **clave compuesta** (conjunto de propiedades clave), no una fila: "You can also select up to three key properties as your Time Series ID. Their combination will be a composite key" (S7); "the entity's primary key may be composite; in that case, the TSDB counterpart should preserve the identifying nature of the attribute" (S8).
- **C6.** La identidad de una timeseries queda definida por el **conjunto completo de atributos** con que se registra; si dos registros usan atributos distintos, "end up as different timeseries" (S25). Corolario: en un bucket agregado, los **parámetros de agregación** (p. ej. tamaño de bucket/ventana) forman parte de la identidad — el mismo `(app, type, timestamp)` con distinto `bucket_seconds` es otra serie.
- **C7.** Para construir una clave estable: "Use the source system's stable identifier when one exists. Use a computed composite key only when the source system does not already provide a durable id"; y la expresión de una clave compuesta "must be deterministic and must produce exactly the same value everywhere the key is used" (S9). Se distingue **composición** (columnas separadas) de **concatenación/derivación** a un único valor (S9, S11).
- **C8.** Es práctica común que el registro de anomalía **conserve una referencia a su origen** (p. ej. `transaction_id` + `original_transaction` + `features_used`) para trazabilidad y explicabilidad (S10).

> **Correspondencia con el cambio**: una serie agregada (P5) no tiene una fila física con `metric_id`; su identidad natural es la **clave compuesta del bucket** (C5, C6). Derivar un id sintético es válido **solo** si el origen carece de un id durable (C7) — pero aquí el problema no es "falta de id", sino que **el id existente (`rum_metric.metric_id`) no representa la unidad agregada**.

### 3.3. Contrato-first y versionado de contrato (RQ3)

- **C9.** OpenAPI 3.1 es un dialecto de JSON Schema Draft 2020-12: los mismos esquemas del contrato pueden alimentar validación runtime, generación de código y mocks; `nullable` se reemplaza por arrays de tipo (S12, S13).
- **C10.** `info.version` es la **versión de la API** (semver) y debe cambiar con cada edición publicada del documento; difiere de la versión de la especificación OAS (S12, S14).
- **C11.** Una definición limpia de "cambio breaking": aditivo (campo opcional nuevo, endpoint nuevo) es seguro; remoción, renombre, validación más estricta, defaults cambiados o semántica de errores alterada son breaking y requieren major (S14, S16).
- **C12.** La deprecación debe ser **observable en banda** y gobernada: `deprecated: true` en la operación (S12, S28) más encabezados `Deprecation` (RFC 9745) y `Sunset` (RFC 8594), y un gate de CI que impida retirar sin notice (S14, S15, S16).
- **C13.** La práctica de feature store modela la **definición** de la serie por separado de la **materialización** de datos: la `FeatureView` "contain[s] the schema of data and a reference to where data can be found"; el dataset "are the actual data manifestation of querying those data sources" (S17, S18).
- **C14.** El contrato de la serie/feature es **versionado y con owner explícito** (`version`, `owner`, `org`), y la identidad de fila se compone de columnas de entidad + una columna de timestamp de evento (S19, S20).

> **Correspondencia con el cambio**: el "contrato de dataset operativo" que promete el EDT (P10) debe ser el contrato **de la serie agregada** (schema + referencia a la fuente), versionado en `info.version`, con `deprecated`/`Sunset` para evolucionar, y no un contrato sobre la tabla física (C13, C14).

### 3.4. Acceso multi-tenant al dataset (RQ3)

- **C15.** Las credenciales deben estar **atadas a conjuntos explícitos de tenants y scopes**; una identidad intencionalmente cross-tenant "must be separately authorized and least privileged" (S21, S24).
- **C16.** El contexto de tenant debe derivarse **del servidor** (de la credencial) y **nunca** de campos provistos por el cliente (query/body/path) salvo como verificación de consistencia (S23, S22).
- **C17.** Una API key **global** compartida entre tenants crea "unacceptable blast radius: any leak becomes a cross-tenant incident"; la key tenant-scoped da un límite duro (S23).
- **C18.** Los scopes no otorgan más de lo que la identidad puede hacer; el endpoint rechaza antes de ejecutar si falta el scope (S24).

> **Correspondencia con el cambio**: la confirmación "key por aplicación" (entrada fija) coincide con C15/C16/C17; el read path ya deriva el tenant exclusivamente de la key (P3, P9). El riesgo residual es un dataset **multi-app** (R4): requeriría N keys o una credencial de servicio explícitamente cross-tenant (C15).

### 3.5. Estándares aplicables (RQ4)

- **C19.** OpenTelemetry aporta convenciones de atributos semánticos estables para métricas y excepciones; su adopción busca "a common naming scheme that can be standardized across a codebase, libraries, and platforms" (S25, S26, S27). Para excepciones, los atributos núcleo son `exception.type`, `exception.message`, `exception.escaped`, `exception.stacktrace` (S26).
- **C20.** OpenAPI 3.1 cubre versionado (`major.minor.patch`), `deprecated`, y `operationId` estable como identificador de operación para SDKs (S12, S28). Renombrar `operationId` es breaking para clientes generados (S14).

> **Correspondencia con el cambio**: el proyecto ya usa OpenAPI 3.1 (P9, `operationId`s `queryMetrics`/`listMetrics`); no hay que migrar de versión. Las semconv de OTel son una **referencia de nomenclatura** para los atributos del dataset (no obligan a instrumentar OTel en el MVP).

---

## 4. Contradicciones, incertidumbre y frescura

### 4.1. Contradicciones entre fuentes externas

- **Bench (direct-read) vs best practice (API-only).** S4/S6 documentan una postura pragmática ("reading data from a database owned by a different service is not bad"; la VIEW es un contrato válido) frente a la postura dominante S1/S2/S3 ("the schema is part of the implementation; access only via API"). No es una contradicción factual: S4/S6 admiten el acceso directo **solo** como excepción acotada (reporting/batch), condición que no aplica al caso "evitar acoplamiento a la ingesta" del issue #43.
- **Snapshot vs pull.** S3/S5 recomiendan réplica/materialización para lecturas intensivas; S4-S6 advierten que introducen estado nuevo, staleness y duplicación de la lógica de scoping. La evidencia no permite resolver "cuál es mejor" en abstracto: depende del requisito (reproducibilidad/EDA vs frescura/latencia).
- **Id sintético vs clave compuesta.** S9 admite ambos, con una regla de precedencia clara: preferir el **id estable del origen**; derivar un **composite/computed key** solo cuando no existe un id durable. La tensión aparece porque en este proyecto **sí existe** un id (`metric_id`) pero corresponde a una fila cruda, no a la unidad agregada.

### 4.2. Incertidumbre

- No se halló una convención de la industria específica para "anclar una anomalía a un bucket agregado". S7/S8/S9 son evidencia sólida para el **principio** (la identidad de una serie es su clave compuesta), pero la materialización exacta (¿clave compuesta en ANOMALY? ¿tabla de series?) es una decisión de diseño, no un estándar publicado.
- S7 proviene del espejo `docs.azure.cn` del mismo documento de Microsoft (contenido equivalente al de `learn.microsoft.com`). Se cita la URL accedida.

### 4.3. Frescura

- OpenAPI 3.1 (S12/S28): especificación estable y vigente; el proyecto ya está en 3.1 (P9).
- Feast (S17–S20): documentación de un proyecto activo; sus conceptos (feature view/dataset versionado) son estables, aunque los detalles de API cambian entre releases.
- El resto de S1–S6, S21–S24: material de arquitectura/seguridad de vigencia amplia; las versiones puntuales no condicionan los claims.

---

## 5. Aplicación a las decisiones del cambio

### (a) Mecanismo de desacoplamiento

La entrada fija ya fijó **E1**. La evidencia la respalda y permite acotar E2/E3:

| Enfoque | Evidencia aplicable | Veredicto según evidencia externa |
|---|---|---|
| **E1 — Pull HTTP del read path** | C1, C4, C16 (API-como-contrato; tenant derivado de la key) | Alineado: es el consumo vía API pública; reutiliza auth/agregación/scoping de S3-01; footprint ~0; respeta §5.1 de P2 |
| **E3 — Lectura directa de `RUM_METRIC`** | C2, C3 (acoplamiento de esquema; excepción solo para batch) | Contradice C2 para el propósito declarado ("no acoplar a la implementación interna de la ingesta", issue #43); duplica el scoping multi-tenant ya resuelto (P3) |
| **E2 — Export materializado** | C3 (válido para batch/reproducibilidad), con staleness + estado nuevo | Legítimo como **follow-up** de reproducibilidad/EDA; no para el MVP de E1 (agrega productor/estado y no resuelve `metric_id`) |

### (b) Identidad de la serie agregada / `metric_id` (M1–M4)

Hecho vinculante a tener presente: `anomaly.metric_id` es `UUID NOT NULL` con **FK a `rum_metric.metric_id`** (P8), y `MetricBatchInput.metric_id` es requerido (P4). Una fila agregada (P5) **no** tiene una fila `rum_metric` asociada. Por lo tanto, **ninguna** de las opciones conserva simultáneamente (i) el anclaje a la serie agregada y (ii) la FK física actual **sin** tocar contrato/DDL. La elección es sobre **qué** se relaja.

| Opción | Descripción | Pros (evidencia) | Contras / footprint / acoplamiento / contrato-migración |
|---|---|---|---|
| **M1** — `metric_id` opcional (nullable) | Relajar `MetricBatchInput.metric_id` a `UUID4 \| None`; el bucket no lo trae | Mínimo cambio en el shape de salida del read path (ya no tiene `metric_id`, P9). El consumidor no inventa ids (C7: no derivar si no hace falta) | `anomaly.metric_id NOT NULL` + FK (P8) se rompe: **DDL + cambio de contrato ML** (P4/P7). La anomalía queda sin anclaje físico → hay que re-anclar a la clave del bucket (deriva a M4). Breaking para el contrato ML (C11) |
| **M2** — `uuid5` determinista | `uuid5(namespace, app+type+bucket)` por fila agregada | No cambia `MetricBatchInput` (P4). Determinista y reproducible (C7, C9). Permite calcular el mismo id en ambos lados | El uuid5 **no existe** en `rum_metric` → la FK de P8 falla (violación) o hay que **eliminar/redefinir la FK** (DDL). Además el bucket varía con `bucket_seconds` (C6): la clave debe incluir los parámetros de agregación, y el lector debe conocerlos |
| **M3** — Exponer filas crudas (con `metric_id`) | Nuevo endpoint/vista de `rum_metric` sin agregar | Preserva `metric_id` real y la FK de ANOMALY (P8). Aceptable para **batch/reporting** (C3) | **Scope nuevo** (S3-01 entregó solo agregados); materializa filas hacia el proceso ML (footprint, C3); reintroduce acoplamiento a la forma cruda (C2) |
| **M4** — Anclar la anomalía al bucket | Identidad = `(application_id, metric_type_id, timestamp, [parámetros de agregación])`; quitar `metric_id` del input ML | Conceptualmente el más limpio para datos agregados (C5, C6, C7): la anomalía referencia la **serie**, no una fila. Es la identidad "natural" del shape P5 y soporta trazabilidad (C8) | **Cambio de contrato de entrada ML + de la entidad ANOMALY + DDL** (P4, P7, P8). Breaking (C11). Requiere definir si la clave va a ANOMALY (columnas) o a una tabla `metric_series` |

**Lectura de la evidencia**: C5–C7 favorecen que la identidad de la serie agregada sea una **clave compuesta** (C7 prefiere id estable del origen; aquí el "origen" de la *serie* es el bucket, no la fila). Esto empuja conceptualmente hacia **M4** o, como mínimo, hacia **M2 + un reemplazo explícito de la FK** por una referencia de serie. M3 es el único que preserva la FK sin DDL, pero es scope nuevo y acopla. **M1 no resuelve por sí solo el anclaje**: al nulear el FK obliga a re-anclar (→ M4).

### (c) Acceso multi-tenant al dataset

- La entrada fija (**key por aplicación**) es coherente con C15–C18 y con el read path existente (P3, P9): el tenant se deriva de la key; no hay parámetro de app en el request.
- **Dataset multi-app** (R4): C15/C17 exigen que una identidad cross-tenant sea **explícitamente autorizada y least-privileged**, no que se ensanche la key por app. Si el consumo futuro necesita todas las apps, la vía respaldada es una **credencial de servicio dedicada y auditada** (o N keys), nunca reutilizar una key por app.
- C24: conviene que la credencial del dataset tenga **scope de solo lectura** explícito y que el endpoint rechace antes de ejecutar si falta.

---

## 6. Conflictos entre evidencia externa y los contratos propios del proyecto

1. **`containers.md` (E3, DB-directa) vs ADR-0003 (E1) vs evidencia (C1/C2/C4).** El C4/§2.3 de P2 (`Rel(ai, db, "Read batch", "RUM_METRIC (read)")`) refleja el patrón de lectura directa; ADR-0003 (P3) y la entrada fija (E1) van por API. **Qué debe ganar**: la evidencia externa (C1–C4) respalda E1 para el objetivo de desacoplamiento; el proyecto ya decidió E1, pero **`containers.md` queda en contradicción** y debe reconciliarse por ADR. La evidencia no "pisa" el contrato: señala que P2 está desalineado y requiere corrección explícita (RI R1).
2. **`anomaly.metric_id NOT NULL FK → rum_metric` (P8) y `MetricBatchInput.metric_id` requerido (P4) vs identidad de serie agregada (C5–C7).** La evidencia dice que la identidad de una serie es su clave compuesta, no una fila; el contrato del proyecto exige un UUID de fila. **Qué debe ganar**: mientras el DDL no cambie, **el contrato del proyecto gana** (es vinculante y no se puede violar un FK en runtime). La resolución es una **migración de contrato/DDL** deliberada (M1/M2/M4), no una reinterpretación silenciosa. La evidencia informa **cuál** migración es más limpia (M4), pero la decisión es de Federico + Romeo + DB.
3. **`MetricAggregate` sin `metric_id` (P9) vs `MetricBatchInput` con `metric_id` requerido (P4).** Es el desajuste que ADR-0003 ya reconoce (P3). La evidencia no lo resuelve; lo encuadra como **cambio breaking del contrato ML** (C11) que debe documentarse/versionarse (C12, C13).
4. **Ejemplo del EDT (P10: `metric_type` por nombre, `error_count`) vs schemas reales (P4/P5/P9).** Drift documental. Debe corregirse para que el contrato de dataset sea único (C13, C14).
5. **`containers.md` §5.1 (no cross-import) vs cualquier módulo compartido.** La evidencia (C1) es consistente con un límite fuerte entre servicios; no hay conflicto: descarta importar `MetricAggregate` desde `src/ml`.

---

## 7. Recomendaciones respaldadas y elecciones de producto (separadas)

> Las **recomendaciones** son conclusiones trazables a las fuentes (§2/§3). Las **decisiones de producto** pertenecen a Federico + Romeo y **no** son autoritativas en este artefacto.

### 7.1. Recomendaciones respaldadas por evidencia

- **R1 (E1).** Exponer el dataset **como el contrato de la serie agregada**, no como la tabla: el shape público es `MetricAggregate` (P5, P9). La tabla `rum_metric` y su esquema son implementación (C1, C4). *(respaldada, alineada con la entrada fija)*
- **R2 (contrato).** Formalizar el "contrato de dataset operativo" como documento + referencia OpenAPI 3.1, **versionado** (`info.version`, semver) y con evolución por `deprecated`/`Sunset` si cambia (C10, C12, C13, C14). Corregir el drift del EDT (P10).
- **R3 (identidad).** Tratar la **clave del bucket** `(application_id, metric_type_id, timestamp)` como la identidad de la serie, e **incluir los parámetros de agregación** (p. ej. `bucket_seconds`) en esa identidad, porque un mismo `(app, type, timestamp)` con otro bucket es otra serie (C5, C6).
- **R4 (`metric_id`).** Si la anomalía debe seguir anclándose a la **serie** (no a una fila), la opción conceptualmente más limpia es **M4** (clave de serie); si se necesita mantener el shape de entrada ML, **M2 con una FK/referencia de serie explícita** es viable **solo** si se resuelve la FK de P8 por migración. **M1 sola no alcanza** (deriva a M4); **M3** es la única que preserva la FK sin migración pero es scope nuevo y acopla (C2, C3, C5–C7). *(respaldada como análisis; la elección es de producto)*
- **R5 (multi-tenant).** Mantener **key por aplicación**; derivar el tenant del servidor (key), nunca del cliente (C16). Cualquier dataset multi-app debe usar una **credencial de servicio cross-tenant explícita y least-privileged**, no ensanchar la key (C15, C17).
- **R6 (estándares).** No migrar de OpenAPI (ya 3.1). Usar semconv de OTel solo como referencia de **nomenclatura de atributos** del dataset (C19); no obliga a instrumentar OTel en el MVP.

### 7.2. Elecciones de producto pendientes (no autoritativas aquí)

Coinciden con D1–D6 de la exploración (P1). Las que la evidencia informa directamente:

- **D2 (M1/M2/M3/M4)** — decisión de contrato ML (`MetricBatchInput`) + entidad ANOMALY + posible DDL. Toca el dominio de Romeo. **Bloqueante** para el mapeo.
- **D3 (alcance del dataset)** — un tenant por key vs credencial de servicio para todas las apps.
- **D6 (cadencia/ventana)** — impacta la identidad de la serie (R3: incluir `bucket_seconds`).
- **D1 (reconciliación `containers.md` ↔ ADR-0003)** — requiere ADR aunque E1 esté fijado (R1).

---

## 8. Riesgos y vacíos

- **V1 (frescura/normalización).** Este lane asume que el dataset consume valores canónicos almacenados y que ISS-S3-02 (no implementada al momento de la exploración) no es dependencia. Si la normalización cambia `value`, el contrato de dataset debe versionarse (C10, C13).
- **V2 (identidad y bucket).** Si el lector ML no conoce los parámetros de agregación (`bucket_seconds`), una clave derivada (M2/M4) puede ser **inconsistente entre productor y consumidor** — C7 exige "exactly the same value everywhere".
- **V3 (FK).** Cualquier opción que no sea M3 exige tocar la FK de P8; sin migración explícita, el insert de ANOMALY falla en runtime. Es el principal riesgo técnico de M1/M2/M4.
- **V4 (multi-app).** Un dataset global con key por app fuerza N keys o una credencial cross-tenant; la evidencia exige autorización explícita y least-privilege (C15, C17).
- **V5 (drift documental).** Mientras `containers.md` (E3), el EDT (P10) y el contrato de dataset no se reconcilien, persisten tres "fuentes de verdad" contradictorias.
- **Vacío declarado.** No existe un estándar publicado para el anclaje de anomalías a buckets agregados; §5(b) es evidencia-aplicada, no una convención normativa.

---

## 9. Próximo paso sugerido

La evidencia soporta la entrada fija (E1, key por app) y delimita la decisión abierta de `metric_id` (M1–M4) con sus implicancias de contrato/DDL. El siguiente paso **no** es `sdd-propose` hasta que Federico + Romeo confirmen **D2** (y, en lo posible, D1/D3/D6), dado que M2/M4 tocan el contrato ML y la FK de ANOMALY.
