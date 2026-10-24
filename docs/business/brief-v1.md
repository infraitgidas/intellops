# Brief de la v1 — alcance congelado (entrega en M2, 18/12/2026)

**Estado**: propuesta para aprobación del equipo (issue A.2); las decisiones de §8.3 (23/10/2026) y §8.4 (24/10/2026) son **propuestas** pendientes de acuerdo.
**Alcance**: fija qué entra en la v1, qué se difiere y qué recortes se permiten. No redefine arquitectura ni implementación.
**Hitos**: el alcance se congela en **M1 — Feature freeze v1 (04/12/2026)** y la v1 se entrega en **M2 — Entrega MVP v1 (18/12/2026)**.
**Fuentes**: se detallan en §9. Cada afirmación de alcance cita `archivo:línea` o `archivo §sección`; los documentos `.docx` se citan por sección.

---

## 1. Decisión ejecutiva

La v1 es el release que cierra **M2** el **18/12/2026**, con el alcance congelado en **M1** el **04/12/2026**, y clausura la fase **F0** con el **MVP-0 operativo**. No es "todo IntellOps": es un sitio piloto medido con RUM y sondas, una alerta recibida por Telegram y tests ≥ 70 % sobre código real (`docs/business/fuentes/plan-raiz-roadmap-edt.md:91`; `docs/business/fuentes/plan-integral-gantt-v1.0.pdf`, §hitos; `docs/business/plan-gestion-roadmap-edt.md §3, §6.2`; `docs/business/issues-fases-abc.md §1.2, §4`).

La definición de producto de referencia para este brief es la del plan raíz: **observabilidad del lado del cliente con dos sensores, RUM (usuarios reales) y sondas sintéticas (disponibilidad medida activamente)** (`docs/business/fuentes/plan-raiz-roadmap-edt.md:21`). Por D7 (resuelta el 23/10/2026), este brief y `docs/brief-v2.md` son los documentos normativos; `docs/brief.md` queda como histórico.

---

## 2. Qué es la v1 y qué no es

| Entrega | Fecha | Criterio de salida | Fuente |
|---|---|---|---|
| **M1 — Feature freeze v1** | 04/12/2026 | Todas las funciones de la v1 integradas en `develop`; el alcance queda cerrado | `docs/business/fuentes/plan-integral-gantt-v1.0.pdf`, §hitos |
| **M2 — Entrega MVP v1 (v1)** | 18/12/2026 | Sitio piloto medido con RUM y sondas, demo ante GIDAS, alerta por Telegram, tests ≥ 70 % e informes finales de PPS | `docs/business/fuentes/plan-raiz-roadmap-edt.md:91`; `docs/business/fuentes/plan-integral-gantt-v1.0.pdf`, §hitos; `docs/business/plan-gestion-roadmap-edt.md §3` |
| **M3 — v1.1** | 16/04/2027 | Detección ML sobre datos reales, sondas TLS/DNS/multi-origen, ISP/ASN y User Health Score | `docs/business/fuentes/plan-integral-gantt-v1.0.pdf`, §hitos y R.4–R.7 |
| **M4 — v2.0** | 11/06/2027 | LLM local RCA, 3 sitios piloto, prueba SUS, paper y oferta de extensión | `docs/business/fuentes/plan-integral-gantt-v1.0.pdf`, §hitos y R.8–R.11 |
| **MVP-1 / F1** | 01–06/2027 | Producto mínimo viable validado con **SUS > 75** | `gestionProyecto/roadmap/roadmap-producto.md:16`; `docs/business/plan-gestion-roadmap-edt.md §1, §6.2` |

**El prototipo 2027–2028 queda como extensión post-v2.0**, fuera de la secuencia M0–M4 (`docs/business/fuentes/plan-integral-gantt-v1.0.pdf`, §Después de la v1).

**v1.1 ahora es el hito M3.** Es la etiqueta que usa B.7 para lo diferido ("Diferible a v1.1", `docs/business/issues-fases-abc.md §4 B.7`) y, desde D11 (24/10/2026), coincide con **M3 — v1.1 (16/04/2027)**: detección ML sobre datos reales, sondas TLS/DNS/multi-origen, ISP/ASN y Health Score. Recibe también B.4, B.6 y B.11 (D1).

**No se debe usar SUS > 75 como criterio de la v1.** SUS pertenece a F1/MVP-1 (`gestionProyecto/roadmap/roadmap-producto.md:155`; `docs/business/plan-gestion-roadmap-edt.md §7`). La v1 se aprueba con los criterios de §7, no con una encuesta de usabilidad.

