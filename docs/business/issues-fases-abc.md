# Issues de la v1 — Fases A, B y C

**Estado**: Borrador para revisión. **No publicadas en GitHub todavía.**

**Fuente**: Plan integral del proyecto IntellOps v1.0 (17/10/2026), tabla de tareas
`P0.1`–`R.11`; `docs/business/plan-gestion-roadmap-edt.md`; `docs/business/EDT intellops.md`;
catálogos `docs/business/issues-s1-s2.md` y `docs/business/issues-s2-s3.md`.

**Alcance de este archivo**: issues nuevas de las fases A, B y C (ventana 19/10–18/12/2026,
entrega v1 el 18/12/2026). Las tareas `R.*` se listan al final como backlog post-v1 y **no se
publican todavía**. Las issues `ISS-S1-*`, `ISS-S2-*` e `ISS-S3-*` ya existen en GitHub
(#17–#25 y #35–#45) y no se duplican acá; solo se referencian como dependencias.

---

## 1. Comparación con los catálogos existentes

| Fuente | Qué contiene | Cobertura frente al plan integral |
|---|---|---|
| `docs/business/issues-s1-s2.md` | Catálogo S1 (9 issues) + S2 viejo (9 issues) | S1: 9/9. S2: 5/5 publicadas; **S2-06 a S2-09 quedaron obsoletas** (absorbidas por S3/A.4/B.6) |
| `docs/business/issues-s2-s3.md` | Registro de las 11 issues publicadas (#35–#45) | S2: 5/5. S3: 6/6. **No cubre A/B/C/R** |
| `docs/business/EDT intellops.md` | Plan de 8 sprints (S1–S8) | Origen de S1–S3; no tiene issues A/B/C/R |
| GitHub #17–#25 | Issues S1 publicadas | S1: 9/9, todas cerradas |
| GitHub #35–#45 | Issues S2/S3 publicadas | S2: 5/5. S3: 6/6. Sin labels ni milestones |
| Plan integral (PDF) | 57 tareas: P0, ISS-S1/S2/S3, A, B, C, R | **A/B/C: 0/18 issues de la v1.** De las 22 originales, seis salen por D1/D3 y se suman B.13 (D2), B.14 (D1) y C.7 (D12). **R: 0/11 issues** |

### 1.1. Brechas detectadas

1. **No hay issues para las fases A, B y C**: 22 tareas de la ventana de la v1 (A.1–A.4,
   B.1–B.12, C.1–C.6) no tienen issue en GitHub ni entrada en los catálogos. B.13 se agrega
   después por D2 (sonda HTTP mínima).
2. **No hay issues para R.1–R.11**: 11 tareas post-v1. Correcto que no estén publicadas aún,
   pero conviene dejarlas en backlog para no perderlas.
3. **S2-06 a S2-09 del catálogo viejo están obsoletas**: `RUM_METRIC`, `JS_EXCEPTION`,
   `Dataset inicial` y `Evaluación preliminar` se absorbieron en `ISS-S3-01`, `ISS-S3-02`,
   `ISS-S3-05`, `A.4` y `B.6`. El catálogo `issues-s1-s2.md` sigue mostrándolas como si fueran
   issues vigentes.
4. **Desfase de fase/sprint**: el plan integral usa **Fase A/B/C** y sprints 4–8. Las issues
   `ISS-S2-05` (#39), `ISS-S3-03` (#42) e `ISS-S3-06` (#45) siguen etiquetadas como Sprint 2/3,
   pero el plan las ubica en **Fase A** (19/10–13/11).
5. **Desfase de estado**: el plan marca `ISS-S2-02`/`ISS-S2-03`/`ISS-S2-04` como Hecho, pero
   #36–#38 siguen abiertas. También marca `ISS-S3-01` como Hecho (PR #57) y `ISS-S3-02`/`ISS-S3-04`
   como En curso (PRs #59/#60), mientras #40, #41 y #43 siguen abiertas. Hay que cerrarlas o dejar
   el estado explícito.
   _Actualizado (23/10/2026): #36, #37, #38, #40, #41 y #43 fueron cerradas con evidencia de PR y
   verify-report. Quedan abiertas solo #39, #42 y #45, que son trabajo real de la fase A._
6. **Sin labels ni milestones**: las issues #35–#45 se publicaron sin etiquetas. `A.1` existe
   justamente para crear el tablero, los milestones M0–M4 y las etiquetas `hito:*`, `frente:*`,
   `fase:*` y `owner:*`.
7. **Inconsistencia de owner en S2-01**: el catálogo viejo asigna S2-01 a Santiago; el registro
   publicado y el plan lo asignan a Federico. Vale el registro publicado (`issues-s2-s3.md`).

### 1.2. Mapa de fases

| Fase | Ventana | Hito de cierre | Issues nuevas | Issues existentes que se mueven |
|---|---|---|---|---|
| **A — Cerrar la base** | 19/10 – 13/11/2026 | **M0** (13/11/2026) | A.1, A.2, A.3, A.4 | ISS-S2-05 (#39), ISS-S3-03 (#42), ISS-S3-06 (#45) |
| **B — Construir la v1** | 02/11 – 04/12/2026 | **M1 — Feature freeze v1** (04/12/2026) | B.1, B.3, B.5, B.7 (M3), B.9, B.10, B.13, B.14 | — |
| **C — Cerrar la v1** | 07/12 – 18/12/2026 | **M2 — Entrega MVP v1** (18/12/2026) | C.1–C.7 | — |
| **Post-v1** | 2027 | M3–M4 (+ extensión post-v2.0) | R.1–R.11 (backlog, no publicar) | — |

> **Fase ≠ hito.** Las fases son ventanas internas del equipo y se marcan con `fase:*`. Los hitos
> miden resultados del producto. Desde el 24/10/2026 (D11) cada fase cierra en un hito propio:
> A → M0, B → M1 (feature freeze) y C → M2 (entrega).
>
> **Nota (23/10/2026, revisada el 24/10/2026).** B.2, B.4, B.6, B.8, B.11 y B.12 quedan fuera de
> la v1: B.4, B.6 y B.11 pasan a **M3 (v1.1)** por D1; B.2, B.8 y B.12 pasan al backlog de
> extensión 2027 por D3 y no reciben milestone en M0–M2. B.13 (sonda HTTP mínima) se suma a la
> fase B por D2 y B.14 reemplaza a B.11 en la v1. Las issues movidas conservan su ID y su
> trazabilidad.

---

## 2. Convenciones

- **ID**: se usa el ID del plan integral (`A.1`, `B.12`, `C.5`, `R.8`) para trazabilidad directa.
- **Título sugerido en GitHub**: `A.1 — Tablero, milestones v1 y etiquetas hito/frente`.
- **Labels sugeridas**: `fase:a|b|c`, `hito:m0|m1|m2|m3|m4`,
  `frente:captura|plataforma|inteligencia|gestion`, `owner:<nombre>`, `critico` cuando el plan lo
  marca CRÍTICO.
- **Milestones** (esquema del Gantt v1.0, D11):
  `M0 — Base cerrada (13/11/2026)`, `M1 — Feature freeze v1 (04/12/2026)`,
  `M2 — Entrega MVP v1 (18/12/2026)`, `M3 — v1.1 (16/04/2027)`,
  `M4 — v2.0 (11/06/2027)`. El prototipo 2027–2028 queda como extensión post-v2.0, sin hito.
- **Hito por issue**: `hito:m0` para la fase A; `hito:m1` para la fase B; `hito:m2` para la
  fase C; `hito:m3` para R.2–R.7 y B.4/B.6/B.11; `hito:m4` para R.1 y R.8–R.11.
- **Estimación**: días hábiles y horas del plan integral. Las horas son de planificación, no de
  imputación.
- **Definición de terminado**: criterios de aceptación cumplidos + tests/evidencia + PR revisado
  por otra persona del equipo.

---

## 3. Fase A — Cerrar la base (19/10 – 13/11/2026)

### A.1 — Tablero, milestones v1 y etiquetas hito/frente

- **Fase**: A · **Fechas**: 19/10 – 23/10/2026 · **Días hábiles**: 5
- **Owner**: PO + equipo
- **Depende de**: —
- **Prioridad**: Alta
- **Descripción**: Crear el tablero de GitHub con las columnas del flujo (Backlog, Listo,
  En curso, En revisión, Hecho), los milestones M0–M4 y las etiquetas de hito, frente y owner.
  Es la issue que habilita a publicar el resto con trazabilidad.
- **Criterios de aceptación**:
  - [x] Milestones `M0`–`M4` creados. Fechas firmes: M0 13/11/2026, M1 04/12/2026 y M2 18/12/2026; M3 16/04/2027 y M4 11/06/2027 (D11).
  - [x] Etiquetas `hito:*`, `frente:*`, `fase:*`, `owner:*` y `critico` creadas.
  - [ ] Tablero con las 5 columnas y las issues S1–S3 (#17–#25 y #35–#45) cargadas.
        _Pendiente: el token de `gh` necesita scope `project`. Las issues ya tienen milestone,
        frente y owner; falta el Project V2._
  - [x] Cada issue abierta tiene milestone, frente y owner.
  - [x] Flujo documentado en `docs/business/flujo-github.md`.

### A.2 — Alcance de la v1 congelado (brief v1 y criterios por PPS)

- **Fase**: A · **Fechas**: 19/10 – 30/10/2026 · **Días hábiles**: 10
- **Owner**: PO + equipo
- **Depende de**: A.1
- **Prioridad**: Alta
- **Descripción**: Congelar el alcance mínimo de la v1 y los criterios de aprobación de cada PPS.
  Debe dejar explícito qué entra, qué se difiere a v1.1/2027 y qué recorte se aplica si un sprint
  se atrasa.
- **Criterios de aceptación**:
  - [x] `docs/business/brief-v1.md` (o equivalente) con alcance dentro/fuera.
  - [x] Criterios de aprobación por PPS (F1, F2, F3) y por frente.
        _Entregado como §5.2 por PPS/persona y §5.3 por frente: PPS y frente son ejes distintos._
  - [x] Lista de recortes permitidos (B.7, B.5, etc.) y su impacto.
  - [ ] Aprobado por el equipo y enlazado desde el plan integral.
        _Pendiente: las propuestas D1–D13 se ratifican en la revisión del PR #65._
        _D1–D10 propuestas el 23/10/2026 y D11–D13 el 24/10/2026; siguen pendientes de acuerdo del equipo. El detalle queda en `brief-v1.md` §8.3 y §8.4._
  - [x] Issues A/B/C alineadas con ese alcance.
        _Catálogo alineado: B.2, B.4, B.6, B.8, B.11 y B.12 salen de la v1; se suman B.13 (D2),
        B.14 (D1) y C.7 (D12). La publicación en GitHub sigue pendiente (§7)._

### A.3 — Contrato del agente RUM de navegador v0.1

- **Fase**: A · **Fechas**: 19/10 – 30/10/2026 · **Días hábiles**: 10 · **Horas**: 6
- **Owner**: Federico
- **Depende de**: ISS-S1-05/06
- **Prioridad**: **CRÍTICA**
- **Descripción**: Definir el contrato v0.1 del agente RUM: eventos, muestreo, batching,
  transporte (`sendBeacon`/`fetch`), CORS, política de privacidad, presupuesto de bundle y
  versionado. Debe ser compatible con `POST /telemetry/metrics` y `/telemetry/exceptions`.
- **Criterios de aceptación**:
  - [x] Contrato versionado en `docs/architecture/` u `openspec/specs/`.
        _Entregado en `docs/architecture/ContratoAgenteRUM.md` (v0.1)._
  - [x] Eventos TTFB, FCP, errores JS y metadata de sesión definidos.
  - [x] Estrategia de muestreo, batching y reintento documentada.
  - [x] Presupuesto de bundle definido (< 30 KB gzip).
  - [x] Privacidad y datos permitidos explicitados.
  - [ ] Revisado por Santiago (QA) y alineado con el OpenAPI vigente.
        _OD-01 a OD-06 resueltas el 23/10/2026 y D-01/D-05 ya corregidas. Falta la revisión formal
        de Santiago y ejecutar las correcciones de código de seguimiento (OD-03, OD-04, D-03, D-04)._

### A.4 — Generador sintético y anomalías inyectadas etiquetadas

- **Fase**: A · **Fechas**: 26/10 – 13/11/2026 · **Días hábiles**: 15 · **Horas**: 12
- **Owner**: Romeo
- **Depende de**: ISS-S3-04
- **Prioridad**: **CRÍTICA**
- **Descripción**: Generar un dataset sintético reproducible con anomalías inyectadas y
  etiquetadas, para entrenar y comparar modelos sin depender todavía del dataset real del piloto.
- **Criterios de aceptación**:
  - [ ] Script reproducible (seed fija) en `ml/` o `src/ml/`.
  - [ ] Series con anomalías de distinto tipo y severidad, etiquetadas.
  - [ ] Dataset exportado y documentado (formato, columnas, rangos).
  - [ ] Split train/validation definido.
  - [ ] Consumible por B.6 sin acoplamiento a la ingesta.

### Issues existentes que se mueven a Fase A

- **ISS-S2-05 — Entorno reproducible de testing** (#39): 19/10 – 30/10, 8 h. Mover a Fase A/M0.
- **ISS-S3-03 — Gestión de sesiones (`USER_SESSION`)** (#42): 19/10 – 30/10, 6 h. Mover a Fase A/M0.
- **ISS-S3-06 — Pruebas unitarias de módulos críticos (≥70 %)** (#45): 26/10 – 13/11, 14 h.
  Mover a Fase A/M0. Depende de ISS-S2-05.

---

## 4. Fase B — Construir la v1 (02/11 – 04/12/2026)

### B.1 — Agente RUM: TTFB, FCP y errores JS

- **Fase**: B · **Fechas**: 02/11 – 13/11/2026 · **Días hábiles**: 10 · **Horas**: 16
- **Owner**: Federico
- **Depende de**: A.3, ISS-S2-03
- **Prioridad**: **CRÍTICA**
- **Descripción**: Implementar el agente RUM de navegador que captura TTFB, FCP y errores JS,
  agrupa en batches y los envía a la ingesta según el contrato A.3.
- **Criterios de aceptación**:
  - [ ] `src/agent/rum.js` (o estructura equivalente) implementado.
  - [ ] Captura TTFB, FCP y errores JS no manejados.
  - [ ] Batching, muestreo y transporte según A.3.
  - [ ] Bundle < 30 KB gzip.
  - [ ] Envío exitoso a `/telemetry/metrics` y `/telemetry/exceptions`.
  - [ ] Demo en página HTML y tests del agente.

### B.2 — Auditoría de seguridad del servidor (Lynis)

- **Fase**: B · **Fechas**: 02/11 – 13/11/2026 · **Días hábiles**: 10 · **Horas**: 8
- **Owner**: Federico
- **Depende de**: ISS-S1-03
- **Prioridad**: Alta
- **Estado**: Fuera de la v1: movida al backlog de extensión 2027 por D3; sin milestone en M0–M2 (D11).
- **Descripción**: Ejecutar la auditoría Lynis sobre el servidor/VM del laboratorio, registrar
  el baseline y priorizar hallazgos para el hardening B.8.
- **Criterios de aceptación**:
  - [ ] Baseline Lynis ejecutado y guardado.
  - [ ] Hallazgos clasificados por severidad.
  - [ ] Plan de remediación priorizado para B.8.
  - [ ] Evidencia en `docs/security/` o `governance/`.

### B.3 — API de lectura: series, anomalías y alertas

- **Fase**: B · **Fechas**: 02/11 – 20/11/2026 · **Días hábiles**: 15 · **Horas**: 12
- **Owner**: Santiago
- **Depende de**: ISS-S3-01, A.2
- **Prioridad**: Alta
- **Descripción**: Exponer la API de lectura app-scoped para series de métricas, anomalías y
  alertas, con contrato OpenAPI y paginación/ventanas acotadas.
- **Criterios de aceptación**:
  - [ ] Endpoints de series, anomalías y alertas implementados.
  - [ ] Tenant derivado exclusivamente de la API key.
  - [ ] Ventanas y paginación acotadas.
  - [ ] OpenAPI actualizado y contract tests verdes.
  - [ ] Tests unitarios e integración.

### B.4 — Features y AI worker asíncrono con reintentos

- **Fase**: B · **Fechas**: 02/11 – 13/11/2026 · **Días hábiles**: 10 · **Horas**: 10
- **Owner**: Romeo
- **Depende de**: ISS-S3-04
- **Prioridad**: **CRÍTICA**
- **Estado**: Fuera de la v1: movida a M3 (v1.1) por D1; numeración revisada por D11 (24/10/2026).
- **Descripción**: Implementar el feature engineering y el worker asíncrono del AI engine, con
  lectura batch, reintentos y escritura de anomalías.
- **Criterios de aceptación**:
  - [ ] Feature vector definido e implementado.
  - [ ] Worker asíncrono con reintentos y backoff.
  - [ ] Lectura batch de `RUM_METRIC` sin escribir métricas originales.
  - [ ] Escritura de `ANOMALY` (y `ALERT` Pending cuando corresponda).
  - [ ] Tests de idempotencia y fallos transitorios.

### B.5 — SPA React: latencias RUM y heatmap UX

- **Fase**: B · **Fechas**: 09/11 – 04/12/2026 · **Días hábiles**: 20 · **Horas**: 22
- **Owner**: Romeo
- **Depende de**: B.3 (contrato)
- **Prioridad**: Alta
- **Estado**: Ajustada por D1 (23/10/2026): el panel de predicciones se difiere a M3 junto con B.6,
  porque la v1 no incluye detección ML.
- **Descripción**: Implementar la SPA React con las dos vistas de la v1: latencias RUM y heatmap UX.
  El panel de predicciones se difiere a M3 con B.6. Es un build estático, no un contenedor del
  compose.
- **Criterios de aceptación**:
  - [ ] Dos vistas funcionales contra la API de B.3.
  - [ ] Build estático reproducible.
  - [ ] Bundle < 1 MB.
  - [ ] Estados de carga/error y responsive básico.
  - [ ] Tests de componentes y smoke E2E.

### B.6 — Modelos: baseline estadístico vs Isolation Forest

- **Fase**: B · **Fechas**: 16/11 – 27/11/2026 · **Días hábiles**: 10 · **Horas**: 14
- **Owner**: Romeo
- **Depende de**: A.4, B.4
- **Prioridad**: **CRÍTICA**
- **Estado**: Fuera de la v1: movida a M3 (v1.1) por D1; numeración revisada por D11 (24/10/2026).
- **Descripción**: Comparar el baseline estadístico (Z-score/umbrales) con Isolation Forest
  sobre el dataset etiquetado, elegir el modelo de la v1 y persistir su ciclo de vida.
- **Criterios de aceptación**:
  - [ ] Baseline y Isolation Forest evaluados con el mismo split.
  - [ ] Métricas F1, recall, precision y falsos positivos reportadas.
  - [ ] Selección de modelo justificada y reproducible.
  - [ ] `ML_MODEL` persistido con hiperparámetros y estado.
  - [ ] Informe en `docs/research/` o `ml/`.

### B.7 — RUM completo: XHR y rage clicks

- **Fase**: B · **Fechas**: 16/11 – 27/11/2026 · **Días hábiles**: 10 · **Horas**: 10
- **Owner**: Federico
- **Depende de**: B.1
- **Prioridad**: Media · **Diferible a v1.1**
- **Estado**: Recorte confirmado de la v1 por D10 (23/10/2026); queda en v1.1, que es M3.
- **Descripción**: Extender el agente RUM para capturar latencia XHR y rage clicks. Es la
  primera tarea que se recorta si un sprint se atrasa.
- **Criterios de aceptación**:
  - [ ] XHR latency capturada y enviada.
  - [ ] Rage clicks detectados y enviados.
  - [ ] Contrato y validación de ingesta actualizados.
  - [ ] Tests del agente.

### B.8 — Hardening básico CIS nivel 1

- **Fase**: B · **Fechas**: 16/11 – 04/12/2026 · **Días hábiles**: 15 · **Horas**: 14
- **Owner**: Federico
- **Depende de**: B.2
- **Prioridad**: **CRÍTICA**
- **Estado**: Fuera de la v1: movida al backlog de extensión 2027 por D3; sin milestone en M0–M2 (D11).
- **Descripción**: Aplicar hardening CIS Level 1 sobre el servidor, con playbooks Ansible
  idempotentes y evidencia de antes/después.
- **Criterios de aceptación**:
  - [ ] Playbooks Ansible versionados e idempotentes.
  - [ ] Lynis ≥ 70 % post-hardening.
  - [ ] Rollback documentado.
  - [ ] Evidencia de cumplimiento en `docs/security/` o `governance/`.

### B.9 — Quality gates bloqueantes en CI

- **Fase**: B · **Fechas**: 16/11 – 20/11/2026 · **Días hábiles**: 5 · **Horas**: 6
- **Owner**: Santiago
- **Depende de**: ISS-S3-06
- **Prioridad**: Alta
- **Descripción**: Hacer bloqueantes los gates de calidad en CI: cobertura, lint y contrato.
- **Criterios de aceptación**:
  - [ ] Coverage < 70 % bloquea el PR.
  - [ ] Lint con warnings/errores bloquea el PR.
  - [ ] OpenAPI/contract inválido bloquea el PR.
  - [ ] Gates documentados y verificados con un PR de prueba.

### B.10 — Notificaciones por mail y Telegram (reintentos)

- **Fase**: B · **Fechas**: 16/11 – 04/12/2026 · **Días hábiles**: 15 · **Horas**: 10
- **Owner**: Santiago
- **Depende de**: B.3
- **Prioridad**: **CRÍTICA**
- **Descripción**: Implementar el dispatcher de notificaciones por mail y Telegram con retry y
  backoff exponencial, actualizando el estado de `ALERT`.
- **Criterios de aceptación**:
  - [ ] Envío por mail y Telegram operativo.
  - [ ] Retry con backoff ante fallos transitorios.
  - [ ] `ALERT` pasa de Pending a Sent/Failed con `sent_at`.
  - [ ] Secretos por variables de entorno, nunca en código.
  - [ ] Tests con proveedores mockeados.

### B.11 — Motor de reglas de alerta (severity y confidence)

- **Fase**: B · **Fechas**: 23/11 – 04/12/2026 · **Días hábiles**: 10 · **Horas**: 8
- **Owner**: Romeo
- **Depende de**: B.6
- **Prioridad**: **CRÍTICA**
- **Estado**: Fuera de la v1: movida a M3 (v1.1) por D1; numeración revisada por D11 (24/10/2026).
- **Descripción**: Implementar el motor de reglas que combina umbrales y score del modelo para
  asignar severidad y confidence, y crear la alerta en estado Pending.
- **Criterios de aceptación**:
  - [ ] Reglas de severidad y confidence definidas.
  - [ ] Deduplicación/cooldown para evitar alertas repetidas.
  - [ ] `ALERT` creada en Pending con severidad y mensaje.
  - [ ] Tests de reglas y casos borde.

### B.12 — Logs de seguridad y dashboards Grafana (seguridad y RUM)

- **Fase**: B · **Fechas**: 23/11 – 04/12/2026 · **Días hábiles**: 10 · **Horas**: 12
- **Owner**: Federico
- **Depende de**: B.1, B.2
- **Prioridad**: Alta
- **Estado**: Fuera de la v1: movida al backlog de extensión 2027 por D3; sin milestone en M0–M2 (D11).
- **Descripción**: Pipeline GLP de seguridad (Promtail/Loki) y dashboards Grafana para las vistas
  de seguridad y RUM. Es infraestructura de seguridad del módulo M-SEG, **fuera del compose del
  producto**; no agrega contenedores al compose de 4 sin un ADR nuevo.
- **Criterios de aceptación**:
  - [ ] Pipeline Promtail → Loki operativo en el entorno de seguridad.
  - [ ] Cuatro dashboards de seguridad versionados como JSON.
  - [ ] Vista RUM básica en Grafana.
  - [ ] Evidencia de eventos simulados detectados.
  - [ ] Confirmado que el compose del producto sigue con 4 contenedores.

### B.13 — Sonda HTTP mínima de disponibilidad

- **Fase**: B · **Fechas**: 09/11 – 20/11/2026 · **Días hábiles**: 10 · **Horas**: 8
- **Owner**: Federico
- **Depende de**: B.1
- **Prioridad**: Alta
- **Descripción**: Implementar una sonda HTTP periódica desde un solo origen que registra
  disponibilidad, código de estado y latencia, y envía los datos por el mismo camino de ingesta
  RUM. TLS, DNS y multi-origen quedan en R.4 (2027) y no forman parte de esta issue.
- **Criterios de aceptación**:
  - [ ] Sonda programada a intervalo configurable, ejecutada desde un solo origen.
  - [ ] Registro de disponibilidad, código de estado HTTP y latencia por ejecución.
  - [ ] Datos enviados por el mismo camino de ingesta y consultables en la API de lectura.
  - [ ] Manejo explícito de timeouts y errores de conexión como indisponibilidad.
  - [ ] Tests de la sonda y evidencia de una ejecución real contra el sitio piloto.

### B.14 — Reglas de umbral para alertas de la v1

- **Fase**: B · **Fechas**: 16/11 – 27/11/2026 · **Días hábiles**: 10 · **Horas**: 8
- **Owner**: Romeo
- **Depende de**: B.3, B.13
- **Prioridad**: **CRÍTICA**
- **Estado**: Creada por D1 (23/10/2026). La detección ML (B.11) pasa a M3, pero M2 exige una alerta
  por Telegram, así que la v1 necesita un motor determinístico que la produzca.
- **Descripción**: Implementar el motor de reglas determinísticas que evalúa umbrales sobre las
  métricas RUM y la disponibilidad de la sonda, y crea `ALERT` en estado Pending con severidad y
  mensaje. Sustituye en la v1 al motor de reglas basado en score ML (B.11), que pasa a M3 con la
  detección.
- **Criterios de aceptación**:
  - [ ] Umbrales configurables por métrica y por aplicación (latencia, tasa de errores,
        disponibilidad de la sonda).
  - [ ] `ALERT` creada en estado Pending con severidad y mensaje.
  - [ ] Deduplicación o cooldown para evitar alertas repetidas.
  - [ ] Tests de reglas y casos borde: sin datos, datos insuficientes, valor exactamente en el
        umbral.
  - [ ] Integración con B.10 verificada por un test de contrato.

---

## 5. Fase C — Cerrar la v1 (07/12 – 18/12/2026)

### C.1 — Integración de punta a punta en develop

- **Fase**: C · **Fechas**: 07/12 – 11/12/2026 · **Días hábiles**: 5 · **Horas**: 12 (4 h por persona)
- **Owner**: Equipo
- **Depende de**: B.5, B.10, B.14
- **Prioridad**: **CRÍTICA**
- **Descripción**: Integrar todos los frentes en `develop` y validar el flujo completo:
  agente → ingesta → PostgreSQL → regla de umbral → alerta → notificación → dashboard.
- **Criterios de aceptación**:
  - [ ] Flujo E2E funcionando en `develop`.
  - [ ] Sin conflictos de integración abiertos.
  - [ ] Smoke test documentado y reproducible.
  - [ ] Demo de punta a punta para el equipo.

### C.2 — Agente RUM en el sitio piloto

- **Fase**: C · **Fechas**: 07/12 – 11/12/2026 · **Días hábiles**: 5 · **Horas**: 6
- **Owner**: Federico
- **Depende de**: B.1, B.13
- **Prioridad**: **CRÍTICA**
- **Descripción**: Instalar el agente RUM en el sitio piloto y verificar que la telemetría llega
  de punta a punta, con privacidad y consentimiento resueltos.
- **Criterios de aceptación**:
  - [ ] Sitio piloto definido antes del 04/12.
  - [ ] Agente instalado y enviando datos.
  - [ ] Datos visibles en la ingesta y en el dashboard.
  - [ ] Privacidad/consentimiento documentados.
  - [ ] Evidencia de operación.

### C.3 — Tests E2E automatizados y carga con k6 (≤ 500 ms)

- **Fase**: C · **Fechas**: 07/12 – 16/12/2026 · **Días hábiles**: 8 · **Horas**: 14
- **Owner**: Santiago
- **Depende de**: B.3, B.10
- **Prioridad**: **CRÍTICA**
- **Descripción**: Automatizar los tests E2E y ejecutar la prueba de carga con k6, con objetivo
  de latencia de ingesta ≤ 500 ms.
- **Criterios de aceptación**:
  - [ ] Suite E2E automatizada en CI.
  - [ ] Escenario k6 versionado.
  - [ ] Ingesta ≤ 500 ms bajo carga estándar.
  - [ ] Reporte de resultados y umbrales.

### C.4 — Evaluación de falsos positivos con datos reales

- **Fase**: C · **Fechas**: 09/12 – 16/12/2026 · **Días hábiles**: 6 · **Horas**: 4
- **Owner**: Romeo
- **Depende de**: B.14, C.2
- **Prioridad**: Alta
- **Descripción**: Evaluar los falsos positivos del motor de alertas con datos reales del piloto
  y ajustar umbrales/reglas.
- **Criterios de aceptación**:
  - [ ] Tasa de falsos positivos medida sobre datos reales.
  - [ ] Ajustes de umbrales/reglas documentados.
  - [ ] Comparación antes/después.
  - [ ] Informe de ajuste de reglas para el cierre de la v1 (C.7).

### C.5 — Release v1.0: tag, docker compose y guía de despliegue

- **Fase**: C · **Fechas**: 14/12 – 18/12/2026 · **Días hábiles**: 5 · **Horas**: 8
- **Owner**: Santiago
- **Depende de**: C.3
- **Prioridad**: **CRÍTICA**
- **Descripción**: Preparar el release v1.0: tag, compose de release, guía de despliegue y smoke
  test en una máquina limpia.
- **Criterios de aceptación**:
  - [ ] Tag `v1.0.0` creado.
  - [ ] `docker compose up` funciona en máquina limpia.
  - [ ] Guía de despliegue y rollback documentados.
  - [ ] Smoke test post-deploy.
  - [ ] Release notes.

### C.6 — Informes finales de PPS

- **Fase**: C · **Fechas**: 07/12 – 18/12/2026 · **Días hábiles**: 10 · **Horas**: 24 (8 h por persona)
- **Owner**: Equipo
- **Depende de**: C.1
- **Prioridad**: Alta
- **Estado**: Restituida por D12 (24/10/2026). La revisión anterior (D5) la había convertido en
  informe de cierre de la v1; ese entregable pasa a C.7.
- **Descripción**: Producir el informe final de cada PPS —Romeo A7, Federico F5, Santiago F5— con
  la evidencia de sus actividades A1–A7 y su DoD, y entregarlo junto con la v1 el 18/12/2026
  (D13). Incluye la divergencia entre los planes PPS2 y el repo (D8), sin reescribir los planes
  aprobados.
- **Criterios de aceptación**:
  - [ ] Un informe final por PPS, con evidencia A1–A7 y DoD.
  - [ ] Sección de divergencias entre los planes PPS2 y el repo (D8).
  - [ ] Informe entregado junto con el release el 18/12/2026.

### C.7 — Informe de cierre de la v1

- **Fase**: C · **Fechas**: 14/12 – 18/12/2026 · **Días hábiles**: 5 · **Horas**: sin horas de practicante (PO)
- **Owner**: PO (Emanuel) con apoyo del equipo
- **Depende de**: C.1, C.3, C.5
- **Prioridad**: Alta
- **Estado**: Creada por D12 (24/10/2026).
- **Descripción**: Producir el informe de cierre de la v1 con la evidencia del release, los
  resultados del piloto y la trazabilidad de las decisiones de alcance. No consume capacidad de
  los tres practicantes, que están en 90/90 h hasta el 18/12.
- **Criterios de aceptación**:
  - [ ] Informe único de cierre de la v1.
  - [ ] Evidencia de alcance, métricas de §7 del brief y release `v1.0.0`.
  - [ ] Trazabilidad de D1–D13 y de los recortes aplicados.
  - [ ] Informe entregado junto con el release el 18/12/2026.

---

## 6. Backlog post-v1 (R.1 – R.11) — no publicar todavía

| ID | Tarea | Owner | Ventana | Depende de | Hito |
|---|---|---|---|---|---|
| R.1 | Sitio piloto en operación (sensores activos) | F1 | 14/12/2026 – 11/06/2027 | C.2 | M4 |
| R.2 | Dataset real del piloto: acumulación y etiquetado | F3 | 14/12/2026 – 12/03/2027 | C.4 | M3 |
| R.3 | Convocatoria y onboarding de la nueva cohorte | PO + equipo | 01/02 – 12/03/2027 | M2 | M3 |
| R.4 | Sondas sintéticas HTTP, TLS y DNS | F1 | 01/03 – 26/03/2027 | R.3 | M3 |
| R.5 | Contexto de red: ISP y hosting | F1 | 29/03 – 16/04/2027 | R.4 · ADR de licencia | M3 |
| R.6 | Alertas por sensibilidad | F2 | 15/03 – 16/04/2027 | C.5 | M3 |
| R.7 | Reentrenamiento con dataset real y User Health Score | F3 | 01/03 – 16/04/2027 | R.2 | M3 |
| R.8 | LLM local que explica anomalías (Llama 3.2 1B + RAG) | F3 | 19/04 – 11/06/2027 | R.7 | M4 |
| R.9 | Escenarios multipaso y 3 sitios piloto | F1 | 19/04 – 28/05/2027 | R.4 | M4 |
| R.10 | Release v2.0 y prueba SUS | F2 + F3 | 17/05 – 11/06/2027 | R.6, R.8 | M4 |
| R.11 | Paper, oferta de extensión y handover al mantenedor | PO + equipo | 19/04 – 30/06/2027 | M4 | M4 |

**Nota**: R.1–R.11 quedan fuera de la ventana de las PPS y de la entrega v1. No se publican en
GitHub hasta que el equipo confirme continuidad y la nueva cohorte (R.3). Se dejan acá para no
perder la trazabilidad del plan integral.

---

## 7. Resumen para publicación

| Grupo | Issues nuevas | Estado sugerido |
|---|---|---|
| Fase A | A.1, A.2, A.3, A.4 | Publicar primero con milestone M0 (A.1 habilita labels/milestones) |
| Fase B | B.1, B.3, B.5, B.7, B.9, B.10, B.13, B.14 | Publicar después de A.2 con milestone M1 |
| Fase C | C.1–C.7 | Publicar con milestone M2 (o al inicio de Fase B para visibilidad) |
| Post-v1 | R.1–R.11 | No publicar; backlog en este archivo |

**Total nuevas**: 19 issues de la v1 (A/B/C) + 11 de backlog post-v1. Las issues B.2, B.4, B.6, B.8, B.11 y B.12 conservan su ID pero no cuentan para la v1 (D1 y D3): B.4, B.6 y B.11 pasan a M3 y las de seguridad no llevan milestone. B.13 se suma por D2, B.14 por D1 y C.7 por D12. B.7 se mantiene en el catálogo, aunque su entrega queda en v1.1 (M3, D10).

### Checklist de publicación

- [ ] A.1 crea milestones M0–M4 y etiquetas.
- [ ] Revisar títulos, owners y dependencias de cada issue.
- [ ] Publicar A.1–A.4 y mover ISS-S2-05, ISS-S3-03 e ISS-S3-06 a Fase A/M0.
- [ ] Publicar B.1, B.3, B.5, B.7, B.9, B.10, B.13 y B.14 con milestone M1.
- [ ] Publicar C.1–C.7 con milestone M2.
- [x] Cerrar/actualizar #40, #41 y #43 según el estado real de los PRs #57, #59 y #60.
- [ ] Marcar S2-06 a S2-09 de `issues-s1-s2.md` como obsoletas/absorbidas.
- [ ] No publicar R.1–R.11 todavía.
