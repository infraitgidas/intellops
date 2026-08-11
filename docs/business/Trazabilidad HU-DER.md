# Trazabilidad Historias de Usuario ↔ Modelo de Datos (DER v1.2)

**Fecha:** 9 de agosto de 2026
**Fuentes:**
- HUs: `docs/business/Especificación de Historias de Usuario v1.2.md`
- DER: `docs/der/DER intellops v1.2.pdf` + `docs/der/Explicacion DER v1.2.pdf`

## Mapeo por Historia de Usuario

| HU | Descripción | Entidad(es) | Campos |
|----|-------------|-------------|--------|
| HU-001 | Inicio de sesión institucional | `LAB_USER` | email, contraseña (sesión JWT no modelada) |
| HU-002 | Cierre de sesión | `LAB_USER` | sesión activa |
| HU-03 | Gestión de perfil simplificado | `LAB_USER` | name, email, role |
| HU-04 | Consultar aplicaciones | `APPLICATION` | app_id, name, description |
| HU-05 | Validar instrumentación | `RUM_METRIC` | existencia de metric_id recientes por app |
| HU-06 | Recepción de métricas | `RUM_METRIC` | value, unit, timestamp |
| HU-07 | Recepción e ingesta de logs | Backend Loki (fuera del DER) | — |
| HU-08 | Recepción de trazas | Backend OTel (fuera del DER) | — |
| HU-09 | Dashboard de métricas (5 métricas) | `RUM_METRIC`, `JS_EXCEPTION` | ver mapeo de métricas abajo |
| HU-10 | Visualizar métricas de rendimiento | `RUM_METRIC` | value, unit, page_url, timestamp |
| HU-11 | Consultar detalle de una métrica | `RUM_METRIC` | value, unit, metadata, timestamp |
| HU-12 | Consultar logs | Backend Loki (fuera del DER) | — |
| HU-13 | Filtrar logs | Backend Loki (fuera del DER) | — |
| HU-14 | Consultar trazas | Backend OTel (fuera del DER) | — |
| HU-15 | Consultar detalle de una traza | Backend OTel (fuera del DER) | — |
| HU-16 | Obtener predicciones | `ANOMALY`, `ML_MODEL`, `RUM_METRIC` | severity_score, confidence_score, target_metric, value |
| HU-17 | Consultar explicación de la IA | `ANOMALY`, `ML_MODEL` | confidence_score, expected_value, actual_value, hyperparameters |
| HU-18 | Visualizar recomendaciones | Derivado de `ANOMALY` / `ML_MODEL` | severity_score, target_metric |
| HU-19 | Consultar prioridad de una recomendación | Derivado de `ANOMALY` | severity_score |
| HU-20 | Configurar canales y sensibilidad de alertas | `ALERT`, `ANOMALY` | recipient, channel; severity_score (sensibilidad) |
| HU-21 | Visualizar alertas | `ALERT` → `ANOMALY` → `RUM_METRIC` | message, sent_at, channel, severity_score, metric_type |
| HU-22 | Historial de alertas | `ALERT` | status, sent_at, message |

## Mapeo de las 5 métricas deterministas (HU-09)

| Métrica | Entidad | metric_type | Campo | Unidad |
|---------|---------|-------------|-------|--------|
| TTFB | `RUM_METRIC` | `TTFB` | value | ms |
| FCP | `RUM_METRIC` | `FCP` | value | ms |
| XHR Latency | `RUM_METRIC` | `XHR_Latency` | value | ms |
| Tasa de Excepciones JS | `JS_EXCEPTION` | — (derivada) | COUNT(error_id) por ventana/sesión | count |
| Rage Clicks | `RUM_METRIC` | `Rage_Click` | value | count |

> Nota: en el DER v1.2, el enum `Rage_Click` figura en `USER_FAVORITE_METRIC.metric_type`.

## Referencias cruzadas

- `USER_SESSION` relaciona `APPLICATION` y `LAB_USER` con `RUM_METRIC` (session_id).
- `JS_EXCEPTION.metric_id` (opcional) asocia errores a la métrica que los originó.
- `ANOMALY` relaciona `RUM_METRIC` (metric_id) con `ML_MODEL` (model_id).
- `ALERT.anomaly_id` asocia cada alerta a la anomalía que la disparó.