**M0 es la antesala, no la entrega.** La fase A cierra M0 el 13/11/2026 con contratos, ADRs, EDT en issues y el primer dato de punta a punta (`docs/business/issues-fases-abc.md §1.2`; `docs/business/plan-gestion-roadmap-edt.md §3`). M0 es infraestructura de gestión, M1 el feature freeze (04/12) y M2 la entrega (18/12).

**Advertencia de definición.** El plan raíz usa la numeración anterior —detección ML en M2 y LLM en M3 (`docs/business/fuentes/plan-raiz-roadmap-edt.md:32-33`)—, mientras que el Gantt v1.0 ubica la detección ML en M3 y el LLM en M4 (`docs/business/fuentes/plan-integral-gantt-v1.0.pdf`, §hitos). **D11 (24/10/2026)** adopta la numeración del Gantt. Además, `docs/business/plan-gestion-roadmap-edt.md §4` define el MVP-0 con modelos de IA y `docs/business/issues-fases-abc.md §4–§5` programa B.4/B.6/B.11 en la v1. **D1 (propuesta del 23/10/2026)**: la v1 usa reglas de umbral para alertas (B.14); la detección ML (B.4, B.6, B.11) se mueve a M3.

---

## 3. Alcance dentro

La tabla distingue **Firme** (entra en la v1), **Fuera de la v1** (diferido a M3–M4 o al backlog de extensión 2027) y **Recortado** (sale de la v1 por una decisión expresa). Las decisiones D1–D13 son propuestas del equipo (ver §8.3 y §8.4) y se aplican como base de trabajo hasta su ratificación. El estado describe el repositorio al 23/10/2026, no la intención del plan.

| Capacidad | Fase / issue | Hito | Estado real en el repo | Condición |
|---|---|---|---|---|
| Contratos de ingesta, OpenAPI y esquema de datos | A / ISS-S1-02, ISS-S1-04 | M0 | **Implementado**: OpenAPI 3.1 v1.0.0 (`openspec/specs/openapi.yaml:1-4`), esquema inicial de 9 entidades + catálogos (`src/api/infrastructure/db/migrations/versions/0001_initial_schema.py:1-10`), contrato RUM aprobado (`docs/architecture/ContratoIngestaRUM.md:1-12`). Los paths de anomalías, alertas, dashboard y asistente existen en el contrato pero no tienen router implementado (`openspec/specs/openapi.yaml:220-341`). | Firme |
| Auth, multi-tenancy, usuarios y aplicaciones | A / ISS-S2-01, ISS-S2-02 | M0 | **Implementado**: routers de auth, users, applications, telemetry y metrics (`src/api/main.py:91-95`); API keys y redacción de secretos (`CHANGELOG.md:23-27`). | Firme |
| Ingesta asíncrona RUM, normalización, sesiones y read path | A / ISS-S2-03, ISS-S3-01, ISS-S3-02, ISS-S3-03 | M0 | **Implementado / Parcial**: `/telemetry/*`, cola en proceso, normalización y `GET /metrics/query` y `GET /metrics/list` (`CHANGELOG.md:28-71`; `src/api/presentation/routers/metrics.py:1-12`). La issue #42 de sesiones sigue abierta (`docs/business/issues-fases-abc.md §1.1`). | Firme |
| Dataset sintético con anomalías etiquetadas | A.4 | M0 | **Parcial**: hay datos mock y un reader de dataset (`src/ml/pipeline/mock_reader.py`; `src/ml/pipeline/api_reader.py:1-12`), pero no hay generador reproducible con anomalías etiquetadas. | Firme |
| Agente RUM básico (TTFB, FCP, errores JS) | B.1 | M1 | **No existe**: `src/agent/` contiene solo `.gitkeep`; el contrato de ingesta sí está aprobado. | Firme |
| XHR y rage clicks | B.7 | M3 (v1.1) | **No existe**: el contrato de métricas ya los nombra (`openspec/specs/openapi.yaml:947`), pero el agente no los captura. | **Recortado de la v1** (D10) |
| Sonda HTTP mínima de disponibilidad desde un origen | B.13 | M1 | **No existe en código versionado**: no hay módulo de sondas en `src/`; el prototipo local de sonda no está versionado. TLS, DNS y multi-origen quedan en R.4 para M3 (`docs/business/issues-fases-abc.md §6 R.4`). | Firme: sonda HTTP mínima desde un origen (D2) |
| API de lectura de anomalías y alertas | B.3 | M1 | **Parcial**: series y catálogo implementados; `/anomalies` y `/alerts` solo tienen path en el contrato (`openspec/specs/openapi.yaml:220-295`), sin router. | Firme |
| Features, worker de IA, modelos y motor de reglas | B.4, B.6, B.11 | M3 (v1.1) | **Parcial / No existe**: `intellops-ai-engine` es un placeholder (`src/ml/entrypoint.py:1-5`; `openspec/specs/architecture/containers.md:80`); las tablas `ml_model`, `anomaly` y `alert` existen en el esquema (`src/api/infrastructure/db/migrations/versions/0001_initial_schema.py:228-313`), sin lógica. `intellops-ai-engine` sigue existiendo como contenedor, sin lógica de detección en v1. | **Fuera de la v1** → M3 (D1) |
| SPA React con dos vistas (latencias RUM y heatmap UX) | B.5 | M1 | **No existe en código versionado**: `src/frontend/` contiene solo `.gitkeep`; el visor local es un prototipo no versionado, no las dos vistas. La SPA no es un contenedor del compose (`docs/adr/0010-arquitectura-de-4-contenedores.md:39`). | Firme (D10); el recorte es B.7 |
| Notificaciones por mail y Telegram | B.10 | M1 | **No existe**: `intellops-comms` es un placeholder (`src/comms/entrypoint.py:1-5`; `openspec/specs/architecture/containers.md:95`). | Firme |
| Tests ≥ 70 % y quality gates | A / ISS-S3-06, B.9 | M0 / M1 | **Parcial**: gate `fail_under = 70` (`pyproject.toml:59`), CI con lint 9.0 y contrato (`.github/workflows/ci.yml:41,129-159`); la issue #45 sigue abierta. | Firme |
| E2E, carga con k6 y piloto medido | C.1, C.2, C.3 | M2 | **No existe**: no hay suite E2E, escenario k6 ni agente instalado en el piloto. El compose de 4 contenedores sí existe (`docker-compose.yml:1-10`). | Firme |
| Release v1.0.0 | C.5 | M2 | **Parcial**: compose operativo; no hay tag `v1.0.0` ni guía de despliegue (`CHANGELOG.md:8`). | Firme |
| Lynis, hardening CIS y pipeline GLP de seguridad | B.2, B.8, B.12 | Extensión 2027 (sin hito) | **No existe / Parcial**: el plan raíz los saca del camino crítico (`docs/business/fuentes/plan-raiz-roadmap-edt.md:35`); el catálogo los mantenía en fase B (`docs/business/issues-fases-abc.md §4 B.2, B.8, B.12`). La PPS de seguridad de Federico cerró el 19/10/2026. | **Fuera de la v1** → backlog de extensión 2027 (D3) |

