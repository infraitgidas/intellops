# Brief de la v1 — alcance congelado (M1, 18/12/2026)

**Estado**: propuesta para aprobación del equipo (issue A.2); decisiones de §8.3 resueltas el 23/10/2026.
**Alcance**: fija qué entra en la v1, qué se difiere y qué recortes se permiten. No redefine arquitectura ni implementación.
**Hito**: M1 — Piloto medido y v1 entregada, 18/12/2026.
**Fuentes**: se detallan en §9. Cada afirmación de alcance cita `archivo:línea`; los documentos `.docx` se citan por sección.

---

## 1. Decisión ejecutiva

La v1 es el release que cierra **M1** el **18/12/2026** y clausura la fase **F0** con el **MVP-0 operativo**. No es "todo IntellOps": es un sitio piloto medido con RUM y sondas, una alerta recibida por Telegram y tests ≥ 70 % sobre código real (`IntellOps — Plan de Gestión, Roadmap y EDT.md:91`; `docs/business/plan-gestion-roadmap-edt.md:63,132`; `docs/business/issues-fases-abc.md:9-10,58`).

La definición de producto de referencia para este brief es la del plan raíz: **observabilidad del lado del cliente con dos sensores, RUM (usuarios reales) y sondas sintéticas (disponibilidad medida activamente)** (`IntellOps — Plan de Gestión, Roadmap y EDT.md:21`). Por D7 (resuelta el 23/10/2026), este brief y `docs/brief-v2.md` son los documentos normativos; `docs/brief.md` queda como histórico.

---

## 2. Qué es la v1 y qué no es

| Entrega | Fecha | Criterio de salida | Fuente |
|---|---|---|---|
| **v1 / M1** | 18/12/2026 | Sitio piloto medido con RUM y sondas, demo ante GIDAS, alerta por Telegram, tests ≥ 70 % | `IntellOps — Plan de Gestión, Roadmap y EDT.md:91`; `docs/business/plan-gestion-roadmap-edt.md:63` |
| **MVP-1 / F1** | 01–06/2027 | Producto mínimo viable validado con **SUS > 75** | `gestionProyecto/roadmap/roadmap-producto.md:16`; `docs/business/plan-gestion-roadmap-edt.md:20,133` |
| **M2** | H1 2027 | Detección ML sobre series, dashboard, dataset etiquetado como condición de entrada, ISP/ASN y escenarios multi-paso | `docs/business/plan-gestion-roadmap-edt.md:64`; `docs/business/flujo-github.md:20` |
| **M3** | 2027 | LLM local que explica anomalías (RCA) y líneas de extensión | `docs/business/plan-gestion-roadmap-edt.md:65` |
| **M4** | 2028 | Prototipo inicial y experimentación integrada | `docs/business/plan-gestion-roadmap-edt.md:66` |

**v1.1 no es un hito.** Es la etiqueta que usa B.7 para lo diferido: "Diferible a v1.1" (`docs/business/issues-fases-abc.md:261`). No tiene fecha ni criterio de salida propio.

**No se debe usar SUS > 75 como criterio de la v1.** SUS pertenece a F1/MVP-1 (`gestionProyecto/roadmap/roadmap-producto.md:155`; `docs/business/plan-gestion-roadmap-edt.md:155`). La v1 se aprueba con los criterios de §7, no con una encuesta de usabilidad.

**M0 es la antesala, no la entrega.** La fase A cierra M0 el 13/11/2026 con contratos, ADRs, EDT en issues y el primer dato de punta a punta (`docs/business/issues-fases-abc.md:56`; `docs/business/plan-gestion-roadmap-edt.md:62`). M0 es infraestructura de gestión; M1 es el piloto medido y la v1.

**Advertencia de definición.** El plan raíz ubica la detección ML en M2 y el LLM en M3 (`IntellOps — Plan de Gestión, Roadmap y EDT.md:32-33`), mientras que `docs/business/plan-gestion-roadmap-edt.md:75-83` define el MVP-0 con modelos de IA incluidos y `docs/business/issues-fases-abc.md:211-324,353` programa B.4/B.6/B.11 y un E2E con "AI" en la v1. **D1 (resuelta el 23/10/2026)**: la v1 usa reglas de umbral para alertas; la detección ML se mueve a M2.

