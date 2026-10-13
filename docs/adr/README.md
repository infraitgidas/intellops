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
| [0001](0001-reemplazo-elk-por-grafana-loki-prometheus.md) | Reemplazo de ELK Stack por Grafana + Loki + Prometheus | Aceptado | 2026-05-27 |
| [0002](0002-pipeline-ingesta-async.md) | Pipeline de ingesta RUM asíncrono en proceso y nomenclatura `/telemetry/*` | Aceptado | 2026-09-25 |
| [0003](0003-ownership-tenant-read-path.md) | Ownership de tenant en la persistencia de telemetría y read path app-scoped | Aceptado | 2026-09-29 |
| [0004](0004-normalize-before-validate.md) | Normalizar antes de validar en el pipeline de ingesta RUM | Aceptado | 2026-10-13 |
| [0005](0005-representation-only-normalization.md) | Normalización de solo representación (nunca recortar magnitudes) | Aceptado | 2026-10-13 |
| [0006](0006-error-type-in-code-catalog.md) | Canonicalización de `error_type` en código (sin catálogo DDL) | Aceptado | 2026-10-13 |
| [0007](0007-unit-alias-conversion.md) | Semántica de conversión de alias de unidad para métricas RUM | Aceptado | 2026-10-13 |
