# Proposal: A.4 — Generador sintético y anomalías inyectadas etiquetadas (GitHub #66)

> **Decisión en una línea**: un script reproducible (`ml/data/generate_labeled_dataset.py`, numpy + stdlib) genera series RUM sintéticas con el contrato M4, anomalías etiquetadas por tipo y severidad, *hard negatives* y split temporal 80/20; exporta CSV + `manifest.json` y ofrece un lector que B.6 usa sin tocar la ingesta.

## Intent

B.6 (baseline estadístico vs Isolation Forest) necesita un dataset **etiquetado**. No hay datos reales del laboratorio (puede que no existan durante la v1). El generador actual (`generate_mock_dataset.py`, EDA de ISS-S3-05) no etiqueta, no tiene split y sortea anomalías al azar por fila. Resultado esperado: un dataset rico en realismo, honesto sobre su origen sintético, que permita medir F1, recall, precisión y **tasa de falsos positivos** (KPI del proyecto).

## Scope

### In Scope
1. Script `ml/data/generate_labeled_dataset.py` con CLI (`--seed`, `--days`, `--bucket-seconds`, `--apps`, `--out-dir`).
2. Modelo generativo: 3 perfiles de app, estacionalidad diaria y semanal, tendencia, ruido AR(1) heterocedástico, correlación entre métricas, huecos por buckets sin sesiones.
3. Catálogo de 6 tipos de anomalía × 3 severidades, más 2 patrones de *hard negative*.
4. Agenda estratificada de eventos (mínimos por combinación y split, sin solapes, sin cruzar el corte).
5. Export CSV (contrato M4 + etiquetas) + `manifest.json` (sha256, conteos, rangos); lector `load_labeled_dataset`.
6. Tests `tests/test_labeled_dataset.py` (marker `unit`), `ml/data/README.md`, regla `.gitignore` para `ml/data/synthetic/`.

### Out of Scope
- Entrenar o comparar modelos (B.6). Persistir `ML_MODEL`.
- Cambios en `src/api`, `src/ml`, `generate_mock_dataset.py`, `rum_mock.json`, el notebook EDA, `CHANGELOG.md`, `openapi.yaml`.
- Nuevas dependencias (pandas, pyarrow, scipy). Commit de datos generados.

## Approach

Un solo módulo (KISS en estructura), rico en datos. Streams numpy independientes por `(app, métrica)` vía `SeedSequence.spawn`. La severidad se mide en sigmas del desvío **local** de la serie limpia desestacionalizada. Ver `design.md`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `ml/data/generate_labeled_dataset.py` | New | Generador, export y lector |
| `tests/test_labeled_dataset.py` | New | Tests unitarios (rápidos, parámetros chicos) |
| `ml/data/README.md` | New | Formato, columnas, catálogo, split, limitaciones |
| `.gitignore` | Modified | Ignora `ml/data/synthetic/` |
| `openspec/changes/A4/` | New | Artefactos SDD |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| El modelo aprende el generador y no el fenómeno | High | README con limitaciones explícitas; no reportar F1 "de producción"; revalidar con datos reales (R.2) |
| sha256 no reproducible entre plataformas o versiones de numpy | Med | `manifest.json` registra versión de numpy; README documenta el alcance del hash |
| Agenda imposible con ventanas chicas | Low | Error explícito; defaults calibrados |

## Rollback Plan

Revert de los commits del cambio. No toca runtime ni DB: rollback sin impacto.

## Success Criteria

- [ ] Script reproducible (seed fija) en `ml/`.
- [ ] Series con anomalías de distinto tipo y severidad, etiquetadas.
- [ ] Dataset exportado y documentado (formato, columnas, rangos).
- [ ] Split train/validation definido (temporal).
- [ ] Consumible por B.6 sin acoplamiento a la ingesta.