---

## 3. Alcance dentro

La tabla distingue **Firme** (entra en la v1), **Fuera de la v1** (diferido a M2 o al backlog de extensión 2027) y **Recortado** (sale de la v1 por una decisión expresa). Las decisiones D1–D10 están resueltas desde el 23/10/2026 (ver §8.3). El estado describe el repositorio al 23/10/2026, no la intención del plan.

| Capacidad | Fase / issue | Hito | Estado real en el repo | Condición |
|---|---|---|---|---|
| Contratos de ingesta, OpenAPI y esquema de datos | A / ISS-S1-02, ISS-S1-04 | M0 | **Implementado**: OpenAPI 3.1 v1.0.0 (`openspec/specs/openapi.yaml:1-4`), esquema inicial de 9 entidades + catálogos (`src/api/infrastructure/db/migrations/versions/0001_initial_schema.py:1-10`), contrato RUM aprobado (`docs/architecture/ContratoIngestaRUM.md:1-12`). Los paths de anomalías, alertas, dashboard y asistente existen en el contrato pero no tienen router implementado (`openspec/specs/openapi.yaml:220-341`). | Firme |
| Auth, multi-tenancy, usuarios y aplicaciones | A / ISS-S2-01, ISS-S2-02 | M0 | **Implementado**: routers de auth, users, applications, telemetry y metrics (`src/api/main.py:91-95`); API keys y redacción de secretos (`CHANGELOG.md:23-27`). | Firme |
| Ingesta asíncrona RUM, normalización, sesiones y read path | A / ISS-S2-03, ISS-S3-01, ISS-S3-02, ISS-S3-03 | M0 | **Implementado / Parcial**: `/telemetry/*`, cola en proceso, normalización y `GET /metrics/query|list` (`CHANGELOG.md:28-71`; `src/api/presentation/routers/metrics.py:1-12`). La issue #42 de sesiones sigue abierta (`docs/business/issues-fases-abc.md:45`). | Firme |
| Dataset sintético con anomalías etiquetadas | A.4 | M0 | **Parcial**: hay datos mock y un reader de dataset (`src/ml/pipeline/mock_reader.py`; `src/ml/pipeline/api_reader.py:1-12`), pero no hay generador reproducible con anomalías etiquetadas. | Firme |
| Agente RUM básico (TTFB, FCP, errores JS) | B.1 | M1 | **No existe**: `src/agent/` contiene solo `.gitkeep`; el contrato de ingesta sí está aprobado. | Firme |
| XHR y rage clicks | B.7 | v1.1 | **No existe**: el contrato de métricas ya los nombra (`openspec/specs/openapi.yaml:947`), pero el agente no los captura. | **Recortado de la v1** (D10) |
| Sonda HTTP mínima de disponibilidad desde un origen | B.13 | M1 | **No existe en código versionado**: no hay módulo de sondas en `src/`; el prototipo local `demo/probe_ttfb.py` no está versionado. TLS, DNS y multi-origen quedan en R.4 para 2027 (`docs/business/issues-fases-abc.md:441`). | Firme: sonda HTTP mínima desde un origen (D2) |
| API de lectura de anomalías y alertas | B.3 | M1 | **Parcial**: series y catálogo implementados; `/anomalies` y `/alerts` solo tienen path en el contrato (`openspec/specs/openapi.yaml:220-295`), sin router. | Firme |
| Features, worker de IA, modelos y motor de reglas | B.4, B.6, B.11 | M2 | **Parcial / No existe**: `intellops-ai-engine` es un placeholder (`src/ml/entrypoint.py:1-5`; `openspec/specs/architecture/containers.md:80`); las tablas `ml_model`, `anomaly` y `alert` existen en el esquema (`src/api/infrastructure/db/migrations/versions/0001_initial_schema.py:228-313`), sin lógica. `intellops-ai-engine` sigue existiendo como contenedor, sin lógica de detección en v1. | **Fuera de la v1** → M2 (D1) |
| SPA React con dos vistas (latencias RUM y heatmap UX) | B.5 | M1 | **No existe en código versionado**: `src/frontend/` contiene solo `.gitkeep`; `demo/mini-viewer.html` es un visor local no versionado, no las dos vistas. La SPA no es un contenedor del compose (`docs/adr/0010-arquitectura-de-4-contenedores.md:39`). | Firme (D10); el recorte es B.7 |
| Notificaciones por mail y Telegram | B.10 | M1 | **No existe**: `intellops-comms` es un placeholder (`src/comms/entrypoint.py:1-5`; `openspec/specs/architecture/containers.md:95`). | Firme |
| Tests ≥ 70 % y quality gates | A / ISS-S3-06, B.9 | M0 / M1 | **Parcial**: gate `fail_under = 70` (`pyproject.toml:59`), CI con lint 9.0 y contrato (`.github/workflows/ci.yml:41,129-159`); la issue #45 sigue abierta. | Firme |
| E2E, carga con k6 y piloto medido | C.1, C.2, C.3 | M1 | **No existe**: no hay suite E2E, escenario k6 ni agente instalado en el piloto. El compose de 4 contenedores sí existe (`docker-compose.yml:1-10`). | Firme |
| Release v1.0.0 | C.5 | M1 | **Parcial**: compose operativo; no hay tag `v1.0.0` ni guía de despliegue (`CHANGELOG.md:8`). | Firme |
| Lynis, hardening CIS y pipeline GLP de seguridad | B.2, B.8, B.12 | Backlog 2027 | **No existe / Parcial**: el plan raíz los saca del camino crítico (`IntellOps — Plan de Gestión, Roadmap y EDT.md:35`); el catálogo los mantenía en fase B (`docs/business/issues-fases-abc.md:182-194,270-282,326-340`). La PPS de seguridad de Federico cerró el 19/10/2026. | **Fuera de la v1** → backlog de extensión 2027 (D3) |

