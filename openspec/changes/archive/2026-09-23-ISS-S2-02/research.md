# RESEARCH — ISS-S2-02: Aplicaciones y credenciales de ingesta

**Artefacto**: `gentle-ai.sdd-research/v1`
**Cambio**: ISS-S2-02 (GitHub #36). **Base**: `develop` con ISS-S2-01 mergeado (PR #53).
**Fase**: sdd-research. **Rama**: `feat/ISS-S2-02`.
**Modo**: openspec (repo-local) + Engram (recuperación). **Idioma**: español neutro técnico.
**Revision**: `r3`. **Outcome**: `done`. **Fecha**: 2026-09-16.

---

## 1. Admisión y grants observados (re-entrada r3)

Declaración de capacidad recibida del orquestador (`gentle-ai.sdd-research-capability/v1`) — idéntica a r1/r2:

| Clase | Grant declarado | Herramientas declaradas |
|---|---|---|
| `open-web` | granted | `websearch`, `webfetch` |
| `documentation` | granted | `context7_resolve-library-id` + `context7_query-docs` (MCP Context7) |

Grants observados en el runtime de ejecución (ambas clases ejercitadas con llamadas reales antes de registrar claims):

| Clase | Grant observado | Verificación |
|---|---|---|
| `open-web` | **DISPONIBLE** | `websearch` (2 consultas exitosas) y `webfetch` (3 fetches exitosos: OWASP API2, Stripe keys, MDN 401, GitHub PAT). |
| `documentation` | **DISPONIBLE** | `context7_resolve-library-id` (resolvió `/schemathesis/schemathesis`) y `context7_query-docs` (auth OpenAPI y checks). |

**Resultado de admisión: ACEPTADA.** El runtime recargó los permisos que estaban pendientes desde r2 (la actualización de configuración del usuario ahora es efectiva). Se accede a fuentes y se emiten claims con respaldo de source IDs.

---

## 2. Preguntas de investigación (RQ) — intento retenido (sin cambios respecto de r1/r2)

- **RQ1** — Convención de header y semántica HTTP para autenticación por API key en APIs REST: `X-API-Key` vs `Authorization: Bearer`/`ApiKey`, y qué códigos/headers corresponden (401 sin credencial/inválida, 403 app inactiva, `WWW-Authenticate`).
- **RQ2** — Generación y almacenamiento de API keys: entropía mínima, prefijos identificables, mostrar la key en claro una única vez, y hashing (¿SHA-256 sin salt es aceptable para keys de alta entropía? ¿cuándo conviene un KDF?), comparación timing-safe.
- **RQ3** — Rotación y revocación: patrones de industria (GitHub/Stripe) sobre revocación explícita vs reemplazo inmediato vs ventana de overlap; ventajas/riesgos de cada uno.
- **RQ4** — Efecto de desactivar una aplicación sobre sus credenciales, y aislamiento multi-tenant derivado del binding credencial→tenant (nunca confiar el tenant del payload). Referencias OWASP API Security Top 10 (BOLA/API1, broken auth/API2).
- **RQ5** — OpenAPI 3.1: aplicación del security scheme `apiKey` a paths y su verificación con contract testing (schemathesis); implicancias de retirar un campo de un schema de respuesta (breaking change de contrato).

---

## 3. Sources

| id | class | title | publisher | URL | accessed_at | excerpt |
|---|---|---|---|---|---|---|
| S1 | open-web | x-api-key: The API Key Header Explained, With Code and Gotchas | SelfDevKit | https://selfdevkit.com/blog/x-api-key/ | 2026-09-16 | `X-API-Key` no está en RFCs ni en el registro IANA; convención de facto por AWS API Gateway. RFC 6648 desaconseja el prefijo `X-`; RFC 9110 define 401 (credencial ausente/inválida) y 403 (válida sin permiso). `Authorization: Bearer` es estandarizado y suele redactarse de logs. |
| S2 | open-web | x-api-key HTTP Header — API Evangelist Headers | API Evangelist | https://headers.apievangelist.com/store/x-api-key/ | 2026-09-16 | Sin estándar; 667 providers lo declaran con 7 spellings distintos. Nombres HTTP case-insensitive (RFC 9110 §5.1) pero los clientes generados difieren. Declarar como security scheme `apiKey`, no como parámetro de header. |
| S3 | open-web | API Keys — OpenAPI Specification docs | Swagger.io (OpenAPI Initiative) | https://swagger.io/docs/specification/v3_0/authentication/api-keys/ | 2026-09-16 | Security scheme `apiKey` con `type: apiKey`, `in: header/query/cookie`, `name`; `securitySchemes` solo no basta, se necesita `security` global u operación; 401 con `WWW-Authenticate` para key ausente/inválida. |
| S4 | open-web | 401 Unauthorized — HTTP status codes | MDN Web Docs (Mozilla) | https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/401 | 2026-09-16 | 401 = falta credencial válida, se envía con `WWW-Authenticate` indicando el esquema esperado; 403 = credencial válida pero sin permiso para la acción. Referencia RFC 9110 §status.401. |
| S5 | open-web | Authentication Headers in REST APIs | Medium (Hector Reyes Alemán) | https://hector-reyesaleman.medium.com/authentication-headers-in-rest-apis-d0482df3ec08 | 2026-09-16 | `Authorization: Bearer` definido en RFC 6750; esquema custom `Authorization: ApiKey` usado por Stripe/Twilio/SendGrid; `X-API-Key` tiene costos: cache HTTP no lo trata como privado, CORS preflight, tooling manual. |
| S6 | open-web | Hashing & Storage — apikeys.guide | apikeys.guide | https://apikeys.guide/docs/security/hashing-and-storage | 2026-09-16 | Para keys irrecuperables, hash SHA-256 (FIPS 180-4, rápido, determinístico); bcrypt/Argon2 son anti-patrón para secrets de alta entropía (reservados a contraseñas). Comparación en tiempo constante; prefijo en claro para lookup O(1); salt opcional. CWE-208. |
| S7 | open-web | Design Customer-Facing API Keys for SaaS: Hashing, Prefixes, Rotation, and Scopes | AverageDevs | https://averagedevs.com/blog/design-customer-facing-api-keys-saas | 2026-09-16 | Hash + prefijo público; nunca el plaintext; show-once; lookup por prefijo + `timingSafeEqual`; HMAC-SHA256 con pepper en secret store (no bcrypt: 100ms por request = outage autoinfligido); rotación con ventana dual; tenant_id en la fila de la key. |
| S8 | open-web | How to Securely Store and Validate API Tokens in a Database | EncryptCodec | https://encryptcodec.com/blog/how-to-securely-store-and-validate-api-tokens-in-a-database | 2026-09-16 | SHA-256 del token (nunca plaintext); CSPRNG 32 bytes base64url; prefijo indexado solo para lookup (~48 bits reversible — la seguridad es el hash completo); comparación constante en app code, no en SQL; el hash es dato interno (tratarlo como hash de contraseña). |
| S9 | open-web | API Keys: How to Generate, Rotate, and Store Them Securely | WebToolkit | https://www.webtoolkit.tech/guides/api-keys-generate-rotate-store | 2026-09-16 | ≥128 bits de entropía; CSPRNG (`crypto.randomBytes`, `secrets`, `crypto/rand`); prefijo identificable alimenta detectores de leaks (GitHub Secret Scanning, TruffleHog); show-once; SHA-256 OK (input ya de alta entropía); comparación constante. |
| S10 | open-web | Migrating API Key Authentication from Bcrypt to HMAC-SHA256 with In-Memory Caching | VesselAPI | https://vesselapi.com/blog/optimizing-api-authentication-hmac | 2026-09-16 | bcrypt: 65–100ms por comparación y no indexable (salt aleatorio → scan de toda la tabla); con 256 bits de entropía la lentitud no aporta; migración a HMAC-SHA256 con pepper en Secrets Manager (~1μs, lookup indexado). |
| S11 | open-web | API Key Management for a Public SaaS API | Iurii Rogulia | https://iurii.rogulia.fi/blog/api-key-management-saas | 2026-09-16 | randomBytes(32) = 256 bits; SHA-256 no bcrypt (nada que brute-forcear); show-once; prefix + hint (últimos 4 chars, patrón Stripe/GitHub); revocación fail-closed: key revocada tratada como inexistente; grace period para rotación planificada, revocación inmediata para compromiso. |
| S12 | open-web | API keys — Stripe Documentation | Stripe | https://docs.stripe.com/keys | 2026-09-16 | Rotar revoca y genera reemplazo inmediato; grace period hasta 7 días con ambas keys válidas; "Expire now" elimina la vieja al instante; keys perdidas no recuperables; reveal-once en live mode; prefijos `sk_/rk_/pk_` + `_live_`/`_test_`. |
| S13 | open-web | API Key Rotation Without Downtime 2026 | Decryption Digest | https://www.decryptiondigest.com/blog/api-key-rotation-zero-downtime-distributed-systems | 2026-09-16 | Patrón dual-credential: old + new válidas durante el overlap; no desactivar la vieja por timer, solo tras confirmar migración de consumidores; GitHub PATs ilimitados (ambos funcionan en paralelo); revocación de compromiso inmediata. |
| S14 | open-web | Managing your personal access tokens | GitHub Docs | https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens | 2026-09-16 | Prefijos `ghp_`/`github_pat_`/`ghu_`; revocación automática si se filtra a repo público o queda sin uso 1 año; tokens atados al recurso: si el usuario pierde acceso, el token se vuelve inactivo; scopes mínimos por repo. |
| S15 | open-web | API Key Management: Rotation & Revocation 2026 | APIScout | https://apiscout.dev/guides/api-key-management-rotation-2026 | 2026-09-16 | Guías: rotación 90 días producción, 30 días service-to-service/admin; overlap Day 0–7 con ambos keys válidos; GitHub escanea repos públicos y auto-revoca leaks. |
| S16 | open-web | How to rotate API keys safely (checklist) | PassStore | https://passstore.makio.app/blog/rotate-api-keys-safely | 2026-09-16 | Orden: inventariar → emitir nueva (least privilege) → deploy → verificar tráfico → revocar vieja; nunca revocar primero salvo abuso activo confirmado. |
| S17 | open-web | API2:2023 Broken Authentication — OWASP API Security Top 10 2023 | OWASP | https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/ | 2026-09-16 | "API keys should not be used for user authentication. They should only be used for API clients authentication." No reinventar autenticación/generación/almacenamiento: usar estándares. Vulnerable: credenciales en URL, hashing débil, tokens predecibles, sin anti-brute-force. |
| S18 | open-web | API1:2023 Broken Object Level Authorization — OWASP API Security Top 10 2023 | OWASP | https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/ | 2026-09-16 | Validar autorización a nivel objeto en cada función que acceda a datos con un ID del cliente; el servidor no debe confiar en IDs del payload; preferir GUIDs aleatorios e impredecibles. |
| S19 | documentation | API Authentication — Schemathesis docs | Schemathesis (ReadTheDocs) | https://schemathesis.readthedocs.io/en/latest/guides/auth/ | 2026-09-16 | Auth alineada al spec: `[auth.openapi.ApiKeyAuth] api_key = "${API_KEY}"`; el nombre del bloque debe coincidir con el securityScheme; soporta `apiKey` para OpenAPI 2.0 y 3.x; sanea valores sensibles por defecto; elimina auth en operaciones de testing de seguridad. |
| S20 | open-web | Discussion #1822: Experimental Open API 3.1 support | Schemathesis (GitHub) | https://github.com/schemathesis/schemathesis/discussions/1822 | 2026-09-16 | Soporte experimental de OpenAPI 3.1: `--experimental=openapi-3.1` / `schemathesis.experimental.OPEN_API_3_1.enable()`; inicialmente validación de respuestas (JSON Schema compatible); la generación de datos sigue OpenAPI 3.0. |
| S21 | open-web | OpenAPI 3.1 Contract Testing Guide: Spec-Driven QA in 2026 | QASkills.sh | https://qaskills.sh/blog/openapi-3-1-contract-testing-guide-2026 | 2026-09-16 | OpenAPI 3.1 alineado con JSON Schema 2020-12; nulabilidad con `type: [string, "null"]` (adios `nullable: true`); Schemathesis property-based; oasdiff: remover campo requerido de respuesta = breaking; Dredd replay determinístico. |
| S22 | open-web | Issue #3516: schemathesis no entiende respuestas/status codes de openapi 3.1.0 | Schemathesis (GitHub) | https://github.com/schemathesis/schemathesis/issues/3516 | 2026-09-16 | Checks `status_code_conformance` y `positive_data_acceptance`; configuración de códigos esperados (p.ej. 2xx/401/403/404/409/422/5xx) en `schemathesis.toml`; validación de respuesta contra el schema del spec. |
| S23 | documentation | Configuration reference (checks) — Schemathesis docs | Schemathesis (ReadTheDocs) | https://github.com/schemathesis/schemathesis/blob/master/docs/reference/configuration.md | 2026-09-16 | `[checks.status_code_conformance] enabled = false`, `[checks.negative_data_rejection] expected-statuses`; auth openapi global (no por operación); headers por operación. |

---

## 4. Validated claims

Cada claim mapea a source IDs verificados en §3. **RQ1 — header y semántica HTTP**:

- **C1** — `X-API-Key` no está definido por ningún RFC ni registrado en el registro IANA de campos HTTP; es una convención de facto popularizada por AWS API Gateway, no un estándar. `[S1][S2]`
- **C2** — RFC 6648 (2012) desaconseja el prefijo `X-` para parámetros nuevos en protocolos de aplicación; RFC 9110 define 401 para credencial ausente/inválida y 403 para credencial válida sin permiso. `[S1][S4]`
- **C3** — Semántica recomendada para API propias: **401** (con `WWW-Authenticate`) para key ausente o inválida y **403** para key válida pero sin permiso o deshabilitada; es práctica común de la industria (p.ej. AWS API Gateway) devolver 403 para ambos casos, lo que se considera "técnicamente laxo". `[S1][S4][S5]`
- **C4** — `Authorization: Bearer` es un esquema HTTP estandarizado (RFC 6750) y las infraestructuras (proxies, gateways, monitoreo) suelen redactarlo de logs por defecto; un header custom como `X-API-Key` no recibe ese tratamiento, lo que facilita fugas de keys en logs. `[S1][S5]`
- **C5** — Los nombres de campos HTTP son case-insensitive (RFC 9110 §5.1), pero en contratos publicados se observan 7 spellings distintos de `x-api-key`; los clientes generados dependen del string exacto. Se debe fijar un único spelling y declararlo como security scheme `apiKey`, no como parámetro de header. `[S2]`
- **C6** — En OpenAPI el scheme se declara como `type: apiKey`, `in: header|query|cookie`, `name`; `securitySchemes` por sí solo no aplica el esquema — se requiere `security` global o por operación; la respuesta 401 para key ausente/inválida puede incluir `WWW-Authenticate`. `[S3]`

**RQ2 — generación y almacenamiento**:

- **C7** — Entropía mínima recomendada de 128 bits (práctica habitual: 32 bytes / 256 bits) generada con CSPRNG (`crypto.randomBytes`, Python `secrets`, Go `crypto/rand`); nunca `Math.random()` ni RNG con seed temporal. `[S8][S9][S11]`
- **C8** — Un prefijo identificable (`ilp_`, `sk_live_`, `ghp_`, `github_pat_`) permite identificar tipo/entorno de un vistazo, alimentar detectores automáticos de leaks (GitHub Secret Scanning, TruffleHog) y realizar lookup O(1) por prefijo sin exponer el secreto. `[S9][S11][S14]`
- **C9** — La key en claro se muestra una sola vez al crear (show-once) y nunca se persiste; se almacena hash + prefijo (+ hint opcional de últimos 4 chars, patrón Stripe/GitHub). `[S7][S8][S11][S12]`
- **C10** — Para keys de alta entropía, **SHA-256 sin salt es aceptable y es el hash recomendado**: determinístico (FIPS 180-4), indexable y rápido; bcrypt/Argon2 son un anti-patrón porque su lentitud deliberada (65–100 ms por comparación) no aporta nada contra brute-force de keys aleatorias y penaliza el hot path de cada request. `[S6][S7][S8][S9][S10][S11]`
- **C11** — Defensa en profundidad opcional: HMAC-SHA256 con pepper en un secret manager (un robo de DB sin el pepper deja los hashes inutilizables); el salt por key es opcional, no crítico, para keys de alta entropía. `[S6][S7][S10]`
- **C12** — La comparación del hash debe ser en tiempo constante (`timingSafeEqual`); la comparación por igualdad de strings (`===` o en SQL) puede filtrar información por timing (CWE-208). `[S6][S7][S8]`
- **C13** — El prefijo NO es un secreto: 8 caracteres base64url ≈ 48 bits son reversibles por enumeración; la seguridad real la aporta el hash completo de la key (256 bits). Nunca exponer el hash en respuestas de API. `[S8]`

**RQ3 — rotación y revocación**:

- **C14** — El patrón estándar de rotación sin downtime es **dual/overlap**: emitir la key nueva antes de revocar la vieja, ambas válidas durante la ventana, y desactivar la vieja solo cuando todos los consumidores migraron (nunca por timer ciego). `[S13][S16]`
- **C15** — Stripe: rotar revoca y genera un reemplazo inmediato, con grace period de hasta **7 días** en que ambas keys funcionan; "Expire now" elimina la vieja al instante; las keys perdidas no se pueden recuperar. `[S12]`
- **C16** — GitHub: admite múltiples tokens en paralelo (create-before-revoke con scopes equivalentes); revocación automática si el token se filtra a un repo público o queda sin uso durante 1 año; revocación manual por settings o REST. `[S13][S14]`
- **C17** — La revocación por compromiso debe ser **inmediata** (fail-closed); la ventana de overlap es para rotación planificada, no para incidentes. `[S11][S13][S16]`
- **C18** — Guías de terceros sugieren rotación periódica (90 días producción, 30 días service-to-service/admin); no es un estándar normativo. `[S15]`

**RQ4 — desactivación de app y aislamiento multi-tenant**:

- **C19** — OWASP API2:2023: las API keys **no deben usarse para autenticación de usuarios**, solo para autenticación de clientes API; no reinventar autenticación, generación ni almacenamiento de tokens — usar estándares. `[S17]`
- **C20** — OWASP API1:2023 (BOLA): validar autorización a nivel objeto en **cada** función que acceda a datos usando un ID provisto por el cliente; el servidor no debe confiar en IDs del payload para decidir qué objeto acceder; preferir IDs aleatorios e impredecibles. `[S18]`
- **C21** — OWASP API2:2023 lista como vulnerabilidades: credenciales en la URL, hashing débil de tokens, tokens predecibles, ausencia de rate limiting/anti-brute-force. `[S17]`
- **C22** — Las credenciales deshabilitadas deben **fallar cerrado**: una key revocada o deshabilitada se trata como inexistente (401); el desactivado del recurso asociado deja la credencial inoperante (GitHub: el token se vuelve inactivo si el usuario pierde acceso al recurso). `[S11][S14]`
- **C23** — Aislamiento multi-tenant por binding credencial→tenant: el tenant se deriva de la fila autenticada de la credencial (tenant_id), nunca del payload del request; esto es la mitigación directa de BOLA/API1. `[S7][S18]`

**RQ5 — OpenAPI 3.1 y contract testing**:

- **C24** — OpenAPI 3.1 alinea los schemas con JSON Schema 2020-12; la nulabilidad se expresa como `type: [string, "null"]` (el `nullable: true` de 3.0 ya no aplica). `[S21]`
- **C25** — Schemathesis lee los `securitySchemes` del spec OpenAPI y aplica auth vía `[auth.openapi.<NombreDelScheme>]` (p.ej. `api_key`), soportando `apiKey` para OpenAPI 2.0 y 3.x; extrae `name`/`in` del scheme; sanea valores sensibles en el output por defecto. `[S19][S23]`
- **C26** — El soporte de OpenAPI 3.1 en Schemathesis es experimental (`--experimental=openapi-3.1` o `OPEN_API_3_1.enable()`), inicialmente para validación de respuestas; la generación de datos sigue el modelo 3.0. `[S20]`
- **C27** — El contract testing verifica que el servidor real cumpla el contrato (conformidad de status codes y schemas de respuesta, content-type); checks como `status_code_conformance` y `positive_data_acceptance` permiten declarar los códigos esperados (p.ej. 2xx/401/403/404/409/5xx) para no marcar como fallo comportamientos intencionales. `[S21][S22][S23]`
- **C28** — Remover un campo **requerido** de una respuesta es un breaking change de contrato (detectable con diff tools tipo oasdiff); exponer el hash de una key en respuestas es mala práctica porque el hash es dato interno (tratarlo como hash de contraseña). `[S21][S8]`

---

## 5. Contradicciones, incertidumbre y frescura

- **Fork de diseño header**: las fuentes divergen entre `X-API-Key` (convención dominante: 667 providers, S2; documentada como scheme `apiKey` en OpenAPI, S3) y `Authorization: Bearer`/`ApiKey` (recomendado por S1/S5 por estandarización y redacción en logs). No es una contradicción factual sino una decisión de diseño: la decisión (a) declara el scheme `apiKey` a nivel contrato, compatible con cualquiera de los dos nombres de header; el nombre exacto del header es decisión de producto, no evidencia.
- **Tensión single-active-key vs overlap**: la decisión de producto (b)+(d) (una sola key activa por app; regenerar sobre app con key activa → 409 con revocación explícita) es **más estricta** que el patrón de industria dual/overlap (C14–C16: Stripe 7 días, GitHub tokens paralelos). La evidencia valida create-before-revoke como seguro, pero con una sola key activa no existe ventana de overlap automática: la rotación pasa a ser un flujo explícito de dos pasos (revocar → regenerar) que el cliente del API debe ejecutar. Riesgo operativo documentado, no contradicción de evidencia.
- **Incertidumbre**:
  - Código exacto para key válida pero app deshabilitada: la semántica RFC 9110 sugiere 403 (C2/C3), pero la práctica de fallar cerrado como "inexistente" tiende a 401 (C22, S11); la decisión (c) elige 403 y es una elección de producto consistente con C3.
  - Métricas de rotación periódica (C18) provienen de una guía de terceros (S15), sin estándar normativo.
  - La afirmación de que SHA-256 sin salt es suficiente (C10) asume keys de alta entropía generadas con CSPRNG; si la generación fuera débil, la premisa se cae (C7 es el prerrequisito).
- **Frescura**: todas las fuentes accedidas el 2026-09-16. OWASP API Security Top 10 2023 es la edición vigente (publicada 2023-07-03). Docs oficiales de Stripe, GitHub y Schemathesis consultadas en su versión actual; el soporte experimental de OpenAPI 3.1 en Schemathesis está marcado como tal en la fuente oficial (S20). Entradas de blog de terceros datadas en 2026.

---

## 6. Decisiones de producto (no autoritativas)

Registradas como contexto retenido (selección de intento), separadas de la evidencia. Son del orquestador, no son evidencia. Se indica el respaldo técnico que la evidencia aporta a cada una (claims):

| # | Decisión | Resuelve | Respaldo de evidencia |
|---|---|---|---|
| a | Guard `require_api_key` reutilizable + `apiKey` en OpenAPI solo a nivel contrato (handlers de `/telemetry/*` en #37) | D1 | C6 (declaración `apiKey` en OpenAPI), C25 (Schemathesis lee el scheme y aplica auth automáticamente). Nombre exacto del header: fork documentado en §5 (X-API-Key vs Authorization) — decisión de producto. |
| b | Una sola key activa por aplicación (`application.api_token_hash`, SHA-256, prefijo `ilp_`) | D2 | C7 (entropía/CSPRNG), C8 (prefijo), C10 (SHA-256 apropiado para alta entropía), C9/C12 (show-once, comparación timing-safe). La unicidad de key activa es más estricta que el patrón de industria (tensión en §5). |
| c | `is_active` en schemas; app inactiva invalida su key (403) | D3 | C22 (fallar cerrado), C3 (403 para credencial válida sin permiso). Alternativa 401 documentada (C22) — decisión de producto. |
| d | Regenerar key sobre app con key activa → 409 con revocación explícita | D4 | C17 (revocación inmediata ante compromiso), C14 (create-before-revoke como patrón seguro). El 409 materializa la rotación en dos pasos explícitos; sin overlap automático (tensión en §5). |
| e | Aislamiento por binding 1:1 credencial→app (el `app_id` del payload nunca se confía) | D5 | C20 (BOLA/API1: no confiar IDs del payload), C23 (tenant derivado de la credencial autenticada). |
| f | Se retira `api_token_hash` de `ApplicationRead` (ADR-16) | D6 | C28 (el hash es dato interno; exponerlo es mala práctica), C13 (el hash completo es la seguridad; el prefijo es lo único mostrable). Retirar un campo requerido sería breaking (C28) — verificar que no sea requerido en el contrato. |

Estas decisiones resuelven D1–D6 de `exploration.md` (a→D1, b→D2, c→D3, d→D4, e→D5, f→D6). El respaldo técnico externo queda ahora **soportado por claims** (r3).

---

## 7. Estado de recuperación y readiness

- **r2 → r3**: admisión denegada en r2 (runtime sin recargar permisos) → admisión aceptada en r3 (ambas clases ejercitadas). Se completaron RQ1–RQ5 con evidencia fuente verificable (23 sources, 28 claims).
- **Readiness**: evidencia `done` y válida (todos los campos del contrato completos); decisiones a–f confirmadas por el orquestador; artefacto persistido en ambos stores (openspec + Engram, bytes idénticos, revisión r3). `proposal_ready = true` (actualizado en preproposal r3).
- **Pendiente orquestador-owned** (no evidencia): elegir el nombre del header para `require_api_key` (`X-API-Key` convención dominante vs `Authorization: ApiKey` estandarizado — §5).