**Nota de estado.** No se computan como capacidad entregada los prototipos locales no versionados (`probe_ttfb.py`, `mini-viewer.html`): no están en `origin/develop`.

**Lectura de la tabla.** Lo "Firme" es lo que no puede faltar para que M2 signifique lo que el plan raíz promete. Lo "Fuera de la v1" tiene hito posterior o backlog de extensión. Lo "Recortado" sale por decisión expresa, con el impacto de §6.

---

## 4. Fuera de alcance

Queda fuera de la v1 todo lo que el plan raíz asigna a M3–M4 o al backlog post-v1. Reincorporar un ítem exige cambiar el hito, no solo abrir una issue.

### 4.1. Backlog post-v1 R.1–R.11

| Grupo | Ítems | Fuente |
|---|---|---|
| Operación y datos | R.1 piloto en operación continua; R.2 dataset real y etiquetado; R.3 nueva cohorte; R.7 reentrenamiento y User Health Score | `docs/business/issues-fases-abc.md §6 R.1–R.7` |
| Capacidades | R.4 sondas sintéticas 2027; R.5 ISP/hosting; R.6 alertas por sensibilidad; R.8 LLM local; R.9 escenarios multi-paso y 3 sitios | `docs/business/issues-fases-abc.md §6 R.4–R.8` |
| Cierre | R.10 release v2.0 y SUS; R.11 paper, oferta de extensión y handover | `docs/business/issues-fases-abc.md §6 R.10–R.11` |

R.1–R.11 no se publican hasta que se confirme la continuidad y la nueva cohorte (`docs/business/issues-fases-abc.md §6`). R.4 pertenece a M3 y se usa como referencia de planificación para TLS, DNS y multi-origen: la sonda HTTP mínima desde un origen sí entra en la v1 (B.13, D2).

### 4.2. Excluido por arquitectura o por recursos

