# ADR 0006: Canonicalización de `error_type` en código (sin catálogo DDL)

- **Estado**: Aceptado
- **Fecha**: 2026-10-13
- **Autores**: Federico Cavallero (Equipo InfraIT — GIDAS UTN FrLP)
- **Decisión relacionada**: Issue #41 (ISS-S3-02), `openspec/changes/ISS-S3-02/specs/ingest-normalization/spec.md` (NORM-4), `docs/architecture/ContratoIngestaRUM.md`

## Contexto

`js_exception.error_type` es una columna `TEXT NOT NULL` de texto libre **sin catálogo** (`openspec/specs/database/ddl_v1.0.sql`). El contrato lista valores de ejemplo (`TypeError`, `ReferenceError`, `RangeError`, `UnhandledRejection`, `Other`). La normalización de ingesta debe hacer consistente el nombrado para que el agrupamiento y la agregación posteriores sean estables.

Un cambio previo (ISS-S3-01) difirió explícitamente "Normalización de error_type a catálogo (ISS-S3-02, #41)" a este cambio. La pregunta es si "catálogo" significa una tabla real en la BD (con DDL, datos semilla y un mapeo de backfill para las filas de texto libre existentes) o una canonicalización en código con un bucket de fallback.

Restricciones vigentes: CPU-only, `<2GB RAM`, `$0/mes`, y minimizar el riesgo de migración.

## Decisión

`error_type` se canonicaliza **en código** (`ingest_normalizer.py`): se recortan espacios en blanco, se aplica case-fold, se aplica un mapa de alias acotado, y todo valor desconocido o no mapeado se lleva a `Other`. El catálogo vive como un frozenset compartido con la validación:

```python
ERROR_TYPE_CATALOG = frozenset({
    "Error", "EvalError", "RangeError", "ReferenceError", "SyntaxError",
    "TypeError", "URIError", "AggregateError", "InternalError",   # built-ins de ECMAScript
    "UnhandledRejection", "Other",                                # ejemplos del contrato
})
ERROR_TYPE_ALIASES: dict[str, str]  # alias con case-fold -> canónico
```

**No se introducen DDL, tabla de catálogo ni migración.** La columna de la BD permanece `TEXT`. Solo se canonicaliza la etiqueta; los campos portadores de anomalía (`message`, `stack_trace`, valores) nunca se reescriben.

Esto refleja el principio OTel/`error.type` (predecible, de baja cardinalidad, nombre de clase canónico, fallback estable estilo `_OTHER`), con `Other` del proyecto como bucket de fallback.

## Consecuencias

Positivas:
- Sin migración, sin datos semilla, sin backfill; reversible revirtiendo el PR.
- `error_type` estable y de baja cardinalidad para el agrupamiento y la agregación posteriores.
- Los valores desconocidos nunca se pierden — se agrupan en `Other` en lugar de rechazarse.

Negativas / trade-offs:
- El catálogo es código, no datos: agregar un nuevo tipo de error canónico requiere un cambio de código (aceptable a esta escala).
- Las filas de texto libre ya persistidas no se rellenan con backfill (solo hacia adelante; fuera de alcance).

Riesgos:
- Agrupamiento excesivo (over-bucketing) silencioso si falta un tipo importante del catálogo; se mitiga revisando el catálogo contra los ejemplos del contrato y los built-ins de ECMAScript.

## Alternativas Consideradas

| Alternativa | Descripción | Razón de descarte |
|---|---|---|
| Tabla de catálogo en BD + migración | Tabla `error_type`, FK/seed, mapeo de backfill para las filas existentes | Requiere DDL, semilla y backfill; mayor costo operativo y riesgo de migración para una etiqueta de baja cardinalidad. |
| Rechazar `error_type` desconocido | Tratar los valores irreconocibles como inválidos | Pierde datos y rompe la flexibilidad `202`; la etiqueta no es la señal. |
| Mantener el texto libre crudo | Sin canonicalización | Deja el nombrado inconsistente, frustrando el criterio 3 y el agrupamiento estable. |

## Recursos / Compatibilidad

- **Stack**: sin dependencias nuevas; datos puros en código.
- **Recursos**: sin DDL, sin almacenamiento extra; `<2GB RAM`, CPU-only, `$0/mes` sin cambios.

## Referencias

- `docs/architecture/ContratoIngestaRUM.md` (matriz de excepciones JS)
- `openspec/changes/ISS-S3-02/specs/ingest-normalization/spec.md` (NORM-4)
- `openspec/changes/archive/2026-09-29-ISS-S3-01/proposal.md:30` (diferimiento de la normalización de error_type)
- [ADR 0004](0004-normalize-before-validate.md)
