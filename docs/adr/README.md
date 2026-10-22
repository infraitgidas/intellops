# Architecture Decision Records (ADR)

Este directorio contiene los Architecture Decision Records del proyecto IntellOps.

## ¿Qué es un ADR?

Un ADR documenta una decisión arquitectónica significativa: contexto, decisión, consecuencias y alternativas consideradas.

## Formato

Cada ADR sigue el formato [Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):

```markdown
# TÍTULO: [Título descriptivo de la decisión]

- **Estado**: [propuesto | aceptado | deprecado | supersedido]
- **Fecha**: YYYY-MM-DD
- **Autores**: [nombre]
- **Contexto**: ...
- **Decisión**: ...
- **Consecuencias**: ...
- **Alternativas consideradas**: ...
- **Referencias**: ...
```

## Convenciones

- **Numeración**: Secuencial, 4 dígitos (`0001`, `0002`, ...)
- **Nomenclatura**: `NNNN-titulo-con-guiones.md`
- **Estados**:
  - `propuesto` → En discusión, no implementado
  - `aceptado` → Implementado y vigente
  - `deprecado` → Ya no aplica
  - `supersedido` → Reemplazado por otro ADR

## ADRs del Proyecto

| # | Título | Estado | Fecha |
|---|--------|--------|-------|
| 0000 | [Plantilla de ADR](0000-template.md) | Plantilla | — |
| 0001 | [Reemplazo de ELK Stack por Grafana + Loki + Prometheus](0001-reemplazo-elk-por-grafana-loki-prometheus.md) | Aceptado | 2026-05-27 |
| 0002 | [Pipeline de ingesta RUM asíncrono en proceso y nomenclatura `/telemetry/*`](0002-pipeline-ingesta-async.md) | Aceptado | 2026-09-25 |
| 0003 | [Ownership de tenant en la persistencia de telemetría y read path app-scoped](0003-ownership-tenant-read-path.md) | Aceptado | 2026-09-29 |
| 0004 | [Normalizar antes de validar en el pipeline de ingesta RUM](0004-normalize-before-validate.md) | Aceptado | 2026-10-13 |
| 0005 | [Normalización de solo representación (nunca recortar magnitudes)](0005-representation-only-normalization.md) | Aceptado | 2026-10-13 |
| 0006 | [Canonicalización de `error_type` en código (sin catálogo DDL)](0006-error-type-in-code-catalog.md) | Aceptado | 2026-10-13 |
| 0007 | [Semántica de conversión de alias de unidad para métricas RUM](0007-unit-alias-conversion.md) | Aceptado | 2026-10-13 |
| 0008 | [Dataset operativo para ML — pull HTTP del read path y anomalía anclada a la serie](0008-ml-dataset-http-pull-series-anchor.md) | Aceptado | 2026-10-14 |
| 0009 | [PostgreSQL 16 como base de datos del MVP (reemplazo de SQLite WAL)](0009-postgresql-16-como-base-de-datos.md) | Aceptado | 2026-09-11 |
| 0010 | [Arquitectura de 4 contenedores para el MVP (monolito modular desacoplado)](0010-arquitectura-de-4-contenedores.md) | Aceptado | 2026-08-12 |
