# RESEARCH — ISS-S3-02: Normalización y calidad de datos

**Artefacto**: `gentle-ai.sdd-research/v1`
**Cambio**: ISS-S3-02 (GitHub #41). **Base**: `feat/ISS-S3-02` off `origin/develop` @ `1a46eb4`.
**Fase**: sdd-research. **Rama**: `feat/ISS-S3-02`.
**Store**: openspec (repo-local). **Idioma**: español neutro técnico.
**Revision**: `r1`. **Outcome**: `done`. **Fecha**: 2026-10-13.

Línea seleccionada: **Semántica de normalización para la ingesta de telemetría RUM del navegador** — canonicalizar (solo representación) antes de la validación: timestamps, unidades, nombres y valores ausentes/inválidos.

---

## 1. Admisión y grants observados (r1)

Declaración de capacidad recibida del runtime (`gentle-ai.sdd-research-capability/v1`):

| Clase | Grant declarado | Herramientas declaradas |
|---|---|---|
| `open-web` | granted | `websearch`, `webfetch` |
| `documentation` | granted | `context7_resolve-library-id` + `context7_query-docs` (MCP Context7) |

Grants observados en el runtime de ejecución (ambas clases ejercitadas con llamadas reales **antes** de registrar cualquier claim):

| Clase | Grant observado | Verificación |
|---|---|---|
| `open-web` | **DISPONIBLE** | `websearch` (7 consultas exitosas) y `webfetch` (3 fetches exitosos: RFC 3339, web.dev FCP, MDN Error). Dos consultas fueron limitadas por rate limit (HTTP 429) y se reintentaron con éxito. |
| `documentation` | **DISPONIBLE** | `context7_resolve-library-id` (resolvió `/websites/opentelemetry_io`) y `context7_query-docs` (guía de unidades de instrumentos OTel, fallback de `error.type`, unidad `s` de `http.server.request.duration`). |

Las herramientas de persistencia (`engram`) **no** son un grant de evidencia y no se usaron como fuente.

**Resultado de admisión: ACEPTADA.** Ambas clases solicitadas están activas; los claims de abajo mapean a source IDs validados.

---

## 2. Preguntas de investigación (RQ)

- **RQ1 — Canonicalización de timestamps.** ¿Cuál es la representación canónica UTC/ISO 8601, es obligatoria una zona horaria explícita, y cómo deberían tratarse el clock skew / timestamps futuros (o reenviados) sin destruir la señal de anomalía?
- **RQ2 — Conversión de alias de unidad → canónica.** Para las 5 métricas RUM (`TTFB`, `FCP`, `XHR_LATENCY`, `JS_EXCEPTION_RATE`, `RAGE_CLICK`), ¿qué conjuntos de alias se aceptan convencionalmente (`s`→`ms`, `sec`, `msec`, …), y por qué convertir alias conocidos a la unidad canónica en lugar de rechazarlos?
- **RQ3 — Canonicalización de nombres.** ¿Cómo deberían canonicalizarse los nombres de tipo de métrica y los valores de `error_type` de JS, y cuáles son los catálogos convencionales (tipos de error JS, atributos exception/error-type)?
- **RQ4 — Política de valores ausentes / inválidos.** ¿Qué reparaciones son de solo representación (seguras) frente a cambios de magnitud (prohibidos), y es correcto rechazar o reparar valores ausentes/inválidos?

---

## 3. Sources

| id | class | title | publisher | URL | accessed_at | excerpt |
|---|---|---|---|---|---|---|
| S1 | open-web | Navigation Timing Level 2 | W3C | https://www.w3.org/TR/navigation-timing-2/ | 2026-10-13 | "A lo largo de este trabajo, todos los valores de tiempo se miden en milisegundos…"; `responseStart` = momento inmediatamente después de que el UA recibe el primer byte de la respuesta. |
| S2 | open-web | Navigation and resource timings | MDN Web Docs | https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Navigation_and_resource_timings | 2026-10-13 | Tiempos de solo lectura en milisegundos; TTFB = `responseStart - navigationStart`; response time = `responseStart - requestStart`. |
| S3 | open-web | Paint Timing | W3C | https://www.w3.org/TR/paint-timing/ | 2026-10-13 | Valores de nombre de `PerformancePaintTiming` `"first-paint"` / `"first-contentful-paint"`; `startTime` es un `DOMHighResTimeStamp`; el tiempo de presentación se engrosa al siguiente múltiplo de 4 ms. |
| S4 | open-web | PerformancePaintTiming | MDN Web Docs | https://developer.mozilla.org/en-US/docs/Web/API/PerformancePaintTiming | 2026-10-13 | FCP = momento en que se renderiza el primer contenido de texto/imagen del DOM; `startTime` se devuelve en milisegundos. |
| S5 | open-web | First Contentful Paint (FCP) | Google (web.dev) | https://web.dev/articles/fcp | 2026-10-13 | FCP = tiempo desde la navegación hasta el primer render de contenido; bueno ≤1.8 s, pobre >3.0 s (calificación/referencia, no una cota de rechazo); FCP incluye TTFB. |
| S6 | open-web | Metrics semantic conventions (general — instrument units) | OpenTelemetry | https://opentelemetry.io/docs/specs/semconv/general/metrics/ | 2026-10-13 | "Las unidades deben seguir UCUM"; "Cuando los instrumentos miden duraciones, DEBERÍAN usarse segundos (es decir, `s`)"; los conteos enteros usan anotaciones entre llaves (`{request}`, `{error}`); los nombres de métricas NO DEBERÍAN incluir unidades. |
| S7 | open-web | Semantic conventions for HTTP metrics | OpenTelemetry | https://opentelemetry.io/docs/specs/semconv/http/http-metrics/ | 2026-10-13 | Unidad de `http.server.request.duration` / `http.client.request.duration` = `s`; `error.type` DEBERÍA ser predecible y de baja cardinalidad. |
| S8 | open-web | Semantic Conventions: default to seconds for duration units (issue #2977) | OpenTelemetry (GitHub) | https://github.com/open-telemetry/opentelemetry-specification/issues/2977 | 2026-10-13 | Prometheus/OpenMetrics "recomiendan fuertemente" segundos para duraciones; el TC votó "5 de 9 … por segundos (`s` en UCUM c/s) como la unidad recomendada para duración"; OTel movió `ms`→`s`. |
| S9 | open-web | HTTP semantic conventions declared stable | OpenTelemetry | https://opentelemetry.io/blog/2023/http-conventions-declared-stable/ | 2026-10-13 | Cambio de unidad de `http.server.duration` `ms` → `s`; estandarización en segundos para unidades de métricas; nuevo atributo `error.type`. |
| S10 | open-web | Semantic conventions for exceptions in logs | OpenTelemetry | https://opentelemetry.io/docs/specs/semconv/exceptions/exceptions-logs/ | 2026-10-13 | `exception.type` = "el tipo de la excepción (su nombre de clase totalmente calificado, si aplica)"; se prefiere el tipo dinámico sobre el estático. |
| S11 | open-web | Error — registry attribute `error.type` | OpenTelemetry | https://opentelemetry.io/docs/specs/semconv/registry/attributes/error/ | 2026-10-13 | `error.type` DEBERÍA ser predecible y de baja cardinalidad; "debería usarse su nombre de clase canónico que identifica el tipo …"; el fallback conocido `_OTHER` DEBE usarse si aplica. |
| S12 | open-web | Error (JavaScript standard built-in objects) | MDN Web Docs | https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error | 2026-10-13 | Tipos de error built-in: `Error` (base), `EvalError`, `RangeError`, `ReferenceError`, `SyntaxError`, `TypeError`, `URIError`, `AggregateError`, `InternalError`. |
| S13 | open-web | RFC 3339 — Date and Time on the Internet: Timestamps | IETF | https://datatracker.ietf.org/doc/html/rfc3339 | 2026-10-13 | Perfil de ISO 8601; `date-time = full-date "T" full-time`; `time-offset = "Z" / time-numoffset`; "la hora local no calificada … se considera inaceptable"; los offsets numéricos son obligatorios. |
| S14 | open-web | storage/remote/write_handler.go | Prometheus (GitHub) | https://github.com/prometheus/prometheus/blob/0279e14d/storage/remote/write_handler.go | 2026-10-13 | `if t > app.maxTime { return … "timestamp is too far in the future" (storage.ErrOutOfBounds) }`; el remote-write rechaza muestras futuras con HTTP 400. |
| S15 | open-web | remote write handler: reject samples with future timestamps (PR #14304) | Prometheus (GitHub) | https://github.com/prometheus/prometheus/pull/14304 | 2026-10-13 | El scrape path permite una "diferencia de 10 minutos"; NTP advierte a 0.5 s / crítico a 1 s; OIDC usa 30 s de clock skew; se fijó +10 minutos para tolerar la deriva emisor/receptor. |
| S16 | open-web | Prometheus Remote Write spec | Prometheus (docs) | https://github.com/prometheus/docs/blob/main/docs/specs/prw/remote_write_spec.md | 2026-10-13 | "Los timestamps DEBEN ser int64 contados como milisegundos desde la epoch Unix" — millis de epoch absolutos, distintos de las duraciones W3C desde el time origin. |
| S17 | open-web | Fingerprint Rules (Event Grouping) | Sentry | https://docs.sentry.io/concepts/data-management/event-grouping/fingerprint-rules/ | 2026-10-13 | `error.type:ConnectionError -> system-down` mapea tipos de excepción a grupos; matchea por nombre de excepción; `{{ error.type }}` fuerza un grupo por tipo de error; el agrupamiento por defecto usa stack trace, tipo de excepción y mensaje. |
| S18 | documentation | OpenTelemetry documentation (instrument units; `error.type`; HTTP duration) | OpenTelemetry (via Context7 `/websites/opentelemetry_io`) | https://opentelemetry.io/docs/specs/semconv/ | 2026-10-13 | "Unit" de `http.server.request.duration`: `s`; "unit" del legacy `http.server.duration`: `ms`; `_OTHER` "Un valor de error de fallback para usar cuando la instrumentación no define un valor personalizado." |
| S19 | open-web | Format registry: `date-time` | OpenAPI Initiative | https://spec.openapis.org/registry/format/date-time | 2026-10-13 | "El formato `date-time` representa una fecha y hora según lo definido por date-time - RFC3339"; tipo de dato JSON `string`. |
| S20 | open-web | Data Types (OpenAPI 3.0) | Swagger / OpenAPI Initiative | https://swagger.io/docs/specification/v3_0/data-models/data-types/ | 2026-10-13 | `date-time` = notación date-time según RFC 3339 §5.6, p. ej. `2017-07-21T17:32:28Z`; `format` es una pista, no una coerción. |
| S21 | open-web | Type coercion rules | Ajv JSON Schema Validator | https://ajv.js.org/coercion.html | 2026-10-13 | La coerción está **deshabilitada por defecto** (`coerceTypes` es `false`); cuando se habilita, string→number usa `+data` (solo para strings numéricos válidos). |
| S22 | open-web | Type-specific keywords / Numeric types | JSON Schema (json-schema.org) | https://json-schema.org/understanding-json-schema/reference/type | 2026-10-13 | `type` restringe el primitivo JSON; `number` incluye enteros; rangos numéricos vía `minimum`/`maximum`; la validación verifica conformidad, no transforma valores. |

---

## 4. Validated claims

Cada claim mapea a source IDs validados en §3.

**RQ1 — Canonicalización de timestamps**

- **C1** — Navigation Timing define todos los valores de tiempo en **milisegundos**; `responseStart` es el momento en que se recibe el primer byte de la respuesta. `[S1][S2]`
- **C2** — TTFB es una **duración** derivada como `responseStart - navigationStart` (ms); el "response time" como `responseStart - requestStart` (ms). La `value` de la métrica RUM es por lo tanto una duración en ms, no un instante de reloj de pared. `[S2]`
- **C3** — Paint Timing expone FCP como la entrada `PerformancePaintTiming` `"first-contentful-paint"` con `startTime` un `DOMHighResTimeStamp` en **milisegundos** (desde el time origin); el tiempo de presentación se engrosa al múltiplo de **4 ms**. `[S3][S4]`
- **C4** — RFC 3339 define el formato `date-time` de Internet (un perfil de ISO 8601): `date-time = full-date "T" full-time`; `time-offset = "Z" / time-numoffset`; una **hora local no calificada es inaceptable** para la interoperabilidad; los offsets numéricos son obligatorios; `Z` denota offset UTC 00:00. `[S13]`
- **C5** — El `format: date-time` de OpenAPI se define como **RFC 3339 §5.6** (tipo JSON `string`); ejemplo `2017-07-21T17:32:28Z`. `[S19][S20]`
- **C6** — RFC 3339 recomienda UTC y establece que no se atienden las reglas de zona horaria local; `T`/`Z` en mayúscula DEBERÍAN generarse. `[S13]`
- **C7** — El remote-write de Prometheus **rechaza** una muestra cuyo timestamp excede una cota máxima-a-futuro (`now + maxAheadTime`) con `ErrOutOfBounds` → HTTP 400 — rechaza en lugar de reescribir timestamps futuros. `[S14]`
- **C8** — Prometheus permite una tolerancia de clock skew de **+10 minutos** (alineada con el scrape path), porque rechazar con demasiada agresividad rompe ante pequeñas derivas de reloj emisor/receptor; puntos de referencia: NTP advierte a 0.5–1 s, OIDC usa 30 s. `[S15]`
- **C9** — Los timestamps del remote-write de Prometheus son int64 de milisegundos **absolutos** desde la epoch Unix — distintos de las duraciones relativas `DOMHighResTimeStamp` de W3C desde el time origin. Un contrato de ingesta no debe confundir ambos. `[S16][S1][S3]`

**RQ2 — Conversión de alias de unidad → canónica**

- **C10** — OTel: las unidades de instrumentos siguen **UCUM**; al medir duraciones, **DEBERÍA usarse segundos (`s`)**; los nombres de instrumentos NO DEBERÍAN incluir unidades. `[S6][S18]`
- **C11** — Las duraciones HTTP de OTel usan la unidad `s` (`http.server.request.duration`); el cambio de `ms`→`s` se hizo explícitamente para alinearse con Prometheus/OpenMetrics. `[S7][S9][S8]`
- **C12** — El Technical Committee de OTel votó segundos (`s`, UCUM sensible a mayúsculas) como la unidad recomendada para duración; Prometheus/OpenMetrics recomiendan fuertemente segundos para duraciones. `[S8]`
- **C13** — Los conteos de OTel son adimensionales: los conteos enteros DEBERÍAN usar anotaciones entre llaves (`{request}`, `{error}`) sin `1` inicial; las fracciones de utilización usan la unidad `1`. `[S6][S18]`
- **C14** — W3C/Web Vitals expresan TTFB/FCP nativamente en **milisegundos**; FCP bueno ≤1.8 s / pobre >3.0 s es una **calificación** (referencia), no un criterio de rechazo. `[S1][S2][S3][S5]`
- **C15** — Las unidades SI de tiempo son escalares con conversión exacta y sin pérdida (`1 s = 1000 ms`), por lo que una conversión alias→canónica (p. ej. segundos→milisegundos ×1000) es un cambio de representación puro y no altera la magnitud de la medición. `[S13][S6]`

**RQ3 — Canonicalización de nombres y `error_type`**

- **C16** — OTel define `exception.type` como "el tipo de la excepción (su nombre de clase totalmente calificado, si aplica)"; se prefiere el tipo **dinámico** sobre el estático. `[S10]`
- **C17** — `error.type` de OTel DEBERÍA ser **predecible y de baja cardinalidad**; cuando se fija a un tipo, DEBERÍA usarse su **nombre de clase canónico**; el fallback conocido `_OTHER` DEBE usarse cuando aplica uno de los valores conocidos. `[S11][S7]`
- **C18** — ECMAScript/MDN definen un catálogo fijo de built-ins: `Error` (base), `EvalError`, `RangeError`, `ReferenceError`, `SyntaxError`, `TypeError`, `URIError`, `AggregateError`, `InternalError`. `[S12]`
- **C19** — Sentry agrupa errores por fingerprint derivado de stack trace, tipo de excepción y mensaje; las reglas de fingerprint matchean `error.type` (nombre de excepción) y pueden **mapear muchos tipos a un grupo** (`error.type:ConnectionError -> system-down`); `{{ error.type }}` opta por un grupo por tipo. Esto modela ambas direcciones: canonicalizar tipos desconocidos a un bucket estable y preservar deliberadamente tipos distintos. `[S17]`
- **C20** — Las convenciones de nombrado de métricas de OTel usan identificadores **en minúsculas, separados por puntos** (p. ej. `http.server.request.duration`). `[S7]` (Entra en conflicto con los nombres `UPPER_SNAKE` del proyecto — ver §5.)

**RQ4 — Política de valores ausentes / inválidos**

- **C21** — El `type` de JSON Schema restringe el tipo primitivo JSON; `number` incluye enteros; las cotas numéricas usan `minimum`/`maximum`. La validación verifica conformidad y **no transforma** las instancias. `[S22]`
- **C22** — El `default` de JSON Schema aporta un valor JSON por defecto para un esquema y DEBERÍA validar él mismo contra el esquema; es un default de metadato/anotación, no una reescritura implícita de la instancia. `[S22]`
- **C23** — La coerción de tipos de Ajv está **deshabilitada por defecto** (`coerceTypes: false`); cuando se habilita explícitamente, la coerción string→number usa `+data`, es decir, solo acepta strings que son números válidos y cambia la representación, no la magnitud. `[S21]`
- **C24** — El `format` de OpenAPI es una pista de validación, no una directiva de coerción; las cotas `minimum` (p. ej. `value ≥ 0`) restringen las instancias aceptadas. `[S20][S22]`
- **C25** — El único patrón autoritativo para datos temporales fuera de rango/límite en un pipeline de ingesta real (Prometheus) es **rechazar con un error**, nunca recortar/reescribir en silencio. `[S14][S15]`

---

## 5. Contradicciones, incertidumbre y frescura

**Evidencia externa vs contrato del proyecto (quién gana):**

| # | Conflicto | Evidencia externa | Contrato del proyecto | Ganador / acción |
|---|---|---|---|---|
| X1 | Unidad canónica de duración | OTel canónica = `s` (C10–C12) | `ms` para TTFB/FCP/XHR_LATENCY; OpenAPI `unit enum [ms, count]` | **Gana el contrato del proyecto.** Las duraciones RUM del navegador son nativamente ms (C1–C3, C14). `s` pasa a ser un **alias de entrada** aceptado, normalizado a `ms` (×1000). |
| X2 | Representación de la unidad de conteo | OTel usa anotaciones `{error}` / `{request}`, adimensionales (C13) | `count` (enum OpenAPI) | **Gana el contrato del proyecto.** La evidencia externa igual respalda que los conteos son enteros adimensionales, por lo que `count` es una elección canónica válida; `{…}` es solo una notación. |
| X3 | Capitalización/formato de nombre de métrica | OTel = minúsculas separadas por puntos `http.server.request.duration` (C20) | `UPPER_SNAKE` (`TTFB`, `XHR_LATENCY`, …) | **Gana el contrato del proyecto.** OTel es *guía* de nombrado, no un catálogo RUM; la canonicalización aplica principios de estabilidad/case-fold (C17) a los nombres del proyecto. |
| X4 | Notación del fallback de error desconocido | OTel = `_OTHER` (C11) | Ejemplos del contrato = `Other` | **Gana el contrato del proyecto** (`Other`). El concepto (bucket de fallback estable de baja cardinalidad) es idéntico (C17). |
| X5 | Tipo del valor `count` | JSON Schema `number` (C21) | La matriz de validación dice `number (entero)` para `JS_EXCEPTION_RATE`/`RAGE_CLICK`; OpenAPI dice `value: number, minimum: 0` | **Inconsistencia interna del contrato** entre la matriz de validación (entero) y OpenAPI (`number`). **No** redondear en silencio: el redondeo es un cambio de magnitud. Exponer como decisión abierta (rechazar conteos no enteros vs aceptar como almacenado `DOUBLE PRECISION`). |
| X6 | Tratamiento de timestamps futuros | Prometheus rechaza más allá de una pequeña tolerancia (C7, C8) | Contrato línea 30: los rangos de sanity son cotas de **rechazo**; lo fuera de rango es la señal de anomalía | **Alineado: rechazo, nunca recorte.** Un timestamp futuro/reenviado fuera de rango es dato de interés; el fallback `now()` del worker actual es una reescritura silenciosa que no debe sobrevivir en el normalizador. |

**Especificidad del conjunto de alias (incertidumbre):** Ninguna fuente autoritativa enumera un conjunto de alias aceptado para la ingesta RUM. La evidencia establece las **unidades canónicas y los factores de conversión exactos** (`s`↔`ms`, count = adimensional) y el *principio* de que las duraciones se escriben convencionalmente en segundos o milisegundos; la lista concreta de alias (`sec`, `secs`, `msec`, `millis`, …) es una **decisión de producto**, no un claim con fuente.

**Tolerancia de clock skew (incertidumbre):** No hay una única tolerancia normativa. Prometheus usa +10 minutos para tolerancia de skew pero rechaza de inmediato las muestras muy a futuro (C7, C8). Si el proyecto agrega una guarda de timestamps futuros, debería expresarse como una **cota de rechazo**, no como una reescritura — reflejando C7/C25.

**Frescura:** Todas las fuentes accedidas el 2026-10-13. RFC 3339 (2002, aún el perfil de Internet, actualizado por RFC 9557). Las convenciones semánticas HTTP de OTel se estabilizaron en 2023-11 (C9/S9). W3C Navigation Timing 2 y Paint Timing son documentos W3C vigentes. web.dev FCP actualizado por última vez el 2023-12-06. Las fuentes de Prometheus son de la rama `main` / PRs actuales. Ninguna fuente es más antigua de lo que justifica su estatus aún autoritativo.

---

## 6. Decisiones de producto (confirmadas — no autoritativas, intención retenida)

Registradas como inputs confirmados; **no** son evidencia. Cada una se anota con la evidencia en la que se apoya y dónde la evidencia calla.

| # | Decisión | Resuelve | Respaldo de evidencia |
|---|---|---|---|
| D1 | Las inconsistencias de unidad se resuelven por **conversión de alias conocidos a la unidad canónica**, no por rechazo estricto. | Exploration Q1 | Las unidades y factores canónicos están respaldados por fuentes (C10–C15); *la conversión-vs-rechazo en sí es una elección de producto* — la evidencia respalda los objetivos y el hecho de que la conversión preserva la magnitud. |
| D2 | El orden del pipeline es **normalizar ANTES de validar** (`Raw → Normalize → Validate → Enqueue → Store`). | Exploration Q2 | **Sin evidencia externa** (esto es arquitectura, no semántica de telemetría). Razón: la validación sigue siendo la autoridad única de rechazo mientras la normalización resuelve representaciones que de otro modo rechazaría. |
| D3 | La normalización de `error_type` es **canonicalización en código** (trim/case + mapa de alias, desconocido → `Other`), **sin catálogo DDL / sin migración**. | Exploration Q3 | El tipo de error canónico de baja cardinalidad + fallback estable está respaldado por fuentes (C16, C17, C19); *sin-DDL es una elección de producto*. |
| D4 | **RESTRICCIÓN DURA**: la normalización es de solo representación; NUNCA DEBE recortar/reparar magnitudes o valores fuera de rango. Los rangos de sanity son cotas de rechazo; esos valores son la señal de anomalía. | Contrato `ContratoIngestaRUM.md:30` | Fuertemente respaldado: reglas de representación de RFC 3339 (C4), no-transformación de JSON Schema (C21), la coerción de Ajv es opt-in y de solo representación (C23), Prometheus rechaza en lugar de reescribir fuera de rango (C7, C25). |

---

## 7. Recomendaciones por área (respaldadas por evidencia; para spec/design)

### Área 1 — Canonicalización de timestamps

- **Forma canónica**: un datetime con zona horaria normalizado a **UTC**, serializado como RFC 3339 / ISO 8601 `date-time` con offset explícito (`Z` preferido). Aceptar cualquier offset RFC 3339 válido y convertir a UTC (solo representación). `[C4][C5][C6]`
- **Rechazar**, no reparar: datetimes naïve, zona horaria ausente, strings no parseables → `invalid_timestamp`. `[C4][S13]`
- **Precedencia**: `metrics[].timestamp` si está presente, si no el `timestamp` del envelope (ya es el comportamiento del contrato). `[C2]` (la `value` de la métrica es una duración; `timestamp` es el instante de captura)
- **Clock skew / timestamps futuros**: **nunca recortar.** Si se agrega alguna protección, expresarla como una **cota de rechazo** (p. ej. `timestamp > now + tolerance`), reflejando el comportamiento de Prometheus de rechazar-no-reescribir; un timestamp futuro/anómalo legítimo es señal, no ruido. `[C7][C8][C25]`
- **Eliminar el fallback silencioso `now()`** para eventos aceptados: escribir el tiempo de ingesta sobre un timestamp de cliente inválido es una reescritura de magnitud/tiempo que corrompe el análisis temporal y contradice D4. `[C7][C25]`

### Área 2 — Conversión de alias de unidad → canónica

- **Objetivos canónicos** (contrato): `ms` para TTFB/FCP/XHR_LATENCY; `count` para JS_EXCEPTION_RATE/RAGE_CLICK. `[C14][C13]`
- **Familias de alias aceptadas** (acotadas, con coherencia por métrica): para métricas de duración, la familia `s` (`s`, `sec`, `secs`, `second`, `seconds`) y la familia `ms` (`ms`, `msec`, `msecs`, `millisecond`, `milliseconds`, `millis`); para métricas de conteo, la familia `count`. Las unidades desconocidas/no soportadas aún se rechazan (`invalid_unit`). `[C10][C12][C15]` — **la lista exacta de alias es una elección de producto** (§5).
- **Factores de conversión**: `s`→`ms` ×1000; `ms`→`ms` ×1; count sin cambios. La conversión es escalar y preserva la magnitud. `[C15]`
- **Por qué convertir en lugar de rechazar**: la unidad es una *representación* de la misma cantidad física; W3C emite ms nativamente mientras que el ecosistema más amplio (OTel/Prometheus) emite segundos, por lo que mediciones idénticas llegan bajo etiquetas distintas — canonicalizarlas preserva la señal y es el objetivo de "resolver inconsistencias de unidad". `[C10][C12][C14][C15]`
- **Idempotencia**: la conversión está indexada por la unidad de entrada declarada y se aplica exactamente una vez; tras la normalización la unidad es canónica, por lo que una segunda pasada es un no-op (`ms`→×1). Nunca reinterpretar un valor canónico. `[C15]`
- **Valores fraccionarios de `count`**: **no** redondear (cambio de magnitud); rechazar o aceptar tal cual según la decisión abierta X5. `[C21][C23]`

### Área 3 — Canonicalización de nombre de métrica y `error_type`

- **Nombres de tipo de métrica**: conjunto canónico `{TTFB, FCP, XHR_LATENCY, JS_EXCEPTION_RATE, RAGE_CLICK}`. Normalizar recortando y aplicando case-fold a la entrada hacia la grafía canónica, más un mapa de alias explícito y acotado para sinónimos conocidos. Tras la normalización, los nombres desconocidos se rechazan (`invalid_metric_type`). Los nombres canónicos siguen el `UPPER_SNAKE` del proyecto (el contrato gana sobre la capitalización de OTel). `[C17][C20]`
- **`error_type`**: recortar espacios en blanco, canonicalizar la capitalización, y mapear a un catálogo acotado; los valores desconocidos/no mapeados → `Other`. El catálogo debería incluir los built-ins de ECMAScript (`Error`, `EvalError`, `RangeError`, `ReferenceError`, `SyntaxError`, `TypeError`, `URIError`, `AggregateError`, `InternalError`) más los ejemplos del contrato (`UnhandledRejection`, `Other`). Esto refleja el principio de OTel de nombre de clase canónico + fallback, estable y de baja cardinalidad, con `Other` como el `_OTHER` del proyecto. `[C16][C17][C18][C19]`
- **Solo se canonicaliza la etiqueta**; los campos portadores de anomalía (`message`, `stack_trace`, valores) nunca se reescriben. `[C19][S17]`
- **Sin catálogo DDL/migración** (D3): la canonicalización es en código; la BD mantiene `error_type TEXT` (ya es el caso). `[C17]`

### Área 4 — Política de valores ausentes / inválidos

- **Requerido ausente** → **rechazar** (`missing_required_field`). **Opcional ausente** → aplicar solo los defaults/herencia que el contrato ya define (metric `timestamp` ← envelope `timestamp`; nulables `page_url`, `stack_trace`, `metric_id`, `user_agent`); no inventar defaults semánticos. `[C22][S22]`
- **Representación inválida** (segura de reparar, solo representación): coerción de cadenas numéricas (`"120.5"` → `120.5`) solo para cadenas numéricas finitas válidas, y recorte de espacios en blanco en strings. Es una flexibilidad deliberada; notar que la coerción de JSON Schema/Ajv está **deshabilitada por defecto**, por lo que es un opt-in explícito, y la coerción debe usar el equivalente de `+data` (verificación de número válido), nunca una transformación de magnitud. `[C21][C23]`
- **Reparaciones prohibidas**: recortar, limitar, redondear para satisfacer un rango, sustituir `now()`, o cualquier reescritura de una magnitud fuera de rango. Fuera de rango → `invalid_range`; `value` negativa → `invalid_range` (`value ≥ 0`). `[C21][C24][C25]`
- **Strings NaN / Infinity / no finitos** (`"NaN"`, `"Infinity"`) deben **rechazarse**, no convertirse a número. `[C21][C23]`

---

## 8. Readiness y persistencia

- **Outcome**: `done`. Ambas clases declaradas ejercitadas con llamadas reales; 22 fuentes, 25 claims, las cuatro RQ mapeadas a fuentes validadas.
- **Store**: `openspec` (repo-local). Artefacto de evidencia persistido en `openspec/changes/ISS-S3-02/research.md`. Según la matriz de readiness, el readiness solo-openspec requiere una escritura OpenSpec exitosa + readback y decisiones confirmadas — satisfecho.
- **Decisiones de producto**: D1–D4 registradas como **confirmadas** (intención retenida), separadas de la evidencia (§6).
- **Readiness de propuesta**: `proposal_ready = true` para el store openspec, sujeto a la propiedad del orquestador de `gentle-ai.sdd-preproposal/v1` (no escrito por esta fase).
- **Ítems abiertos expuestos para spec/design (no bloqueantes)**: X5 (`count` entero-vs-number), la membresía exacta de la lista de alias de §5, y la cota opcional de rechazo de timestamps futuros.

---

## Aprendizajes clave

1. OTel canonicaliza las unidades de duración a segundos, pero las duraciones RUM del navegador son nativamente milisegundos, por lo que gana el contrato `ms` del proyecto y `s` debe ser un alias de entrada convertido ×1000.
2. La normalización debe ser de solo representación porque Prometheus rechaza los timestamps futuros fuera de límites en lugar de reescribirlos, y tanto RFC 3339 como JSON Schema tratan la representación como algo distinto de la magnitud.
3. OpenTelemetry `error.type` requiere un fallback predecible, de baja cardinalidad y canónico, que mapea directamente al bucket `Other` del proyecto para valores `error_type` de JS desconocidos.
4. `date-time` de OpenAPI se define como RFC 3339 §5.6, y RFC 3339 hace inaceptable una hora local no calificada, que es la base de fuente para rechazar timestamps naïve.
5. AJV deshabilita la coerción de tipos por defecto, por lo que la coerción de cadenas numéricas es un opt-in deliberado y nunca debe extenderse a redondeo o recorte de magnitudes de métricas.