- **LSTM, Kafka y Redis**: fuera del camino crítico y del MVP (`docs/business/fuentes/plan-raiz-roadmap-edt.md:35`; `docs/brief-v2.md:139-140`).
- **OTel Collector, Tempo, Prometheus, Alertmanager, Netdata, Grafana/Loki como contenedores del producto**: roadmap post-MVP; el compose del producto es de 4 contenedores (`docs/adr/0010-arquitectura-de-4-contenedores.md:41`; `openspec/specs/architecture/containers.md:8-11`).
- **Stack LGTM de 13 contenedores**: reemplazado por el diseño de 4 (`docs/adr/0010-arquitectura-de-4-contenedores.md:8`).
- **TimescaleDB inicial**: PostgreSQL 16 es suficiente (`docs/brief-v2.md:141`).
- **LLM local, RCA y RAG**: M4 / R.8 (`docs/business/fuentes/plan-raiz-roadmap-edt.md:33`; `docs/business/issues-fases-abc.md §6 R.8`).
- **ISP/ASN**: M3 / R.5; **escenarios multi-paso y 3 sitios**: M4 / R.9 (`docs/business/fuentes/plan-raiz-roadmap-edt.md:30-31`).
- **App móvil, integración con Jira/ServiceNow y logs no estructurados**: fuera del alcance inicial (`docs/brief-v2.md:141-146`).
- **Oferta de extensión de seguridad (Lynis, CIS)**: línea de extensión desde 2027, fuera de M0–M2 (`docs/business/fuentes/plan-raiz-roadmap-edt.md:126`).

### 4.3. Trabajo de seguridad: excepción conflictiva

El plan raíz manda explícitamente la auditoría Lynis, el hardening CIS y el pipeline de logs de seguridad **fuera del camino crítico** (`docs/business/fuentes/plan-raiz-roadmap-edt.md:13,35`). El catálogo A/B/C los incluía en la fase B: B.2 (Lynis), B.8 (CIS, prioridad **CRÍTICA**) y B.12 (GLP) (`docs/business/issues-fases-abc.md §4 B.2, B.8, B.12`). **D3 (propuesta del 23/10/2026)**: B.2, B.8 y B.12 salen de la v1 y pasan al backlog de extensión 2027, sin milestone en M0–M2. La ventana académica de la PPS de seguridad de Federico cerró el 19/10/2026 y su informe final se entrega con la v1 (C.6), por lo que estas tareas no condicionan la aprobación.

---

## 5. Criterios de aprobación

### 5.1. Aclaración: PPS no es frente

El criterio A.2 dice "Criterios de aprobación por PPS (F1, F2, F3) y por frente" (`docs/business/issues-fases-abc.md §3 A.2`). Es una confusión de nombres: **F1, F2 y F3 son frentes de trabajo**, no PPS (`docs/business/fuentes/plan-raiz-roadmap-edt.md:61-66`; `docs/business/flujo-github.md §2`). Las **PPS** son tres entregas académicas individuales de **200 h** con actividades **A1–A7** (`docs/business/plan-gestion-roadmap-edt.md §5`). Se escriben por separado: §5.2 por persona/PPS y §5.3 por frente.

### 5.2. Criterios por PPS / persona

Cada PPS se aprueba contra su propio plan de 200 h y su DoD, no contra la entrega de la v1. Las ventanas académicas originales cerraron el 18/09/2026 (Romeo) y el 19/10/2026 (Federico y Santiago), pero el Gantt v1.0 reprogramó las actividades de cierre a noviembre y diciembre y fija la entrega de los **informes finales de PPS junto con la v1 el 18/12/2026** (C.6; D13).