**Nota de estado.** No se computan como capacidad entregada los prototipos locales no versionados de `demo/` (`probe_ttfb.py`, `mini-viewer.html`): no están en `origin/develop`.

**Lectura de la tabla.** Lo "Firme" es lo que no puede faltar para que M1 signifique lo que el plan raíz promete. Lo "Fuera de la v1" tiene hito posterior o backlog de extensión. Lo "Recortado" sale por decisión expresa, con el impacto de §6.

---

## 4. Fuera de alcance

Queda fuera de la v1 todo lo que el plan raíz asigna a M2–M4 o al backlog post-v1. Reincorporar un ítem exige cambiar el hito, no solo abrir una issue.

### 4.1. Backlog post-v1 R.1–R.11

| Grupo | Ítems | Fuente |
|---|---|---|
| Operación y datos | R.1 piloto en operación continua; R.2 dataset real y etiquetado; R.3 nueva cohorte; R.7 reentrenamiento y User Health Score | `docs/business/issues-fases-abc.md:438-444` |
| Capacidades | R.4 sondas sintéticas 2027; R.5 ISP/hosting; R.6 alertas por sensibilidad; R.8 LLM local; R.9 escenarios multi-paso y 3 sitios | `docs/business/issues-fases-abc.md:441-446` |
| Cierre | R.10 release v2.0 y SUS; R.11 paper, oferta de extensión y handover | `docs/business/issues-fases-abc.md:447-448` |

R.1–R.11 no se publican hasta que se confirme la continuidad y la nueva cohorte (`docs/business/issues-fases-abc.md:450-452`). R.4 se usa solo como referencia de planificación para TLS, DNS y multi-origen: la sonda HTTP mínima desde un origen sí entra en la v1 (B.13, D2).

### 4.2. Excluido por arquitectura o por recursos

