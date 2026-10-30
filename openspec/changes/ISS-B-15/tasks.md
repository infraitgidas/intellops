# Tasks: ISS-B-15 — Alineación del contrato RUM v0.1 con la implementación

## Review Workload Forecast

Estimated changed lines: ~450 (contrato ~60, ingest/persistencia ~120, tests ~220, docs ~50). Delivery strategy: seis work-units en `feat/ISS-B-15`, un PR a develop.

## Fase 1 — Documentación del cambio

- [x] 1.1 `openspec/changes/ISS-B-15/proposal.md` y `tasks.md` con alcance y decisiones D1–D4.

## Fase 2 — Correcciones de contrato

- [x] 2.1 D-04: quitar `429` de `/telemetry/metrics` y `/telemetry/exceptions` en OpenAPI, `interfaces.md` y docs de ingesta; conservar el de `/assistant/query`.
- [x] 2.2 D-04: ajustar tests de contrato y la corrida scoped de schemathesis.
- [x] 2.3 D-03: quitar `viewport` y `connection` de `RumEvent.metadata.properties`; test de ausencia.
- [x] 2.4 D-03: verificar que `page_url` y `user_agent` se mantienen.

## Fase 3 — Ingesta

- [x] 3.1 OD-04/D-02: agregar `invalid_schema_version` y validar `schema_version` por evento en `validate_rum_event` y `validate_js_exception`.
- [x] 3.2 OD-04/D-02: incluir `schema_version` en `_REQUIRED_JS_FIELDS` y actualizar docstring/orden de validación.
- [x] 3.3 OD-04/D-02: documentar el nuevo código en OpenAPI y `PipelineIngestaRUM.md`.
- [x] 3.4 OD-03: `sample_rate` optional en OpenAPI y `JsExceptionEvent`; el agente lo envía en excepciones.
- [x] 3.5 OD-03: persistir `sample_rate` en `ExceptionRow`, entidad, repositorio y `_build_rows`.
- [x] 3.6 OD-03: migración `0005` y espejo en `ddl_v1.0.sql`.

## Fase 4 — Tests y verificación

- [x] 4.1 Tests de política: `schema_version` inválido en ambos eventos, ausente en excepción, `sample_rate` presente y ausente.
- [x] 4.2 Test HTTP de 202 parcial con un evento de `schema_version` inválido y el resto aceptado.
- [x] 4.3 Tests de contrato: telemetría sin `429`, `/assistant/query` con `429`, metadata sin `viewport`/`connection`, `sample_rate` 0..1 opcional.
- [x] 4.4 Tests del agente: `sample_rate` en el payload de excepciones y en métricas.
- [x] 4.5 Actualizar §13/§14 del contrato y `CHANGELOG.md`.
- [x] 4.6 `pytest tests/test_contract.py`, `pytest -m unit` y `npm test` en verde (salvo la falla ambiental de `numpy`).