| PPS / persona | Actividades A1–A7 (horas) | DoD de aprobación | Relación con la v1 |
|---|---|---|---|
| **Federico — M-SEG** (01/06–19/10/2026; informe final 18/12/2026) | A1 30 · A2 25 · A3 35 · A4 55 · A5 40 · A6 10 · A7 5 = 200 | Lynis ≥ 70 % antes/después, eventos simulados detectados < 60 s, 4 dashboards versionados, contrato de eventos publicado (`RRHH/Federico Cavallero/PPS2_PlanTrabajo_IntellOps_Blanco_Cavallero_v2.docx`, §10; `docs/business/fuentes/pps/informe-2-alcance-pps.docx`, Propuesta A) | Su PPS es seguridad; la captura RUM queda explícitamente fuera de su PPS (Informe 2, Propuesta A, "Qué queda afuera"). La v1 le asigna F1 Captura: **el trabajo de v1 no puede ser condición de aprobación de su PPS**. |
| **Santiago — M-QA** (01/06–19/10/2026; informe final 18/12/2026) | A1 30 · A2 25 · A3 35 · A4 55 · A5 40 · A6 10 · A7 5 = 200 | Coverage ≥ 70 %, pipeline verde < 10 min, gates bloqueantes, ≥ 3 escenarios E2E, informe de carga (`RRHH/Santiago Montanari/PPS2_PlanTrabajo_IntellOps_Montanari_v2.docx`, §10; Informe 2, Propuesta C) | Su PPS de QA se alinea con B.9/C.3, pero el cierre académico (19/10) es anterior a la v1 (18/12). La aprobación se basa en la evidencia de su ventana, no en el release. |
| **Romeo — M-ML V-06** (04/05–18/09/2026; A4–A7 reprogramadas a nov–dic; informe final 18/12/2026) | A1 30 · A2 25 · A3 40 · A4 50 · A5 35 · A6 10 · A7 10 = 200 | Worker asíncrono, comparación IF vs. LSTM/Prophet, F1 ≥ 0.70, health score con r > 0.75, motor de reglas, 3 vistas, tasa de falsos positivos (`docs/business/fuentes/pps/especificacion-entregables-pps-v06.md:13-52`; `RRHH/Romeo Monfroglio/PPS2_PlanTrabajo_IntellOps_V06_2026.docx`, §10) | Su PPS incluye health score y dashboard; la v1 difiere el health score a R.7 (2027) (`docs/business/issues-fases-abc.md §6 R.7`). Ver D6. |

**Regla de aprobación:** una PPS se aprueba con su informe final, su DoD y la evidencia de sus A1–A7. No se aprueba por haber contribuido a la v1, y M2 no se aprueba por tener las PPS cerradas.

### 5.3. Criterios por frente

| Frente | Dueño / respaldo | Criterio de aceptación de la v1 | Evidencia |
|---|---|---|---|
| **F1 Captura** | Federico / Romeo | Agente RUM con TTFB, FCP y errores JS, bundle < 30 KB; B.7 (XHR y rage clicks) recortado a v1.1; sonda HTTP mínima desde un origen; agente instalado en el piloto | `docs/business/fuentes/plan-raiz-roadmap-edt.md:63,87-91`; `docs/business/issues-fases-abc.md §4 B.1, §5 C.2` |
| **F2 Plataforma** | Santiago / Federico | 4 contenedores operativos; ingesta ≤ 500 ms; telemetría persistida y consultable; API de lectura; alerta despachada por Telegram; gate de cobertura; release `v1.0.0` | `docs/business/fuentes/plan-raiz-roadmap-edt.md:64,88-91`; `docs/adr/0010-arquitectura-de-4-contenedores.md:24-41`; `docs/business/issues-fases-abc.md §4–§5` |
| **F3 Inteligencia** | Romeo / Santiago | Dataset etiquetado; regla de umbral con severidad y confidence; evaluación de falsos positivos. La selección de modelo con F1/precisión/recall pertenece a M3 (D1) | `docs/business/fuentes/plan-raiz-roadmap-edt.md:65,89-91`; `docs/business/issues-fases-abc.md §3–§4` |

### 5.4. Condiciones transversales de M2

- Demo de punta a punta ante GIDAS y handovers al día (`docs/business/fuentes/plan-raiz-roadmap-edt.md:91`).
- Tests ≥ 70 % sobre código real (`docs/business/fuentes/plan-raiz-roadmap-edt.md:141`).
- Ninguna persona aprueba su propio PR; se exige 1 aprobación de otro frente (`docs/business/flujo-github.md §3`).
- Toda issue del sprint tiene un milestone y un frente (`docs/business/flujo-github.md §1, §2`).

---

## 6. Recortes permitidos y su impacto

El orden es normativo: se corta primero lo que menos afecta la promesa de M2. No se puede cortar un ítem "Firme" de §3 sin redefinir M2.