- **LSTM, Kafka y Redis**: fuera del camino crítico y del MVP (`IntellOps — Plan de Gestión, Roadmap y EDT.md:35`; `docs/brief-v2.md:139-140`).
- **OTel Collector, Tempo, Prometheus, Alertmanager, Netdata, Grafana/Loki como contenedores del producto**: roadmap post-MVP; el compose del producto es de 4 contenedores (`docs/adr/0010-arquitectura-de-4-contenedores.md:41`; `openspec/specs/architecture/containers.md:8-11`).
- **Stack LGTM de 13 contenedores**: reemplazado por el diseño de 4 (`docs/adr/0010-arquitectura-de-4-contenedores.md:8`).
- **TimescaleDB inicial**: PostgreSQL 16 es suficiente (`docs/brief-v2.md:141`).
- **LLM local, RCA y RAG**: M3 / R.8 (`IntellOps — Plan de Gestión, Roadmap y EDT.md:33`; `docs/business/issues-fases-abc.md:445`).
- **ISP/ASN y escenarios multi-paso**: M2 (`IntellOps — Plan de Gestión, Roadmap y EDT.md:30-31`).
- **App móvil, integración con Jira/ServiceNow y logs no estructurados**: fuera del alcance inicial (`docs/brief-v2.md:141-146`).
- **Oferta de extensión de seguridad (Lynis, CIS)**: línea de extensión desde M3, no producto de la v1 (`IntellOps — Plan de Gestión, Roadmap y EDT.md:126`).

### 4.3. Trabajo de seguridad: excepción conflictiva

El plan raíz manda explícitamente la auditoría Lynis, el hardening CIS y el pipeline de logs de seguridad **fuera del camino crítico** (`IntellOps — Plan de Gestión, Roadmap y EDT.md:13,35`). El catálogo A/B/C los incluía en la fase B: B.2 (Lynis), B.8 (CIS, prioridad **CRÍTICA**) y B.12 (GLP) (`docs/business/issues-fases-abc.md:182-194,270-282,326-340`). **D3 (resuelta el 23/10/2026)**: B.2, B.8 y B.12 salen de la v1 y pasan al backlog de extensión 2027. La PPS de seguridad de Federico cerró el 19/10/2026, por lo que estas tareas ya no condicionan una aprobación académica.

---

## 5. Criterios de aprobación

### 5.1. Aclaración: PPS no es frente

El criterio A.2 dice "Criterios de aprobación por PPS (F1, F2, F3) y por frente" (`docs/business/issues-fases-abc.md:118`). Es una confusión de nombres: **F1, F2 y F3 son frentes de trabajo**, no PPS (`IntellOps — Plan de Gestión, Roadmap y EDT.md:61-66`; `docs/business/flujo-github.md:45-54`). Las **PPS** son tres entregas académicas individuales de **200 h** con actividades **A1–A7** (`docs/business/plan-gestion-roadmap-edt.md:100-101`). Se escriben por separado: §5.2 por persona/PPS y §5.3 por frente.

### 5.2. Criterios por PPS / persona

Cada PPS se aprueba contra su propio plan de 200 h y su DoD, no contra el hito M1. Las fechas de cierre son anteriores a la v1: Romeo 18/09/2026; Federico y Santiago 19/10/2026 (`docs/business/plan-gestion-roadmap-edt.md:127-128`).

