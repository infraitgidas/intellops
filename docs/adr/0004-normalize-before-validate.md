# ADR 0004: Normalizar antes de validar en el pipeline de ingesta RUM

- **Estado**: Aceptado
- **Fecha**: 2026-10-13
- **Autores**: Federico Cavallero (Equipo InfraIT — GIDAS UTN FrLP)
- **Decisión relacionada**: Issue #41 (ISS-S3-02), `openspec/changes/ISS-S3-02/` (proposal, specs ARCH-5/NORM-1..7), `docs/architecture/PipelineIngestaRUM.md`, `docs/adr/0002-pipeline-ingesta-async.md`

## Contexto

El issue #41 especifica el flujo de calidad de datos `Raw → Validation → Normalization → Storage`. Hoy la ruta de ingesta valida por evento con una política de solo rechazo (`src/api/domain/services/ingest_policy.py`: `invalid_unit`, `invalid_metric_type`, `invalid_timestamp`) y la única coerción de representación vive implícitamente en el worker de infraestructura (`queue.py` `_build_rows`/`_parse_ts`, post-`202`), sin nombre y no testeable por unidad.

El orden literal del issue es contraproducente para los criterios 2 y 3 ("resolver inconsistencias de unidad", "resolver inconsistencias de nombres"): si la validación corre primero, rechaza las mismas representaciones de unidad/nombre que la normalización debe resolver. Se requiere una etapa de normalización con nombre, y su posición determina si esos criterios son alcanzables.

## Decisión

El orden del pipeline es **`Raw → Normalize → Validate → Enqueue → Store`**. Una etapa de normalización pura y sin E/S (`src/api/domain/services/ingest_normalizer.py`) corre por evento en `IngestService.process_batch` **antes** de `ingest_policy`:

```python
payload = event.model_dump(mode="json")
payload = normalizer(payload)        # canonicalización de representación únicamente
reason = validator(payload)          # autoridad única de rechazo
if reason is None:
    await self._queue.enqueue(QueuedEvent(..., payload=payload))
```

La normalización nunca decide la aceptación y nunca lanza excepciones; deja pasar todo valor que no pueda representar canónicamente para que la validación lo rechace. Se preserva la semántica parcial `202` por evento.

## Consecuencias

Positivas:
- Las inconsistencias de unidad/nombre/timestamp son resolubles, lo que hace alcanzables los criterios 2–3 mientras la validación sigue siendo la autoridad única de rechazo.
- Un único responsable de la normalización; las funciones puras son testeables por unidad de forma aislada (TDD estricto, S3-06).
- Las fallas de normalización se exponen al cliente como rechazos por evento en lugar de desaparecer en la dead-letter del worker.

Negativas / trade-offs:
- Toca la ruta de request (CPU despreciable, transformaciones puras de dict en memoria).
- Amplía el conjunto de entrada aceptado (ver ADR 0007); requiere documentar la flexibilidad del contrato (ARCH-6).

Riesgos:
- Debe garantizarse la idempotencia de la conversión (ADR 0007).

## Alternativas Consideradas

| Alternativa | Descripción | Razón de descarte |
|---|---|---|
| Orden literal del issue (validar primero) | Mantener `Raw → Validation → Normalization → Storage` | Hace inalcanzables los criterios 2–3: la validación de solo rechazo descarta los alias antes de que la normalización corra. |
| Normalizar en el worker de infraestructura (refactor de `_build_rows`) | Normalización post-`202` | Las reparaciones/rechazos son invisibles al cliente y alimentan la dead-letter; las reglas de negocio se filtran a infraestructura; mala testeabilidad por unidad pura. |
| Normalizar en el límite de escritura del repositorio | Canonicalizar al insertar filas | Los repositorios no deben contener reglas de negocio; solo tests atados a la BD; no puede reportar rechazos. |

## Recursos / Compatibilidad

- **Stack**: sin dependencias nuevas; Python puro dentro de la capa de dominio existente.
- **Recursos**: solo transformaciones en memoria — sin proceso nuevo, se mantiene `<2GB RAM`, CPU-only, `$0/mes`.

## Referencias

- `openspec/changes/ISS-S3-02/proposal.md`, `specs/architecture/spec.md` (ARCH-5), `specs/ingest-normalization/spec.md` (NORM-1)
- `docs/architecture/ContratoIngestaRUM.md`
- [ADR 0002](0002-pipeline-ingesta-async.md)