1. **B.7 — XHR y rage clicks (recorte confirmado).** Es la única tarea marcada "Diferible a v1.1" y "la primera que se recorta" (`docs/business/issues-fases-abc.md §4 B.7`). **D10 (propuesta del 23/10/2026)** lo confirma como recorte de la v1. Impacto: se pierden 2 de las 5 métricas RUM del contrato (`openspec/specs/openapi.yaml:947`), pero quedan TTFB, FCP y errores JS. M2 sigue en pie si el resto se cumple; el plan raíz ya prevé diferirlos antes de mover M2 (`docs/business/fuentes/plan-raiz-roadmap-edt.md:93`). No afecta la aprobación de ninguna PPS: la de Federico es de seguridad y la de Romeo excluye RUM.
2. **B.5 — SPA React (se mantiene).** **D10 (propuesta del 23/10/2026)** mantiene B.5 en la v1: es dependencia de C.1 (`docs/business/issues-fases-abc.md §4 B.5, §5 C.1`) y sostiene la demo visual de las 3 vistas. El recorte confirmado es B.7, no B.5.
3. **B.2, B.8 y B.12 — seguridad (fuera de la v1).** **D3 (propuesta del 23/10/2026)** los retira de la v1 y los pasa al backlog de extensión 2027, sin milestone en M0–M2. Impacto: la v1 no incluye hardening CIS ni evidencia GLP, pero el flujo RUM → alerta no se afecta. B.8 estaba marcada **CRÍTICA** en el catálogo (`docs/business/issues-fases-abc.md §4 B.8`), así que las issues se actualizan con su nuevo estado. La PPS de Federico cerró su ventana el 19/10/2026 y entrega su informe final con la v1, así que estas tareas no condicionan la aprobación.
4. **No recortables sin redefinir M2:** sonda HTTP mínima de disponibilidad (D2; `docs/business/fuentes/plan-raiz-roadmap-edt.md:25,90`), alerta por Telegram (`docs/business/fuentes/plan-raiz-roadmap-edt.md:90-91`), piloto medido (`docs/business/issues-fases-abc.md §5 C.2`), tests ≥ 70 % (`docs/business/fuentes/plan-raiz-roadmap-edt.md:91`) y flujo E2E (`docs/business/issues-fases-abc.md §5 C.1`). Si cualquiera se cae, M2 deja de significar lo que el plan raíz promete y la dirección debe aprobar un hito nuevo.
5. **B.4, B.6 y B.11 no son recortes: están fuera de la v1 por D1.** La detección ML se mueve a M3 (v1.1). El paso "AI" del E2E se reemplaza por la regla de umbral de B.14, y C.1 se actualiza en consecuencia.
6. **C.6 se divide en dos entregables (D12).** C.6 conserva los informes finales de PPS (8 h por persona) y C.7 agrega el informe de cierre de la v1 con horas del PO, sin consumir la capacidad de los practicantes.

---

## 7. Métricas de éxito de la v1

No son las métricas de MVP-1. SUS y la validación con 4 personas pertenecen a F1/2027 (`gestionProyecto/roadmap/roadmap-producto.md:155`).

| Métrica | Umbral | Verificación | Fuente |
|---|---|---|---|
| Cobertura de tests sobre código real | ≥ 70 % | `pytest --cov=src`; gate `fail_under` | `docs/business/fuentes/plan-raiz-roadmap-edt.md:141`; `pyproject.toml:59` |
| Latencia de ingesta bajo carga estándar | ≤ 500 ms | Escenario k6 versionado | `docs/business/issues-fases-abc.md §5 C.3`; `gestionProyecto/marco/04-especificaciones.md:110` |
| Flujo E2E | agente → ingesta → PostgreSQL → regla de umbral → alerta → notificación | Smoke test documentado en `develop` | `docs/business/issues-fases-abc.md §5 C.1` |
| Alerta recibida por Telegram | 1 alerta ante anomalía inyectada | Evidencia de recepción en el canal | `docs/business/fuentes/plan-raiz-roadmap-edt.md:90-91`; `docs/business/issues-fases-abc.md §4 B.10` |
| Sitio piloto medido con RUM | Datos visibles en ingesta y dashboard | Evidencia de operación | `docs/business/issues-fases-abc.md §5 C.2`; `docs/business/fuentes/plan-raiz-roadmap-edt.md:90` |
| Demo de cierre ante GIDAS | 1 demo de punta a punta | Revisión de M2 | `docs/business/fuentes/plan-raiz-roadmap-edt.md:91` |
| Compose de release | `docker compose up` en máquina limpia | Smoke test post-deploy | `docs/business/issues-fases-abc.md §5 C.5`; `docs/adr/0010-arquitectura-de-4-contenedores.md:24-31` |
| F1 de detección (M3; no aplica a la v1) | ≥ 0.70 | Dataset de validación | `docs/business/issues-fases-abc.md §4 B.6`; `gestionProyecto/marco/04-especificaciones.md:62` |

---

## 8. Supuestos, dependencias externas y decisiones de alcance

### 8.1. Supuestos

