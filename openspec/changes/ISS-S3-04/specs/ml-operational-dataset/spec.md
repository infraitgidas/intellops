# SPEC — ml-operational-dataset (Nueva) — ISS-S3-04

**Tipo**: Delta spec (capability nueva). **Cambio**: ISS-S3-04 (GitHub #43). **Base**: `proposal.md` (decisión D2 = M4, D4 = (a), ronda de preguntas 2026-10-14), `decisiones-metric-id-y-frontera.md` §6, read path de ISS-S3-01 (`GET /metrics/query`, TQ-1/TQ-2, OAS-14).
**Alcance**: reader HTTP en `src/ml`, mapeo `MetricAggregate` → `MetricBatchInput` sin `metric_id`, configuración, límites de ventana/bucket, alineación de buckets y manejo de errores. Sin entrenamiento ni cableado del reader en el motor (cambio posterior), sin cambios en `src/api` salvo la migración `0004` (ver capability `database`).

## Purpose

Exponer al motor ML el dataset operativo agregado, consumiendo el contrato público del read path sin acoplarse a los internos de la ingesta. La identidad de una observación es la serie/bucket `(application_id, metric_type_id, bucket_start, bucket_seconds)`.

---

## ADDED Requirements

### Requirement: MLD-1 (identidad de serie M4 y contrato de entrada)

`MetricBatchInput` NO DEBE contener `metric_id`. Cada registro DEBE contener `application_id`, `metric_type_id`, `timestamp` (inicio del bucket, UTC), `value`, `session_count` y `bucket_seconds`. La identidad de la serie/bucket DEBE ser la tupla `(application_id, metric_type_id, bucket_start, bucket_seconds)`, donde `bucket_start` es el `timestamp` del bucket. (Traceability: proposal In Scope §1; D2 = M4.)

#### Scenario: MLD-1.1 Registro válido sin metric_id
- GIVEN un diccionario con `application_id`, `metric_type_id`, `timestamp`, `value`, `session_count` y `bucket_seconds`
- WHEN se valida como `MetricBatchInput`
- THEN la validación es exitosa y el modelo no expone el campo `metric_id`

#### Scenario: MLD-1.2 Falta bucket_seconds
- GIVEN un registro sin `bucket_seconds`
- WHEN se valida como `MetricBatchInput`
- THEN la validación falla con error de campo requerido

#### Scenario: MLD-1.3 Mocks alineados
- GIVEN `src/ml/mock_data.json` y la salida de `ml/data/generate_mock_dataset.py`
- WHEN se validan todos sus registros como `MetricBatchInput`
- THEN todos son válidos y ninguno contiene `metric_id`

### Requirement: MLD-2 (mapeo MetricAggregate → MetricBatchInput)

El adaptador DEBE ser una función pura (sin red ni I/O) que transforme cada `MetricAggregate` `(application_id, metric_type_id, timestamp, value, session_count)` en un `MetricBatchInput`, propagando `bucket_seconds` (el valor con el que se pidió la ventana) a cada registro. El adaptador NO DEBE sintetizar identificadores (`uuid`) ni requerir campos ausentes del agregado. (Traceability: proposal Approach "adaptador puro".)

#### Scenario: MLD-2.1 Mapeo con bucket_seconds propagado
- GIVEN una lista de `MetricAggregate` y `bucket_seconds = 60`
- WHEN se aplica el adaptador
- THEN se obtiene una lista de `MetricBatchInput` del mismo largo y orden, cada uno con `bucket_seconds = 60` y los demás campos iguales al agregado

#### Scenario: MLD-2.2 Entrada vacía
- GIVEN una respuesta del read path con lista vacía
- WHEN se aplica el adaptador
- THEN devuelve una lista vacía sin error

### Requirement: MLD-3 (pull HTTP con API key por aplicación)

El reader DEBE obtener los datos exclusivamente mediante `GET /metrics/query` del read path por HTTP (cliente `httpx`), enviando la API key de la aplicación en el header `X-API-Key`. El reader NO DEBE importar código de `src/api` ni acceder a la base de datos. La base URL y la key DEBEN provenir de configuración. (Traceability: proposal In Scope §3; ADR-0003; `containers.md` §5.1.)

#### Scenario: MLD-3.1 Request autenticado
- GIVEN una configuración con base URL y API key de la app A
- WHEN el reader pide una ventana
- THEN envía `GET {base_url}/metrics/query` con header `X-API-Key` igual a la key configurada y los parámetros `start`, `end` y `bucket_seconds`

#### Scenario: MLD-3.2 Sin cross-imports
- GIVEN el código de `src/ml`
- WHEN se analizan sus imports
- THEN ninguno referencia el paquete `src.api`

### Requirement: MLD-4 (alineación de ventana a epoch UTC)

Antes de pedir datos, el reader DEBE alinear `start` y `end` a múltiplos de `bucket_seconds` medidos desde el epoch UTC (`floor` para `start`; `end` alineado al múltiplo igual o inferior más cercano). La alineación DEBE aplicarse aunque difiera del anclaje por defecto del read path (que ancla los buckets al `start` de la ventana). Dos pulls solapados DEBEN producir el mismo `bucket_start` para el mismo instante. (Traceability: proposal Approach "hallazgo"; pregunta 2.)

#### Scenario: MLD-4.1 Start no alineado
- GIVEN `bucket_seconds = 60` y `start = 10:00:37Z`
- WHEN el reader construye el request
- THEN `start = 10:00:00Z` y `end` es múltiplo de 60 s desde epoch

#### Scenario: MLD-4.2 Pulls solapados
- GIVEN dos pulls con ventanas distintas que cubren el mismo instante
- WHEN se comparan los `bucket_start` resultantes
- THEN el bucket del instante común tiene el mismo `bucket_start` en ambos

#### Scenario: MLD-4.3 Bucket de 300 s
- GIVEN `bucket_seconds = 300` y `start = 10:07:12Z`
- WHEN el reader alinea
- THEN `start = 10:05:00Z`

### Requirement: MLD-5 (bucket_seconds configurable, default 60, mínimo 60)

`bucket_seconds` DEBE ser configurable por entorno, con valor por defecto 60 y mínimo 60. Un valor menor a 60 DEBE rechazarse al cargar la configuración (error de configuración explícito) y NO DEBE emitirse ningún request. El valor efectivo DEBE propagarse a cada `MetricBatchInput` (MLD-2) y persistirse en `ANOMALY.bucket_seconds`. (Traceability: TQ-2 bucket mínimo 60 s; proposal In Scope §3, §4.)

#### Scenario: MLD-5.1 Default
- GIVEN una configuración sin `bucket_seconds`
- WHEN se carga
- THEN `bucket_seconds = 60`

#### Scenario: MLD-5.2 Valor inválido
- GIVEN `bucket_seconds = 30`
- WHEN se carga la configuración
- THEN falla con error de configuración y no se realiza ningún request HTTP

### Requirement: MLD-6 (ventana configurable, máximo 7 días)

La ventana (`end - start`) DEBE ser configurable y NO DEBE exceder 7 días (límite del read path, TQ-2). Una ventana mayor DEBE rechazarse del lado del reader antes de pedir. Si el read path responde 422 (p. ej. `invalid_query_range`), el reader DEBE propagar un error tipado que incluya el status y el código, sin reintentar con otros parámetros. (Traceability: TQ-2; proposal In Scope §3.)

#### Scenario: MLD-6.1 Ventana en el límite
- GIVEN una ventana de exactamente 7 días
- WHEN el reader construye el request
- THEN se emite el request sin error

#### Scenario: MLD-6.2 Ventana excedida
- GIVEN una ventana de 7 días y 1 bucket
- WHEN se valida la configuración
- THEN el reader rechaza la ventana sin emitir request

#### Scenario: MLD-6.3 Respuesta 422
- GIVEN un read path que responde 422 `invalid_query_range`
- WHEN el reader procesa la respuesta
- THEN lanza un error tipado con status 422 y el código de error, sin devolver datos parciales

### Requirement: MLD-7 (una aplicación/tenant por ejecución)

Cada ejecución DEBE operar sobre una única aplicación, determinada por la API key presente en la configuración. El reader NO DEBE aceptar un parámetro de aplicación en el request (tenant derivado de la key, OAS-14). Multi-app queda fuera de alcance (N pulls, aditivo post-MVP). (Traceability: pregunta 3; ADR-0003.)

#### Scenario: MLD-7.1 Una key, una app
- GIVEN una configuración con la key de la app A
- WHEN el reader ejecuta
- THEN todos los registros devueltos tienen `application_id` de A

#### Scenario: MLD-7.2 Registro de otra app
- GIVEN una respuesta que contiene un `application_id` distinto al esperado
- WHEN el reader valida
- THEN rechaza el lote completo con error de validación (MLD-8)

### Requirement: MLD-8 (validación de cada MetricAggregate)

El reader DEBE validar CADA `MetricAggregate` recibido contra `MetricBatchInput` (tipos, `value` finito, `session_count >= 0`, `timestamp` con zona UTC). Ante una fila inválida el reader DEBE rechazar el lote completo (fail-fast) y NO DEBE devolver datos parciales: una fila malformada es una violación del contrato del productor, no ruido a tolerar. (Traceability: proposal Scope "reader validado"; design "rechaza el lote entero".)

#### Scenario: MLD-8.1 Fila malformada entre válidas
- GIVEN una respuesta con 3 filas, una con `value = null`
- WHEN el reader valida
- THEN lanza error de validación y no devuelve ningún registro

#### Scenario: MLD-8.2 Todas válidas
- GIVEN una respuesta con filas que cumplen el contrato
- WHEN el reader valida
- THEN devuelve todos los registros como `MetricBatchInput`

### Requirement: MLD-9 (errores y no disponibilidad)

El reader DEBE traducir fallas a errores tipados y NO DEBE devolver datos parciales ni inventados: 401/403 (key inválida), 5xx, timeout/error de conexión y cuerpo no JSON o fuera de contrato. Los timeouts DEBEN ser configurables. El reader NO DEBE caer a `mock_data.json` de forma silenciosa. (Traceability: proposal In Scope §3; riesgo de indisponibilidad.)

#### Scenario: MLD-9.1 Key inválida
- GIVEN un read path que responde 401 `invalid_api_key`
- WHEN el reader procesa la respuesta
- THEN lanza un error de autenticación tipado sin datos

#### Scenario: MLD-9.2 Servicio no disponible
- GIVEN un read path que responde 503 o agota el timeout
- WHEN el reader procesa la falla
- THEN lanza un error de indisponibilidad tipado y no usa el mock

#### Scenario: MLD-9.3 Cuerpo fuera de contrato
- GIVEN una respuesta 200 cuyo cuerpo no es una lista de agregados
- WHEN el reader la procesa
- THEN lanza un error de contrato tipado

### Requirement: MLD-10 (configuración por entorno)

La configuración DEBE leerse de variables de entorno: `INTELLOPS_API_BASE_URL`, API key de la aplicación, `bucket_seconds`, ventana y timeout. Faltar base URL o API key DEBE producir un error de configuración explícito. La API key NO DEBE registrarse en logs. (Traceability: proposal In Scope §4.)

#### Scenario: MLD-10.1 Falta API key
- GIVEN un entorno sin API key
- WHEN se carga la configuración
- THEN falla con error de configuración que nombra la variable faltante

#### Scenario: MLD-10.2 Key fuera de logs
- GIVEN un pull con logging habilitado
- WHEN se inspecciona el log
- THEN el valor de la API key no aparece

---

## Fuera de alcance

- Entrenamiento y cableado del reader en el motor (cambio posterior). El EDA ya está cerrado en #44 (ISS-S3-05).
- User Health Score por sesión.
- Cambios en ingesta o en el read path (`src/api`).
- Scheduler (el pull es bajo demanda) y store de histórico propio.
- Multi-app en una misma ejecución.

## Criterios de aceptación verificables

1. Tests unitarios del adaptador puro (MLD-1, MLD-2, MLD-8).
2. Tests del reader con `httpx.MockTransport` (MLD-3 a MLD-9), incluido solapamiento de ventanas (MLD-4.2).
3. Mocks y generador validan contra `MetricBatchInput` sin `metric_id` (MLD-1.3).
4. Sin imports de `src.api` en `src/ml` (MLD-3.2).
