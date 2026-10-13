# PREPROPOSAL — ISS-S3-02: Normalización y calidad de datos

**Artefacto**: `gentle-ai.sdd-preproposal/v1`
**Cambio**: ISS-S3-02 (GitHub #41). **Rama**: `feat/ISS-S3-02`. **Base**: `origin/develop` @ `1a46eb4`.
**Revision**: `r1`. **Fecha**: 2026-10-13.
**Store**: openspec (repo-local). **Idioma**: español neutro técnico.
**Autor**: orquestador (las decisiones de producto son propiedad del orquestador; son intención, no evidencia).

---

## Exploración

- **Resultado**: "Ready for Proposal" (era condicional a Q1–Q3, ahora resuelto).
- **Referencia OpenSpec**: `openspec/changes/ISS-S3-02/exploration.md`
- **Referencia Engram**: `sdd/ISS-S3-02/explore`
- **Hallazgo clave**: la única normalización hoy es implícita y está mal ubicada en el worker de infraestructura (`queue.py._build_rows`/`_parse_ts`, post-`202`); no hay una etapa de normalización con nombre ni canonicalización de unidad/nombre.

## Investigación (research)

- **Request**: RQ1 canonicalización de timestamps; RQ2 conversión de alias de unidad → canónica; RQ3 canonicalización de nombre de métrica y `error_type`; RQ4 política de valores ausentes/inválidos.
- **Clases solicitadas/observadas**: `open-web` (websearch/webfetch) y `documentation` (Context7) — ambas **DISPONIBLES**. **Admisión**: ACEPTADA.
- **Resultado**: `done`.
- **Referencias de evidencia**: `openspec/changes/ISS-S3-02/research.md` (revision `r1`, outcome `done`, 22 sources, 25 claims). Engram discovery `obs-7a8aedcf0ba7123a`.
- **Conflictos resueltos**: evidencia externa vs contrato del proyecto — el contrato del proyecto gana en la unidad canónica de duración (`ms`), la notación de conteo (`count`), el formato de nombre de métrica (`UPPER_SNAKE`) y la notación del error desconocido (`Other`); ver `research.md` §5.

## Decisiones de producto (orquestador-owned; confirmadas; no autoritativas como evidencia)

| # | Decisión | Resuelve | Estado |
|---|----------|----------|--------|
| a | Las inconsistencias de unidad se resuelven por **conversión de alias conocidos a la unidad canónica** (`ms`/`count`), no por rechazo estricto. | Exploration Q1 | confirmed (evidencia C10–C15) |
| b | El orden del pipeline es **normalizar ANTES de validar**: `Raw → Normalize → Validate → Enqueue → Store`. La validación sigue siendo la autoridad única de rechazo; la normalización resuelve representaciones que la validación de otro modo rechazaría. | Exploration Q2 | confirmed (arquitectura, no evidencia) |
| c | La normalización de `error_type` es **canonicalización en código** (trim/case + mapa de alias, desconocido → `Other`); **sin catálogo DDL / sin migración**. | Exploration Q3 | confirmed (C16, C17, C19) |
| d | **RESTRICCIÓN DURA**: la normalización es de solo representación; NUNCA DEBE recortar/reparar magnitudes o valores fuera de rango (los rangos de sanity son cotas de rechazo; esos valores son la señal de anomalía). | `ContratoIngestaRUM.md:30` | confirmed (C4, C7, C21, C23, C25) |
| e | El conjunto de alias de unidad aceptado es la **familia amplia de duración**: `s`, `sec`, `secs`, `msec`, `millis` → `ms`; `counts` → `count`; más las canónicas `ms`/`count`. Las unidades desconocidas aún se rechazan. | `research.md` §5 especificidad del conjunto de alias | confirmed |
| f | **Los valores de conteo no enteros** (`JS_EXCEPTION_RATE`, `RAGE_CLICK`) se **rechazan** (`invalid_range`); sin redondeo (el redondeo es un cambio de magnitud). | `research.md` X5 | confirmed |

La decisión (a) se aplica mediante una conversión alias→canónica idempotente indexada por la unidad de entrada declarada.

## proposal_ready

**`true`** — investigación `done` con evidencia válida; decisiones de producto (a–f) confirmadas; referencias de evidencia válidas; estado del cambio openspec listo. Habilitado para invocar `sdd-propose`.

## Pendiente orquestador-owned

- Nada bloqueante. Ítems diferidos intencionalmente a spec/design (no bloqueantes, según `research.md` §8): el conjunto exacto de defaults de campos opcionales para valores ausentes; la cota opcional de rechazo de timestamps futuros.