- Tres integrantes con 10 h semanales hasta M2; 60 h por sprint (`docs/business/fuentes/plan-raiz-roadmap-edt.md:93`). El Gantt cierra el plan completo con **90/90 h por persona y sin margen** (`docs/business/fuentes/plan-integral-gantt-v1.0.pdf`, §Carga horaria). Con D1 y D3 fuera de la v1 se liberan **34 h de Federico** y **24 h de Romeo** (ya descontadas las 8 h de B.14): eso financia las 8 h de B.13 y deja holgura. **Santiago sigue en el límite, 90/90, sin margen.** **No está confirmada la continuidad** después de las ventanas de las PPS (18/09 y 19/10) hasta el 18/12.
- Receso en enero y febrero, con el piloto generando datos (`docs/business/fuentes/plan-raiz-roadmap-edt.md:123,128`).
- VM Rocky 10, CPU-only, < 2 GB de RAM y costo $0/mes (`docs/adr/0010-arquitectura-de-4-contenedores.md:18`).
- Sitio piloto definido antes del 04/12/2026 (`docs/business/issues-fases-abc.md §5 C.2`).
- Un origen para la sonda HTTP mínima de la v1; el multi-origen queda en R.4 para 2027 (`docs/business/fuentes/plan-raiz-roadmap-edt.md:37,150`).
- Credenciales de Telegram y correo disponibles; secretos por variables de entorno (`docs/business/issues-fases-abc.md §4 B.10`).

### 8.2. Dependencias externas

- Autorización y consentimiento del sitio piloto (`docs/business/issues-fases-abc.md §5 C.2`).
- Telegram Bot API y proveedor de correo (`docs/business/issues-fases-abc.md §4 B.10`).
- GitHub Actions y token `gh` con scope `project` para el tablero (`docs/business/flujo-github.md §4`).
- Free-tier cloud o segunda red para el origen secundario de sondas: no aplica a la v1, queda en R.4 (`docs/business/fuentes/plan-raiz-roadmap-edt.md:37`).
- Calendario académico: el supuesto de receso y de reanudación en marzo desplaza M3/M4 (`docs/business/fuentes/plan-raiz-roadmap-edt.md:128`).
- Licencia de ASN/geolocalización: no aplica a la v1, se verifica antes de M3 (`docs/business/fuentes/plan-raiz-roadmap-edt.md:151`).

### 8.3. Decisiones propuestas (23/10/2026)

**Estado:** propuestas, no acuerdos cerrados. La revisión del PR #65 pidió tratarlas como propuestas hasta cerrarlas con el equipo; las revisiones del 24/10/2026 están en §8.4.

| ID | Decisión | Consecuencia |
|---|---|---|
| **D1** | La v1 usa reglas de umbral para alertas (B.14); la detección ML (B.4, B.6, B.11) se mueve a M3 (v1.1). El criterio de salida de M2 no incluye ML; M3 sí. `intellops-ai-engine` sigue existiendo como contenedor, sin lógica de detección en v1. | B.4, B.6 y B.11 salen de la v1 y se reprograman en M3. La v1 conserva el motor determinístico B.14 y el paso "AI" del E2E se reemplaza por una regla de umbral. |
| **D2** | La v1 incluye una sonda HTTP mínima de disponibilidad desde un solo origen. TLS, DNS y multi-origen pasan a M3 (R.4). Se crea la issue B.13. | Se suma B.13 a la fase B con 8 h financiadas por la liberación de D1 y D3 (§8.1); R.4 queda como referencia para TLS, DNS y multi-origen. |
| **D3** | Lynis (B.2), hardening CIS (B.8) y dashboards GLP (B.12) salen de la v1 y pasan al backlog de extensión 2027, sin milestone en M0–M2. El plan raíz los saca del camino crítico; la ventana de la PPS de seguridad de Federico cerró el 19/10/2026. | B.2, B.8 y B.12 dejan de bloquear M2 y se publican en 2027 con el milestone que fije la extensión. |
| **D4** | El despacho de alertas lo hace `intellops-comms` según ADR-0010; Alertmanager no entra en la v1. | El canal de alertas se implementa sin un servicio adicional; Alertmanager queda en el roadmap. |
| **D5** | ~~C.6 deja de ser "informes finales de PPS" y pasa a ser "Informe de cierre de la v1".~~ **Revisada por D12 (24/10/2026).** | C.6 recupera los informes finales de PPS y el informe de cierre de la v1 pasa a C.7. |
| **D6** | El health score no entra en la v1; queda en R.7 (2027). | La v1 no incluye modelo, endpoint ni datos de health score. |
| **D7** | Son normativos `docs/business/brief-v1.md` y `docs/brief-v2.md`. `docs/brief.md` queda como histórico. | Se agrega la nota de estado en `docs/brief.md` y se elimina la ambigüedad de precedencia. |
| **D8** | Se acepta la divergencia entre los planes PPS2 y el repo; se documenta en los informes finales, sin reescribir los planes PPS2 de forma retroactiva. **Revisada por D13 (24/10/2026):** las ventanas de cierre se reprograman al 18/12/2026 sin reescribir los planes PPS2. | La divergencia queda como evidencia en los informes de cierre; los planes aprobados no se tocan y las fechas de entrega de los informes se alinean con la v1. |
| **D9** | `openspec/specs/architecture/spec.md` se corrige: la base de datos es PostgreSQL 16 (ADR-0009), no SQLite. | La tabla de decisiones arquitectónicas deja de contradecir ADR-0009 y ADR-0010. |
| **D10** | B.5 (SPA) se mantiene en la v1. B.7 (XHR y rage clicks) es el recorte confirmado. | B.5 sigue siendo dependencia de C.1; B.7 queda en v1.1 (M3). |