| PPS / persona | Actividades A1–A7 (horas) | DoD de aprobación | Relación con la v1 |
|---|---|---|---|
| **Federico — M-SEG** (01/06–19/10/2026) | A1 30 · A2 25 · A3 35 · A4 55 · A5 40 · A6 10 · A7 5 = 200 | Lynis ≥ 70 % antes/después, eventos simulados detectados < 60 s, 4 dashboards versionados, contrato de eventos publicado (`RRHH/Federico Cavallero/PPS2_PlanTrabajo_IntellOps_Blanco_Cavallero_v2.docx`, §10; `temp/Informe_2_Alcance_PPS_y_Actividades_por_Integrante_IntellOps.docx`, Propuesta A) | Su PPS es seguridad; la captura RUM queda explícitamente fuera de su PPS (Informe 2, Propuesta A, "Qué queda afuera"). La v1 le asigna F1 Captura: **el trabajo de v1 no puede ser condición de aprobación de su PPS**. |
| **Santiago — M-QA** (01/06–19/10/2026) | A1 30 · A2 25 · A3 35 · A4 55 · A5 40 · A6 10 · A7 5 = 200 | Coverage ≥ 70 %, pipeline verde < 10 min, gates bloqueantes, ≥ 3 escenarios E2E, informe de carga (`RRHH/Santiago Montanari/PPS2_PlanTrabajo_IntellOps_Montanari_v2.docx`, §10; Informe 2, Propuesta C) | Su PPS de QA se alinea con B.9/C.3, pero el cierre académico (19/10) es anterior a la v1 (18/12). La aprobación se basa en la evidencia de su ventana, no en el release. |
| **Romeo — M-ML V-06** (04/05–18/09/2026) | A1 30 · A2 25 · A3 40 · A4 50 · A5 35 · A6 10 · A7 10 = 200 | Worker asíncrono, comparación IF vs. LSTM/Prophet, F1 ≥ 0.70, health score con r > 0.75, motor de reglas, 3 vistas, tasa de falsos positivos (`temp/PPS/especificaci_n_de_entregables_pps_v_06.md:13-52`; `RRHH/Romeo Monfroglio/PPS2_PlanTrabajo_IntellOps_V06_2026.docx`, §10) | Su PPS incluye health score y dashboard; la v1 difiere el health score a R.7 (2027) (`docs/business/issues-fases-abc.md:444`). Ver D6. |

**Regla de aprobación:** una PPS se aprueba con su informe final, su DoD y la evidencia de sus A1–A7. No se aprueba por haber contribuido a M1, y M1 no se aprueba por tener las PPS cerradas.

### 5.3. Criterios por frente

| Frente | Dueño / respaldo | Criterio de aceptación de la v1 | Evidencia |
|---|---|---|---|
| **F1 Captura** | Federico / Romeo | Agente RUM con TTFB, FCP y errores JS, bundle < 30 KB; B.7 (XHR y rage clicks) recortado a v1.1; sonda HTTP mínima desde un origen; agente instalado en el piloto | `IntellOps — Plan de Gestión, Roadmap y EDT.md:63,87-91`; `docs/business/issues-fases-abc.md:166-180,368-373` |
| **F2 Plataforma** | Santiago / Federico | 4 contenedores operativos; ingesta ≤ 500 ms; telemetría persistida y consultable; API de lectura; alerta despachada por Telegram; gate de cobertura; release `v1.0.0` | `IntellOps — Plan de Gestión, Roadmap y EDT.md:64,88-91`; `docs/adr/0010-arquitectura-de-4-contenedores.md:24-41`; `docs/business/issues-fases-abc.md:196-209,284-310,375-416` |
| **F3 Inteligencia** | Romeo / Santiago | Dataset etiquetado; regla de umbral con severidad y confidence; evaluación de falsos positivos. La selección de modelo con F1/precisión/recall pertenece a M2 (D1) | `IntellOps — Plan de Gestión, Roadmap y EDT.md:65,89-91`; `docs/business/issues-fases-abc.md:140-153,211-254,312-324,389-401` |

### 5.4. Condiciones transversales de M1

- Demo de punta a punta ante GIDAS y handovers al día (`IntellOps — Plan de Gestión, Roadmap y EDT.md:91`).
- Tests ≥ 70 % sobre código real (`IntellOps — Plan de Gestión, Roadmap y EDT.md:141`).
- Ninguna persona aprueba su propio PR; se exige 1 aprobación de otro frente (`docs/business/flujo-github.md:74`).
- Toda issue del sprint tiene un milestone y un frente (`docs/business/flujo-github.md:24,47`).

---

## 6. Recortes permitidos y su impacto

El orden es normativo: se corta primero lo que menos afecta la promesa de M1. No se puede cortar un ítem "Firme" de §3 sin redefinir M1.

