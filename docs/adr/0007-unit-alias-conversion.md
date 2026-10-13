# ADR 0007: Semántica de conversión de alias de unidad para métricas RUM

- **Estado**: Aceptado
- **Fecha**: 2026-10-13
- **Autores**: Federico Cavallero (Equipo InfraIT — GIDAS UTN FrLP)
- **Decisión relacionada**: Issue #41 (ISS-S3-02), `openspec/changes/ISS-S3-02/specs/ingest-normalization/spec.md` (NORM-3), `docs/architecture/ContratoIngestaRUM.md`, OpenAPI `RumMetric.unit`

## Contexto

Las unidades canónicas del contrato son `ms` para `TTFB`/`FCP`/`XHR_LATENCY` y `count` para `JS_EXCEPTION_RATE`/`RAGE_CLICK`; el enum `RumMetric.unit` de OpenAPI es `[ms, count]`. Hoy un evento declarado en segundos (`unit: "s"`) o un conteo en plural (`"counts"`) se rechaza (`invalid_unit`) aunque represente la misma medición física. Las duraciones RUM del navegador son nativamente milisegundos (W3C/Navigation Timing), mientras que el ecosistema más amplio (OTel/Prometheus) emite convencionalmente segundos — la misma cantidad llega entonces bajo etiquetas distintas.

El criterio 2 ("resolver inconsistencias de unidad") requiere que el sistema acepte estas representaciones. Las preguntas abiertas son: convertir o rechazar; qué alias; y cómo hacer la conversión segura contra la doble aplicación.

## Decisión

La normalización **convierte una familia acotada de alias de unidad declarados a la unidad canónica**, indexada por la **unidad de entrada declarada**:

```python
UNIT_CONVERSIONS: dict[str, tuple[str, float]] = {   # declarada -> (canónica, factor)
    "ms": ("ms", 1.0), "msec": ("ms", 1.0), "millis": ("ms", 1.0),
    "s": ("ms", 1000.0), "sec": ("ms", 1000.0), "secs": ("ms", 1000.0),
    "count": ("count", 1.0), "counts": ("count", 1.0),
}
```

- La familia `s` (`s`, `sec`, `secs`, `msec`, `millis`) resuelve a `ms`; `counts` resuelve a `count`; las canónicas `ms`/`count` son identidad.
- La conversión es escalar y preserva la magnitud (`1 s = 1000 ms`).
- **Las unidades desconocidas pasan sin cambios** y siguen siendo rechazadas (`invalid_unit`) por la validación.
- La coherencia tipo/unidad (`UNIT_BY_TYPE`) sigue siendo responsabilidad de la validación: p. ej., un alias de duración sobre una métrica de conteo resuelve a `ms` y luego se rechaza como `invalid_unit`.
- El enum `RumMetric.unit` de OpenAPI se amplía a `[ms, count, s, sec, secs, msec, millis, counts]` (ARCH-6) para que el contrato documentado coincida con la flexibilidad en runtime; los valores canónicos almacenados y en respuesta siguen siendo `ms`/`count`.

### Idempotencia

La conversión está indexada por la unidad declarada y se aplica exactamente una vez. Tras una pasada la unidad es canónica, por lo que una segunda pasada mapea `ms → ("ms", ×1)` / `count → ("count", ×1)` — un no-op. Un valor canónico nunca se reinterpreta. Los tests verifican `normalize(normalize(e)) == normalize(e)` para cada alias y que ×1000 se aplica una sola vez.

## Consecuencias

Positivas:
- Mediciones idénticas bajo etiquetas distintas convergen a una única representación canónica, lo que permite una agregación y exportación consistentes (S3-04).
- La conversión preserva la magnitud, por lo que la señal de anomalía queda intacta (ADR 0005).
- Idempotente por construcción; la doble normalización es inofensiva.

Negativas / trade-offs:
- Amplía el conjunto de entrada aceptado: entradas antes rechazadas ahora se aceptan (cambio de semántica del contrato, R1). Se mitiga actualizando OpenAPI y documentando la flexibilidad.
- La lista exacta de alias es una decisión de producto, no proviene de un único estándar; es intencionalmente acotada y explícita.

Riesgos:
- Deriva entre los datos de conversión y las reglas de validación si los registros divergen; se mitiga manteniendo ambos en `ingest_policy.py` como fuente única (R7).

## Alternativas Consideradas

| Alternativa | Descripción | Razón de descarte |
|---|---|---|
| Rechazar todas las unidades no canónicas | Mantener el rechazo estricto `[ms, count]` | Frustra el criterio 2; la unidad es una representación de la misma cantidad. |
| Re-derivar la unidad a partir del valor | Adivinar la unidad a partir de la magnitud | Ambiguo y no determinista; puede cambiar la magnitud silenciosamente. |
| Normalizar solo en el esquema OpenAPI | Documentar los alias sin convertirlos | La documentación divergiría del runtime; no se almacena un valor canónico. |

## Recursos / Compatibilidad

- **Stack**: sin dependencias nuevas; una búsqueda en dict por métrica.
- **Recursos**: CPU despreciable; sin cambios de almacenamiento; `<2GB RAM`, CPU-only, `$0/mes`.

## Referencias

- `docs/architecture/ContratoIngestaRUM.md` (matriz de validación RUM)
- `openspec/changes/ISS-S3-02/specs/ingest-normalization/spec.md` (NORM-3), `specs/architecture/spec.md` (ARCH-6)
- `openspec/specs/openapi.yaml` (`RumMetric.unit`)
- [ADR 0005](0005-representation-only-normalization.md)
