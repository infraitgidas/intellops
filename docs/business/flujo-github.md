# Flujo de trabajo en GitHub

**Estado**: vigente desde el 23/10/2026 (issue A.1).
**Fuente**: plan raíz `docs/business/fuentes/plan-raiz-roadmap-edt.md` §Modelo de trabajo;
`docs/business/plan-gestion-roadmap-edt.md` §3; `docs/business/issues-fases-abc.md` §2.

Este documento define cómo se etiqueta y se mueve una issue en el repositorio. Si una issue no
cumple estas reglas, no entra al sprint.

---

## 1. Hitos (milestones)

Los hitos son los cinco del plan integral v1.0 entregado a coordinación (D11). Miden resultados del
producto, no ventanas de trabajo: cada fase interna cierra en uno de ellos.

| Milestone | Fecha | Qué cierra |
|---|---|---|
| `M0 — Base cerrada` | 13/11/2026 | Contratos aprobados, ADRs, EDT cargado como issues y primer dato de punta a punta visible |
| `M1 — Feature freeze v1` | 04/12/2026 | Todas las funciones de la v1 integradas en `develop`; el alcance queda cerrado |
| `M2 — Entrega MVP v1` | 18/12/2026 | v1.0 desplegada y midiendo el piloto, E2E y carga en verde, demo ante GIDAS e informes finales de PPS |
| `M3 — v1.1` | 16/04/2027 | Detección ML sobre datos reales, sondas TLS/DNS/multi-origen, ISP/ASN y User Health Score |
| `M4 — v2.0` | 11/06/2027 | LLM local RCA, 3 sitios piloto, prueba SUS, paper y oferta de extensión |

El prototipo 2027–2028 queda como extensión post-v2.0, fuera de la secuencia M0–M4.

**Regla**: toda issue abierta tiene exactamente un milestone. Una issue sin hito no entra al sprint.

---

## 2. Etiquetas

### Fase (`fase:*`)

Ventana interna del equipo. No reemplaza al hito: una fase puede cerrar en un hito que también
cierra otra fase.

| Etiqueta | Ventana |
|---|---|
| `fase:a` | 19/10 – 13/11/2026 — Cerrar la base |
| `fase:b` | 02/11 – 04/12/2026 — Construir la v1 |
| `fase:c` | 07/12 – 18/12/2026 — Cerrar la v1 |

### Hito (`hito:*`)

Espejo del milestone para filtrar y para el tablero: `hito:m0` … `hito:m4`.

### Frente (`frente:*`)

Los cuatro frentes del modelo de trabajo. Toda issue tiene exactamente uno.

| Etiqueta | Alcance | Dueño | Respaldo |
|---|---|---|---|
| `frente:captura` | Agente RUM, sondas, escenarios, contexto de red | Federico | Romeo |
| `frente:plataforma` | Ingesta, almacenamiento, API, alertas, CI y despliegue | Santiago | Federico |
| `frente:inteligencia` | Dataset, detección, User Health Score, LLM, evaluación | Romeo | Santiago |
| `frente:gestion` | Priorización del backlog, revisión, destrabar | Emanuel (PO) | Director del grupo |

### Owner (`owner:*`)

Persona responsable: `owner:federico`, `owner:romeo`, `owner:santiago`, `owner:emanuel`.
Una issue puede tener más de un owner solo si el trabajo es genuinamente compartido.

### Prioridad

`critico` cuando el plan integral marca la tarea como CRÍTICA.

### Estado (`estado:*`)

Reemplaza a las columnas del tablero de Projects, que no se puede crear (§4.1). Cada issue abierta
tiene como máximo una etiqueta de estado.

| Etiqueta | Columna | Cuándo se aplica |
|---|---|---|
| `estado:listo` | Listo | Aprobada, con milestone/frente/owner y sin dependencias abiertas |
| `estado:en-curso` | En curso | Alguien trabajando: hay rama o PR abierto |
| `estado:en-revision` | En revisión | PR abierto esperando review, o acuerdo pendiente de otra persona |
| *(sin etiqueta)* | Backlog | Abierta, todavía no lista (bloqueada o sin aprobar) |
| *(issue cerrada)* | Hecho | Criterios cumplidos y evidencia registrada |

---

## 3. Flujo

Columnas del tablero: **Backlog → Listo → En curso → En revisión → Hecho**.

| Regla | Detalle |
|---|---|
| WIP | Máximo 2 issues en curso por persona |
| Revisión | Nadie aprueba su propio PR; se exige 1 aprobación de alguien de otro frente |
| Contratos primero | La especificación OpenAPI y los esquemas de telemetría se aprueban antes de implementar contra ellos |
| Cierre | Definición de terminado: criterios de aceptación cumplidos + tests/evidencia + PR revisado |
| Integración | Un capitán de integración rotativo por sprint responde por que `main` siempre despliegue |
| Ceremonias | Daily asíncrono y una sincronización de 30 minutos los lunes |
| Entregables | En texto versionable (Markdown, PlantUML, Mermaid). Los PDF se convierten antes de nuevos cambios |

---

## 4. Estado del tablero

Los milestones y las etiquetas están creados y las issues #17–#25 y #35–#45 quedaron cargadas con
milestone, frente y owner.

### 4.1. Por qué no se puede crear el tablero de Projects (25/10/2026)

El tablero de GitHub Projects con las cinco columnas **no se puede crear** en este repositorio.

- El repositorio pertenece a `infraitgidas`, que es una **cuenta de usuario** (`type: User`), no una
  organización.
- Los Projects V2 pertenecen a la cuenta dueña. La cuenta autenticada (`BlancoCavallero`) tiene
  permisos `push` y `triage` sobre el repo, pero no `admin`, así que GitHub rechaza la creación:

  ```
  GraphQL: BlancoCavallero does not have permission to create projects on ownerId U_kgDOEEeTgw. (createProjectV2)
  ```

- El scope del token **ya está concedido** (`gh auth refresh -s project,read:project`); no era el
  problema.

### 4.2. Alternativa adoptada: etiquetas de estado

**Decisión (25/10/2026):** el tablero se representa con las etiquetas `estado:*` de §2. No se crea
un archivo de tablero ni se mantiene una copia en Markdown: la fuente de verdad son las issues y sus
etiquetas.

Las cinco columnas se leen así:

- **Backlog** — abiertas sin `estado:*`
- **Listo** — `estado:listo`
- **En curso** — `estado:en-curso`
- **En revisión** — `estado:en-revision`
- **Hecho** — cerradas

Consultas equivalentes: `is:issue is:open label:"estado:listo"`, etc. Cualquiera puede armar la
vista con los filtros de GitHub Issues.

Alternativas descartadas:

1. **Project V2 creado por la cuenta `infraitgidas`** (o que esa cuenta sume `admin` a
   `BlancoCavallero`). Es el tablero canónico, pero depende de quien administra la cuenta
   institucional.
2. **Project V2 bajo la cuenta personal `BlancoCavallero`**. Se puede crear, pero el tablero queda
   en una cuenta personal y no en la institucional.