1. **B.7 — XHR y rage clicks (recorte confirmado).** Es la única tarea marcada "Diferible a v1.1" y "la primera que se recorta" (`docs/business/issues-fases-abc.md:261-263`). **D10 (resuelta el 23/10/2026)** lo confirma como recorte de la v1. Impacto: se pierden 2 de las 5 métricas RUM del contrato (`openspec/specs/openapi.yaml:947`), pero quedan TTFB, FCP y errores JS. M1 sigue en pie si el resto se cumple; el plan raíz ya prevé diferirlos antes de mover M1 (`IntellOps — Plan de Gestión, Roadmap y EDT.md:93`). No afecta la aprobación de ninguna PPS: la de Federico es de seguridad y la de Romeo excluye RUM.
2. **B.5 — SPA React (se mantiene).** **D10 (resuelta el 23/10/2026)** mantiene B.5 en la v1: es dependencia de C.1 (`docs/business/issues-fases-abc.md:228-239,350`) y sostiene la demo visual de las 3 vistas. El recorte confirmado es B.7, no B.5.
3. **B.2, B.8 y B.12 — seguridad (fuera de la v1).** **D3 (resuelta el 23/10/2026)** los retira de la v1 y los pasa al backlog de extensión 2027. Impacto: la v1 no incluye hardening CIS ni evidencia GLP, pero el flujo RUM → alerta no se afecta. B.8 estaba marcada **CRÍTICA** en el catálogo (`docs/business/issues-fases-abc.md:275`), así que las issues se actualizan con su nuevo estado y milestone. La PPS de Federico ya está cerrada y no depende de la v1.
4. **No recortables sin redefinir M1:** sonda HTTP mínima de disponibilidad (D2; `IntellOps — Plan de Gestión, Roadmap y EDT.md:25,90`), alerta por Telegram (`IntellOps — Plan de Gestión, Roadmap y EDT.md:90-91`), piloto medido (`docs/business/issues-fases-abc.md:366-373`), tests ≥ 70 % (`IntellOps — Plan de Gestión, Roadmap y EDT.md:91`) y flujo E2E (`docs/business/issues-fases-abc.md:353`). Si cualquiera se cae, M1 deja de significar lo que el plan raíz promete y la dirección debe aprobar un hito nuevo.
5. **B.4, B.6 y B.11 no son recortes: están fuera de la v1 por D1.** La detección ML se mueve a M2. El paso "AI" del E2E se reemplaza por una regla de umbral, y C.1 se actualiza en consecuencia.

---

## 7. Métricas de éxito de la v1

No son las métricas de MVP-1. SUS y la validación con 4 personas pertenecen a F1/2027 (`gestionProyecto/roadmap/roadmap-producto.md:155`).

| Métrica | Umbral | Verificación | Fuente |
|---|---|---|---|
| Cobertura de tests sobre código real | ≥ 70 % | `pytest --cov=src`; gate `fail_under` | `IntellOps — Plan de Gestión, Roadmap y EDT.md:141`; `pyproject.toml:59` |
| Latencia de ingesta bajo carga estándar | ≤ 500 ms | Escenario k6 versionado | `docs/business/issues-fases-abc.md:386`; `gestionProyecto/marco/04-especificaciones.md:110` |
| Flujo E2E | agente → ingesta → PostgreSQL → regla de umbral → alerta → notificación | Smoke test documentado en `develop` | `docs/business/issues-fases-abc.md:353` |
| Alerta recibida por Telegram | 1 alerta ante anomalía inyectada | Evidencia de recepción en el canal | `IntellOps — Plan de Gestión, Roadmap y EDT.md:90-91`; `docs/business/issues-fases-abc.md:306` |
| Sitio piloto medido con RUM | Datos visibles en ingesta y dashboard | Evidencia de operación | `docs/business/issues-fases-abc.md:366-373`; `IntellOps — Plan de Gestión, Roadmap y EDT.md:90` |
| Demo de cierre ante GIDAS | 1 demo de punta a punta | Revisión de M1 | `IntellOps — Plan de Gestión, Roadmap y EDT.md:91` |
| Compose de release | `docker compose up` en máquina limpia | Smoke test post-deploy | `docs/business/issues-fases-abc.md:413`; `docs/adr/0010-arquitectura-de-4-contenedores.md:24-31` |
| F1 de detección (M2; no aplica a la v1) | ≥ 0.70 | Dataset de validación | `docs/business/issues-fases-abc.md:251`; `gestionProyecto/marco/04-especificaciones.md:62` |

