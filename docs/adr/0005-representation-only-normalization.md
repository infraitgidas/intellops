# ADR 0005: Normalización de solo representación (nunca recortar magnitudes)

- **Estado**: Aceptado
- **Fecha**: 2026-10-13
- **Autores**: Federico Cavallero (Equipo InfraIT — GIDAS UTN FrLP)
- **Decisión relacionada**: Issue #41 (ISS-S3-02), `openspec/changes/ISS-S3-02/specs/ingest-normalization/spec.md` (NORM-6), `docs/architecture/ContratoIngestaRUM.md:30`

## Contexto

`docs/architecture/ContratoIngestaRUM.md` afirma explícitamente que los rangos por métrica son cotas de **sanity/rechazo**, no cotas de calidad: "un TTFB de 9000ms es un dato legítimo que el sistema acepta — es justamente el valor que el sistema debe detectar como anomalía."

El objetivo de investigación del sistema (observabilidad predictiva) depende de que las magnitudes portadoras de anomalía lleguen intactas al motor de ML. Una etapa de normalización que "sanee" valores (recorte, límite máximo, redondeo, o sustituya el tiempo de ingesta por un timestamp inválido) destruiría exactamente la señal que el producto debe detectar.

## Decisión

La normalización es de **representación únicamente**. PUEDE:
- canonicalizar timestamps a UTC con zona horaria explícita (y heredar el timestamp del envelope cuando falta el timestamp de la métrica);
- convertir alias de unidad a unidades canónicas (ADR 0007);
- canonicalizar nombres de tipo de métrica y `error_type` (ADR 0006/0007);
- coaccionar cadenas numéricas finitas (`"120.5"` → `120.5`) y recortar espacios en blanco.

NO DEBE recortar, limitar, redondear ni reescribir de otro modo magnitudes, y NO DEBE reemplazar un timestamp inválido/naïve/ausente con `now()`. Los valores no finitos (`NaN`, `Infinity`) nunca se coaccionan. Los valores fuera de rango y los conteos no enteros se dejan intactos para que la validación los rechace (`invalid_range`). El fallback silencioso `now()` del worker se elimina (`queue.py`).

## Consecuencias

Positivas:
- Se preserva el objetivo de anomalías del ML: el TTFB de `9000ms` y otros valores legítimos pero inusuales pasan sin cambios.
- Frontera clara y auditable entre representación (normalización) y semántica (validación).
- Se alinea con el precedente externo: Prometheus rechaza las muestras fuera de límites en lugar de reescribirlas; la validación de JSON Schema no transforma instancias.

Negativas / trade-offs:
- Los clientes no pueden confiar en que el servidor "arregle" magnitudes inválidas; en su lugar reciben un código de rechazo explícito.
- Los conteos no enteros siguen siendo un rechazo, no una coerción (Decisión f).

Riesgos:
- Un contribuyente futuro podría añadir recorte "con buena intención"; NORM-6 y este ADR son la salvaguarda.

## Alternativas Consideradas

| Alternativa | Descripción | Razón de descarte |
|---|---|---|
| Recortar valores a las cotas de sanity | Limitar el TTFB de `9000ms` al máximo de sanity | Destruye la señal de anomalía; contradice `ContratoIngestaRUM.md:30` y el objetivo de investigación. |
| Redondear conteos no enteros | Coaccionar `1.5` → `2` o `1` | Un cambio de magnitud; tergiversa la medición. Se rechaza como `invalid_range`. |
| Sustituir `now()` por timestamps inválidos | Mantener el fallback del worker | Corrompe silenciosamente el análisis temporal; un timestamp reescrito es indistinguible de uno real. |

## Recursos / Compatibilidad

- **Recursos**: sin cómputo adicional; la eliminación del fallback `now()` y de la coerción `float()` en el worker reduce el trabajo.

## Referencias

- `docs/architecture/ContratoIngestaRUM.md:30`
- `openspec/changes/ISS-S3-02/specs/ingest-normalization/spec.md` (NORM-6)
- [ADR 0004](0004-normalize-before-validate.md)
