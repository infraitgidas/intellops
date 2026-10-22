# Comparación: Plan de Gestión, Roadmap y EDT vs `develop` + `gestionProyecto`

Documento de contraste punto a punto entre el plan de gestión propuesto por la dirección
(`IntellOps — Plan de Gestión, Roadmap y EDT.md`, Oct 16, 2026) y el estado real del repositorio
en `develop` y en la rama `gestionProyecto`.

**Alcance:** inventario comparativo. No emite decisiones ni propone acciones; solo registra la
diferencia entre lo que declara el doc raíz y lo que existe (o no) en el repositorio.

**Base de contraste:** `docs/fix` partiendo de `origin/develop @1a46eb4` y de la rama
`gestionProyecto`.

---

## Comparación punto a punto

| # | Punto | Lo que dice el doc | Realidad (develop / gestionProyecto) | Veredicto |
|---|-------|--------------------|--------------------------------------|-----------|
| 1 | EDT | "No hay EDT en el repo" | develop SÍ: `docs/business/EDT intellops.md` (bdca8c2) | CONTRADICE |
| 2 | Cronograma | "No hay cronograma" | develop SÍ existe | CONTRADICE |
| 3 | ADR de base de datos | SQLite; "config.yaml dice SQLite" | El repo ya usa **PostgreSQL 16**: `openspec/config.yaml` declara PostgreSQL (nunca dijo SQLite) y el DDL vive en `ddl_v1.0.sql` + Alembic 0001–0004. El ADR faltante existía en `gestionProyecto` y se portó como **`docs/adr/0009`**. | CONTRADICE (el doc atribuye SQLite a `config.yaml`); decisión ya resuelta (ADR-0009) |
| 4 | Roadmap / hitos | Hitos M0–M4 | gestionProyecto: roadmap F0–F4 | SUPERPONE |
| 5 | Probe HTTP (#12) | — | `demo/probe_ttfb.py` UNTRACKED | COINCIDE |
| 6 | Sondas TLS y DNS | M1 | No existe en ninguna rama | FALTA |
| 7 | Agente RUM | M1 | Investigado, sin código | FALTA |
| 8 | Piloto | S4 / 7-dic | No existe | FALTA |
| 9 | Alertmanager | M1 básico | Planificado, sin código | FALTA |
| 10 | WIP≤2, sync lunes, capitán rotativo, respaldos por frente | Sección 6 | Ninguna rama | FALTA |
| 11 | RACI | Sección 6 | No existe (3 asignaciones dispersas) | FALTA |
| 12 | Bus factor / cohorte | Sección 7 | governance/continuity.md existe, sin bus factor/cohorte | PARCIAL |
| 13 | Issues S2/S3 | — | Publicadas #35–#45, sin etiquetas | PARCIAL |
| 14 | Colisión ADR-0002 | — | develop: 0002-pipeline-ingesta-async vs gestionProyecto: 0002-reemplazo-sqlite-por-postgresql | COLISIÓN (renumerar a 0009) |
| 15 | Triple línea base | doc M0–M4 | develop EDT (8 sprints 24/08) · gestionProyecto roadmap F0–F4 · doc M0–M4 | COLISIÓN TRIPLE |
| 16 | Triple MVP | MVP M1 (RUM+sondas) | brief-v2 (MVP-0 SQLite / MVP-1 LGTM) · roadmap-mvp-pps · doc | COLISIÓN TRIPLE |
| 17 | brief-v2 | — | Dos versiones divergentes entre refs | COLISIÓN |
| 18 | docs/adr/README.md | — | Tabla de ADRs vacía | FALTA |
| 19 | PR #7 | +5.399 líneas sin revisión | develop: docs/pr-007-review.md | COINCIDE (hay análisis) |
| 20 | Baseline develop local | — | develop local quedó alineado a `origin/develop @1a46eb4` (partía de `1707caf`, 24 commits atrás) | DESFASE (resuelto) |
| 21 | Arranque S1 19-oct-2026 | S1 empieza 19-oct | develop ya tiene S2 archivado (`openspec/changes/archive/`) y S3 en curso (ramas `ISS-S3-01/02/04/05`) | ATRASADO ~2 sprints |

---

## Leyenda de veredictos

| Veredicto | Significado |
|-----------|-------------|
| **CONTRADICE** | El doc afirma la ausencia de algo que sí existe en el repositorio. |
| **CORREGIDO** | El dato desactualizado del doc ya fue resuelto en otro artefacto o rama. |
| **SUPERPONE** | El doc y otra fuente describen el mismo objeto con esquemas distintos (solapamiento). |
| **COINCIDE** | El doc y la realidad del repositorio concuerdan. |
| **FALTA** | El elemento declarado no existe en ninguna rama evaluada. |
| **PARCIAL** | El elemento existe pero está incompleto o sin el detalle declarado. |
| **COLISIÓN** | Dos artefactos usan el mismo identificador para contenidos distintos. |
| **COLISIÓN TRIPLE** | Tres líneas base divergentes cubren el mismo eje (calendario o MVP). |
| **DESFASE** | Una copia local está atrás de su referencia remota. |
| **ATRASADO** | El avance real del repositorio está por delante del calendario supuesto por el doc. |

---

## Nota de fuentes

- **Doc raíz:** `IntellOps — Plan de Gestión, Roadmap y EDT.md` (Oct 16, 2026), archivo actualmente
  *untracked*. Se usa solo como objeto de comparación, no como fuente de contenido.
- **Rama `develop`:** artefactos `docs/business/EDT intellops.md`, `docs/business/issues-s1-s2.md`,
  `docs/business/issues-s2-s3.md`, `docs/adr/`, `docs/pr-007-review.md`, `openspec/config.yaml`,
  `openspec/specs/database/ddl_v1.0.sql`, `src/api/infrastructure/db/migrations/`.
- **Rama `gestionProyecto`:** `gestionProyecto/roadmap/roadmap-producto.md`,
  `gestionProyecto/roadmap/roadmap-mvp-pps.md`, `gestionProyecto/marco/03-diseno.md`,
  `gestionProyecto/marco/04-especificaciones.md` y
  `gestionProyecto/decisiones/caso-postgresql-vs-sqlite.md` (integrados en esta rama por cherry-pick).
- **Trabajo no versionado:** `demo/probe_ttfb.py` (untracked).

> Las filas 20 y 21 reflejan el estado al cierre de esta reconciliación: el baseline local de
> `develop` ya fue alineado a `1a46eb4` y el archivado de sprints puede seguir avanzando.