---

## 8. Supuestos, dependencias externas y decisiones de alcance

### 8.1. Supuestos

- Tres integrantes con 10 h semanales hasta M1; 60 h por sprint (`IntellOps — Plan de Gestión, Roadmap y EDT.md:93`). **No está confirmada la continuidad** después del cierre de las PPS (18/09 y 19/10) hasta el 18/12.
- Receso en enero y febrero, con el piloto generando datos (`IntellOps — Plan de Gestión, Roadmap y EDT.md:123,128`).
- VM Rocky 10, CPU-only, < 2 GB de RAM y costo $0/mes (`docs/adr/0010-arquitectura-de-4-contenedores.md:18`).
- Sitio piloto definido antes del 04/12/2026 (`docs/business/issues-fases-abc.md:369`).
- Un origen para la sonda HTTP mínima de la v1; el multi-origen queda en R.4 para 2027 (`IntellOps — Plan de Gestión, Roadmap y EDT.md:37,150`).
- Credenciales de Telegram y correo disponibles; secretos por variables de entorno (`docs/business/issues-fases-abc.md:309`).

### 8.2. Dependencias externas

- Autorización y consentimiento del sitio piloto (`docs/business/issues-fases-abc.md:366-372`).
- Telegram Bot API y proveedor de correo (`docs/business/issues-fases-abc.md:306-309`).
- GitHub Actions y token `gh` con scope `project` para el tablero (`docs/business/flujo-github.md:88-90`).
- Free-tier cloud o segunda red para el origen secundario de sondas: no aplica a la v1, queda en R.4 (`IntellOps — Plan de Gestión, Roadmap y EDT.md:37`).
- Calendario académico: el supuesto de receso y de reanudación en marzo desplaza M2/M3 (`IntellOps — Plan de Gestión, Roadmap y EDT.md:128`).
- Licencia de ASN/geolocalización: no aplica a la v1, se verifica antes de M2 (`IntellOps — Plan de Gestión, Roadmap y EDT.md:151`).

### 8.3. Decisiones resueltas (23/10/2026)

| ID | Decisión | Consecuencia |
|---|---|---|
| **D1** | La v1 usa reglas de umbral para alertas; la detección ML (B.4, B.6, B.11) se mueve a M2. El criterio de salida de M1 no incluye ML; M2 sí. `intellops-ai-engine` sigue existiendo como contenedor, sin lógica de detección en v1. | B.4, B.6 y B.11 salen de la v1. El paso "AI" del E2E se reemplaza por una regla de umbral y C.1 se actualiza. |
| **D2** | La v1 incluye una sonda HTTP mínima de disponibilidad desde un solo origen. TLS, DNS y multi-origen pasan a 2027 (R.4). Se crea la issue B.13. | Se suma B.13 a la fase B; R.4 queda como referencia para TLS, DNS y multi-origen. |
| **D3** | Lynis (B.2), hardening CIS (B.8) y dashboards GLP (B.12) salen de la v1 y pasan al backlog de extensión 2027. El plan raíz los saca del camino crítico; la PPS de seguridad de Federico cerró el 19/10/2026. | B.2, B.8 y B.12 dejan de bloquear M1 y se actualizan con su nuevo estado y milestone. |
| **D4** | El despacho de alertas lo hace `intellops-comms` según ADR-0010; Alertmanager no entra en la v1. | El canal de alertas se implementa sin un servicio adicional; Alertmanager queda en el roadmap. |
| **D5** | C.6 deja de ser "informes finales de PPS" y pasa a ser "Informe de cierre de la v1". Las PPS cerraron el 18/09 y el 19/10/2026. | C.6 se renombra y sus criterios pasan a evidencia del release y del piloto, no a entregables académicos. |
| **D6** | El health score no entra en la v1; queda en R.7 (2027). | La v1 no incluye modelo, endpoint ni datos de health score. |
| **D7** | Son normativos `docs/business/brief-v1.md` y `docs/brief-v2.md`. `docs/brief.md` queda como histórico. | Se agrega la nota de estado en `docs/brief.md` y se elimina la ambigüedad de precedencia. |
| **D8** | Se acepta la divergencia entre los planes PPS2 y el repo; se documenta en los informes finales, sin reescribir los planes PPS2 de forma retroactiva. | La divergencia queda como evidencia en los informes de cierre, no como cambio de los planes aprobados. |
| **D9** | `openspec/specs/architecture/spec.md` se corrige: la base de datos es PostgreSQL 16 (ADR-0009), no SQLite. | La tabla de decisiones arquitectónicas deja de contradecir ADR-0009 y ADR-0010. |
| **D10** | B.5 (SPA) se mantiene en la v1. B.7 (XHR y rage clicks) es el recorte confirmado. | B.5 sigue siendo dependencia de C.1; B.7 queda en v1.1. |

