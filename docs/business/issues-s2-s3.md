# Issues publicadas en GitHub — IntellOps (Sprints 2 y 3)

Registro de las issues publicadas en GitHub el **07/09/2026** en el repositorio `infraitgidas/intellops`, según la replanificación de 8 sprints ([IntellOps_Replanificacion_Issues_Sprints.md](../../IntellOps_Replanificacion_Issues_Sprints.md), v1.0, 06/09/2026).

Este archivo reemplaza el catálogo `issues-sprints-2-8.md` para los sprints 2 y 3, que ya fueron publicados.

## Estado de publicación

- **Total publicadas**: 11 (S2: 5, S3: 6)
- **Rango de issues en GitHub**: #35 – #45
- **Estado**: todas `OPEN`
- **Etiquetas**: no aplicadas (las etiquetas del plan `sprint-<n>`, `owner:<nombre>` y de área no existen en el repositorio; se publicaron sin etiquetas)
- **Prioridad**: Alta para todas

## Estructura canónica

Todas las issues siguen la estructura de la issue abierta ISS-S1-04 (#20):

```text
- **Sprint**: SX
- **Owner**: Nombre
- **Etiquetas**: `...` (sugeridas, no aplicadas)
- **Dependencias**: ...
- **Prioridad**: Alta

**Descripción**: ...

**Criterios de aceptación**:
- [ ] ...
```

Los campos `Alineación` y `Libertad` del plan no se incluyen en GitHub; quedan documentados en el plan original.

---

## SPRINT 2 — Foundations e ingesta

### ISS-S2-01 — Backend Core funcional

- **GitHub**: [#35](https://github.com/infraitgidas/intellops/issues/35)
- **Sprint**: S2
- **Owner**: Federico
- **Etiquetas** (sugeridas): `sprint-2`, `owner:federico`, `backend`
- **Dependencias**: S1 (absorbido: arquitectura y contratos)
- **Prioridad**: Alta

**Descripción**: Implementar las capacidades backend necesarias para aplicaciones, usuarios, autenticación y autorización.

**Criterios de aceptación**:
- [ ] Los recursos son accesibles mediante API.
- [ ] Se persisten correctamente.
- [ ] Se respeta aislamiento/autorización entre aplicaciones.

---

### ISS-S2-02 — Aplicaciones y credenciales de ingesta

- **GitHub**: [#36](https://github.com/infraitgidas/intellops/issues/36)
- **Sprint**: S2
- **Owner**: Federico
- **Etiquetas** (sugeridas): `sprint-2`, `owner:federico`, `backend`, `seguridad`
- **Dependencias**: ISS-S2-01
- **Prioridad**: Alta

**Descripción**: Permitir gestionar aplicaciones y las credenciales necesarias para enviar telemetría.

**Criterios de aceptación**:
- [ ] Creación de aplicaciones.
- [ ] Activación/inactivación.
- [ ] Validación de credenciales.
- [ ] Autorización de ingesta.
- [ ] Aislamiento entre aplicaciones.

---

### ISS-S2-03 — Ingesta RUM asíncrona

- **GitHub**: [#37](https://github.com/infraitgidas/intellops/issues/37)
- **Sprint**: S2
- **Owner**: Federico
- **Etiquetas** (sugeridas): `sprint-2`, `owner:federico`, `telemetria`, `backend`, `contrato`
- **Dependencias**: ISS-S2-02
- **Prioridad**: Alta

**Descripción**: Implementar los endpoints de ingesta RUM asíncrona:

```http
POST /telemetry/metrics
POST /telemetry/exceptions
```

Debe soportar procesamiento asíncrono y modular sin broker externo.

**Criterios de aceptación**:
- [ ] Batches aceptados.
- [ ] Validación de batches y de eventos individuales según la política por evento.
- [ ] Respuesta adecuada que informa el resultado del batch de forma consistente.
- [ ] Procesamiento desacoplado del request.
- [ ] Backpressure.
- [ ] Errores controlados.
- [ ] Observabilidad mínima.

**Nomenclatura definitiva (absorbida de ISS-S1-02)**:
- [ ] OpenAPI actualizado a `POST /telemetry/metrics` y `POST /telemetry/exceptions`.
- [ ] Implementación alineada con esos endpoints.
- [ ] Tests alineados.
- [ ] Schemathesis alineado.
- [ ] No quedan referencias funcionales a las rutas anteriores (`/metrics/ingest`, `/logs/ingest`) en OpenAPI, implementación, tests, Schemathesis, documentación, ejemplos ni frontend.

**Nota**: No se prescribe `asyncio.Queue`, `BackgroundTasks`, workers específicos ni otra estructura interna.

---

### ISS-S2-04 — Pipeline CI/CD inicial

- **GitHub**: [#38](https://github.com/infraitgidas/intellops/issues/38)
- **Sprint**: S2
- **Owner**: Santiago
- **Etiquetas** (sugeridas): `sprint-2`, `owner:santiago`, `qa`, `ci-cd`
- **Dependencias**: S1 (absorbido: baseline de calidad)
- **Prioridad**: Alta

**Descripción**: Incorporar progresivamente la pipeline de QA.

**Criterios de aceptación**:
- [ ] Lint.
- [ ] Unit tests.
- [ ] Reporte de cobertura.

**Nota**: La evolución posterior podrá incorporar integration-test, build, staging y E2E.

---

### ISS-S2-05 — Entorno reproducible de testing

- **GitHub**: [#39](https://github.com/infraitgidas/intellops/issues/39)
- **Sprint**: S2
- **Owner**: Santiago
- **Etiquetas** (sugeridas): `sprint-2`, `owner:santiago`, `qa`, `infra`
- **Dependencias**: ISS-S2-04
- **Prioridad**: Alta

**Descripción**: Disponer de un entorno reproducible para ejecutar las pruebas automáticamente.

**Criterios de aceptación**:
- [ ] La suite se ejecuta sin depender de la máquina del desarrollador.

---

## SPRINT 3 — Datos y procesamiento

### ISS-S3-01 — Persistencia de telemetría

- **GitHub**: [#40](https://github.com/infraitgidas/intellops/issues/40)
- **Sprint**: S3
- **Owner**: Federico
- **Etiquetas** (sugeridas): `sprint-3`, `owner:federico`, `telemetria`, `base-de-datos`
- **Dependencias**: ISS-S2-03
- **Prioridad**: Alta

**Descripción**: Persistir métricas y excepciones manteniendo relaciones con aplicación, sesión, timestamp y tipo de evento.

**Criterios de aceptación**:
- [ ] Aplicación.
- [ ] Sesión.
- [ ] Timestamp.
- [ ] Tipo de evento.

---

### ISS-S3-02 — Normalización y calidad de datos

- **GitHub**: [#41](https://github.com/infraitgidas/intellops/issues/41)
- **Sprint**: S3
- **Owner**: Federico
- **Etiquetas** (sugeridas): `sprint-3`, `owner:federico`, `telemetria`, `datos`
- **Dependencias**: ISS-S2-03
- **Prioridad**: Alta

**Descripción**: Implementar el flujo de normalización:

```text
Raw → Validation → Normalization → Storage
```

**Criterios de aceptación**:
- [ ] Resuelve inconsistencias de timestamps.
- [ ] Resuelve inconsistencias de unidades.
- [ ] Resuelve inconsistencias de nombres.
- [ ] Maneja valores faltantes.
- [ ] Maneja valores inválidos.

---

### ISS-S3-03 — Gestión de sesiones

- **GitHub**: [#42](https://github.com/infraitgidas/intellops/issues/42)
- **Sprint**: S3
- **Owner**: Santiago
- **Etiquetas** (sugeridas): `sprint-3`, `owner:santiago`, `backend`, `telemetria`
- **Dependencias**: ISS-S2-01
- **Prioridad**: Alta

**Descripción**: Implementar la gestión de sesiones necesaria para relacionar actividad RUM con aplicaciones y usuarios cuando corresponda.

---

### ISS-S3-04 — Dataset operativo para ML

- **GitHub**: [#43](https://github.com/infraitgidas/intellops/issues/43)
- **Sprint**: S3
- **Owner**: Federico + Romeo
- **Etiquetas** (sugeridas): `sprint-3`, `owner:federico`, `owner:romeo`, `ml`, `datos`
- **Dependencias**: ISS-S3-01
- **Prioridad**: Alta

**Descripción**: Exponer los datos necesarios para el motor ML sin acoplarlo a la implementación interna de la ingesta.

---

### ISS-S3-05 — EDA del dataset inicial

- **GitHub**: [#44](https://github.com/infraitgidas/intellops/issues/44)
- **Sprint**: S3
- **Owner**: Romeo
- **Etiquetas** (sugeridas): `sprint-3`, `owner:romeo`, `ml`, `datos`
- **Dependencias**: S1 (absorbido: `src/ml` y contratos) · **Precondición:** merge de `feat/ISS-S1-07` (contiene `mock_reader.py` y dataset/mock)
- **Prioridad**: Alta

**Descripción**: Partir de los datos/reader existentes y producir un notebook de exploración estadística.

**Criterios de aceptación**:
- [ ] Análisis de distribuciones.
- [ ] Análisis de valores atípicos.
- [ ] Análisis de comportamiento temporal.
- [ ] Análisis de correlaciones.
- [ ] Evaluación de la calidad del dataset.
- [ ] Hipótesis para detección de anomalías.

---

### ISS-S3-06 — Pruebas unitarias de módulos críticos

- **GitHub**: [#45](https://github.com/infraitgidas/intellops/issues/45)
- **Sprint**: S3
- **Owner**: Santiago
- **Etiquetas** (sugeridas): `sprint-3`, `owner:santiago`, `qa`
- **Dependencias**: ISS-S2-04
- **Prioridad**: Alta

**Descripción**: Aumentar cobertura sobre los módulos de mayor riesgo.

**Criterios de aceptación**:
- [ ] Cobertura sobre normalización.
- [ ] Cobertura sobre lógica de negocio.
- [ ] Cobertura sobre transformaciones.
- [ ] Cobertura sobre validaciones.

---

## Resumen

| Issue | Título | GitHub | Owner |
|---|---|---|---|
| ISS-S2-01 | Backend Core funcional | [#35](https://github.com/infraitgidas/intellops/issues/35) | Federico |
| ISS-S2-02 | Aplicaciones y credenciales de ingesta | [#36](https://github.com/infraitgidas/intellops/issues/36) | Federico |
| ISS-S2-03 | Ingesta RUM asíncrona | [#37](https://github.com/infraitgidas/intellops/issues/37) | Federico |
| ISS-S2-04 | Pipeline CI/CD inicial | [#38](https://github.com/infraitgidas/intellops/issues/38) | Santiago |
| ISS-S2-05 | Entorno reproducible de testing | [#39](https://github.com/infraitgidas/intellops/issues/39) | Santiago |
| ISS-S3-01 | Persistencia de telemetría | [#40](https://github.com/infraitgidas/intellops/issues/40) | Federico |
| ISS-S3-02 | Normalización y calidad de datos | [#41](https://github.com/infraitgidas/intellops/issues/41) | Federico |
| ISS-S3-03 | Gestión de sesiones | [#42](https://github.com/infraitgidas/intellops/issues/42) | Santiago |
| ISS-S3-04 | Dataset operativo para ML | [#43](https://github.com/infraitgidas/intellops/issues/43) | Federico + Romeo |
| ISS-S3-05 | EDA del dataset inicial | [#44](https://github.com/infraitgidas/intellops/issues/44) | Romeo |
| ISS-S3-06 | Pruebas unitarias de módulos críticos | [#45](https://github.com/infraitgidas/intellops/issues/45) | Santiago |
