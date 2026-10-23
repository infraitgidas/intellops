# Flujo de trabajo en GitHub

**Estado**: vigente desde el 23/10/2026 (issue A.1).
**Fuente**: plan raíz "IntellOps — Plan de Gestión, Roadmap y EDT" §Modelo de trabajo;
`docs/business/plan-gestion-roadmap-edt.md` §3; `docs/business/issues-fases-abc.md` §2.

Este documento define cómo se etiqueta y se mueve una issue en el repositorio. Si una issue no
cumple estas reglas, no entra al sprint.

---

## 1. Hitos (milestones)

Los hitos son los cinco del plan raíz. Miden resultados del producto, no ventanas de trabajo.

| Milestone | Fecha | Qué cierra |
|---|---|---|
| `M0 — Base cerrada` | 13/11/2026 | Contratos aprobados, ADRs, EDT cargado como issues y primer dato de punta a punta visible |
| `M1 — Piloto medido y v1 entregada` | 18/12/2026 | Sitio piloto medido con RUM y sondas, demo ante GIDAS, alerta por Telegram, tests ≥ 70 % |
| `M2 — Detección ML y dashboard` | H1 2027 (a fijar) | Detección ML sobre series, dashboard, dataset etiquetado como condición de entrada |
| `M3 — LLM local RCA` | 2027 (a fijar) | LLM local que explica anomalías y líneas de extensión |
| `M4 — Prototipo y experimentación` | 2028 (a fijar) | Prototipo inicial y experimentación integrada |

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

El tablero (GitHub Projects con las cinco columnas) **queda pendiente**: el token de `gh` no tiene
el scope `project`. Para crearlo hay que ejecutar `gh auth refresh -s project,read:project` y luego
crear el Project V2 y cargar las issues.