---

## 9. Referencias

- `IntellOps — Plan de Gestión, Roadmap y EDT.md` — plan raíz de la dirección; alcance, hitos, frentes, cronograma y decisiones.
- `docs/business/plan-gestion-roadmap-edt.md` — mapeo F0–F4 / M0–M4, PPS, indicadores, riesgos y GAPS.
- `docs/business/issues-fases-abc.md` — catálogo A/B/C/R; A.2 y criterios de recorte.
- `docs/business/EDT intellops.md` — EDT operativo de 8 sprints.
- `docs/business/issues-s1-s2.md` y `docs/business/issues-s2-s3.md` — catálogos S1–S3 y estado de publicación.
- `docs/business/flujo-github.md` — milestones, etiquetas y flujo vigentes desde el 23/10/2026.
- `docs/brief.md` — brief v2.0 de mayor recurso (TimescaleDB, LSTM, 8 GB); **histórico** desde D7 (23/10/2026).
- `docs/brief-v2.md` — brief redefinido para recursos escasos.
- `docs/project-brief.md` — **existe pero está vacío (0 bytes)**; no se usó como fuente.
- `gestionProyecto/roadmap/roadmap-producto.md` — fases F0–F4, KPIs y riesgos.
- `gestionProyecto/roadmap/roadmap-mvp-pps.md` — acotamiento del MVP a las PPS y DoD por módulo.
- `gestionProyecto/marco/03-diseno.md` y `gestionProyecto/marco/04-especificaciones.md` — diseño y requisitos de sistema.
- `docs/adr/0010-arquitectura-de-4-contenedores.md` — arquitectura vigente del MVP.
- `openspec/specs/architecture/containers.md`, `openspec/specs/architecture/spec.md` y `openspec/specs/openapi.yaml` — estado del contrato y de la arquitectura.
- `docs/architecture/ContratoIngestaRUM.md` — contrato de ingesta RUM aprobado.
- `temp/PPS/especificaci_n_de_entregables_pps_v_06.md` — entregables y DoD de la PPS de Romeo.
- `temp/Informe_2_Alcance_PPS_y_Actividades_por_Integrante_IntellOps.docx` — alcance y A1–A7 de las tres PPS.
- `RRHH/Federico Cavallero/PPS2_PlanTrabajo_IntellOps_Blanco_Cavallero_v2.docx`, `RRHH/Santiago Montanari/PPS2_PlanTrabajo_IntellOps_Montanari_v2.docx` y `RRHH/Romeo Monfroglio/PPS2_PlanTrabajo_IntellOps_V06_2026.docx` — planes PPS2.
- `README.md` y `CHANGELOG.md` — estado implementado y deuda declarada.
- `docker-compose.yml`, `pyproject.toml` y `.github/workflows/ci.yml` — compose, gate de cobertura y CI.