### 8.4. Revisiones propuestas (24/10/2026, revisión del PR #65)

Estas decisiones corrigen la divergencia entre este brief y el plan integral entregado a coordinación (`docs/business/fuentes/plan-integral-gantt-v1.0.pdf`, v1.0, 17/10/2026).

| ID | Decisión | Consecuencia |
|---|---|---|
| **D11** | Se adopta el esquema de hitos del Gantt v1.0: M0 = 13/11/2026 (base cerrada), M1 = 04/12/2026 (feature freeze v1), M2 = 18/12/2026 (entrega MVP v1), M3 = 16/04/2027 (v1.1), M4 = 11/06/2027 (v2.0). | Se renumeran milestones, etiquetas `hito:*`, secciones del brief y del catálogo. Las fases A, B y C cierran en M0, M1 y M2. El prototipo 2027–2028 queda como extensión post-v2.0, fuera de la secuencia M0–M4. |
| **D12** | C.6 vuelve a ser "Informes finales de PPS" (8 h por persona, 07–18/12) y el "Informe de cierre de la v1" pasa a C.7, con horas del PO y sin consumir capacidad de los practicantes. | Las tres PPS recuperan su entregable final y la v1 mantiene su informe de cierre. La capacidad de 90/90 h por persona no cambia. |
| **D13** | Las ventanas de las PPS se reprograman: Romeo A4 (nov), A5 (nov–dic), A6 y A7 (dic); Federico F2 y F4 (nov–dic), F5 (dic); Santiago F3 (oct–nov), F4 (dic), F5 (nov–dic). Los informes finales se entregan con la v1 el 18/12/2026 y los planes PPS2 aprobados no se reescriben. | Cierra la contradicción de §5.2: la v1 ya no se presenta como anterior al cierre de las PPS. La aprobación sigue dependiendo del informe, el DoD y la evidencia A1–A7. |

---

## 9. Referencias

`docs/business/fuentes/` contiene las fuentes congeladas tal como se recibieron: los `.md` conservan sus líneas originales, así que las citas `archivo:línea` son verificables.

- `docs/business/fuentes/plan-raiz-roadmap-edt.md` — plan raíz de la dirección; alcance, hitos, frentes, cronograma y decisiones. Usa la numeración anterior de hitos (ver D11).
- `docs/business/fuentes/plan-integral-gantt-v1.0.pdf` — plan integral v1.0 (17/10/2026) entregado a coordinación; esquema de hitos M0–M4, cronograma de tareas, capacidad 90/90 h y trazabilidad PPS.
- `docs/business/fuentes/diagramas-actividades-v1.0.pdf` — diagramas de actividades y controles M0/M1/M2 del mismo plan.
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
- `docs/business/fuentes/pps/especificacion-entregables-pps-v06.md` — entregables y DoD de la PPS de Romeo.
- `docs/business/fuentes/pps/informe-2-alcance-pps.docx` — alcance y A1–A7 de las tres PPS.
- `RRHH/Federico Cavallero/PPS2_PlanTrabajo_IntellOps_Blanco_Cavallero_v2.docx`, `RRHH/Santiago Montanari/PPS2_PlanTrabajo_IntellOps_Montanari_v2.docx` y `RRHH/Romeo Monfroglio/PPS2_PlanTrabajo_IntellOps_V06_2026.docx` — planes PPS2.
- `README.md` y `CHANGELOG.md` — estado implementado y deuda declarada.
- `docker-compose.yml`, `pyproject.toml` y `.github/workflows/ci.yml` — compose, gate de cobertura y CI.
