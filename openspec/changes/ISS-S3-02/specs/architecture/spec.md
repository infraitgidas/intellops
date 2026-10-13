# Delta para architecture

**Cambio**: ISS-S3-02 (#41). **Tipo**: Delta (capability modificada). **Store**: openspec.
**Base**: proposal (Capabilities: `architecture` modificada), exploration §"Tensión de orden", research X6/D2/D4, `docs/architecture/PipelineIngestaRUM.md`, ADR-0002.

## Purpose

Registrar el orden del pipeline de ingesta introducido por la capability `ingest-normalization` y la flexibilidad de contrato documentada que requiere.

## ADDED Requirements

### Requirement: ARCH-5 (orden del pipeline de ingesta)

El pipeline de ingesta DEBE documentarse e implementarse como `Raw → Normalize → Validate → Enqueue → Store`: una etapa de normalización en el dominio DEBE correr antes de la validación por evento, y la validación DEBE seguir siendo la autoridad única de rechazo. La normalización DEBE resolver representaciones (timestamp, unidad, nombre) que de otro modo la validación rechazaría.
(Previamente: sin etapa de normalización con nombre; la única coerción era implícita en el worker de infraestructura, post-`202`.)

#### Scenario: Orden observable

- GIVEN el flujo de ingesta
- WHEN se envía un evento que lleva un alias de unidad
- THEN la normalización corre primero y la validación ve el evento canónico

#### Scenario: Autoridad de rechazo sin cambios

- GIVEN un evento canónico que viola una cota de sanity
- WHEN corre la validación
- THEN la validación (no la normalización) devuelve la razón de rechazo

### Requirement: ARCH-6 (flexibilidad de contrato documentada)

La declaración `RumMetric.unit` de OpenAPI DEBE ampliarse para aceptar la familia de alias (`s`, `sec`, `secs`, `msec`, `millis`, `counts`) junto con `ms`/`count`, para que el contrato documentado coincida con la flexibilidad en runtime. La ampliación DEBE ser retrocompatible; las unidades y nombres de métrica desconocidos DEBEN seguir rechazándose.

#### Scenario: El contrato refleja los alias

- GIVEN el `openspec/specs/openapi.yaml` actualizado
- WHEN se inspecciona `RumMetric.unit`
- THEN la familia de alias se acepta y la semántica de envelope / `schema_version` no cambia

## Next recommended

**design** — definir la secuencia de normalizar-antes-de-validar y el ADR que registra la decisión de orden.
