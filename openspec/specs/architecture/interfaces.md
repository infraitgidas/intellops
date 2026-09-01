# Interfaces Specification — IntellOps

- **Versión**: 1.0
- **Fecha**: 2026-05-27
- **Autores**: Emanuel Rodriguez, Equipo InfraIT GIDAS

## 1. Contratos de API

### 1.1. OpenAPI 3.1 — REST API

**Arquitectura de nomenclatura unificada (ISS-S1-02):**
Se decidió usar `/metrics/ingest` como endpoint canonical por sobre `/telemetry/metrics`,
basado en la adopción existente en la especificación actual y para mantener compatibilidad
con la convención de ingesta OTel del agente RUM. Todos los endpoints relacionados con
métricas deben usar el prefijo `/metrics/`.

**Archivo**: `openspec/specs/openapi.yaml` (por crear en primer cambio)

| Método | Path | Propósito | Status |
|--------|------|-----------|--------|
| GET | `/health` | Health check del sistema | ✅ Planificado |
| GET | `/ready` | Readiness check (dependencias listas) | ✅ Planificado |
| POST | `/metrics/ingest` | Ingesta de métricas OTel | ✅ Planificado |
| GET | `/metrics/query` | Consulta de métricas históricas | ✅ Planificado |
| GET | `/metrics/list` | Listado de métricas disponibles | ✅ Planificado |
| GET | `/anomalies` | Listado de anomalías detectadas | ✅ Planificado |
| GET | `/anomalies/{id}` | Detalle de una anomalía específica | ✅ Planificado |
| GET | `/predictions` | Predicciones actuales | ✅ Planificado |
| GET | `/predictions/forecast` | Forecasting conversacional | ✅ Planificado |
| GET | `/alerts` | Listado de alertas | ✅ Planificado |
| POST | `/alerts/config` | Configurar regla de alerta | ✅ Planificado |
| PUT | `/alerts/{id}/ack` | Acknowledge de alerta | ✅ Planificado |
| GET | `/dashboard/summary` | Resumen para dashboard principal | ✅ Planificado |
| GET | `/dashboard/heatmap` | Datos para mapa de calor | ✅ Planificado |
| POST | `/assistant/query` | Consulta al asistente GenIA | ✅ Planificado |
| GET | `/admin/config` | Configuración del sistema | 🔒 Autenticado |
| PUT | `/admin/config` | Actualizar configuración | 🔒 Autenticado |
| GET | `/admin/status` | Estado del sistema | 🔒 Autenticado |

#### Endpoints Críticos

##### POST /metrics/ingest

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          source:
            type: string
            description: "Identificador del agente/servicio"
          metrics:
            type: array
            items:
              $ref: '#/components/schemas/Metric'
          timestamp:
            type: string
            format: date-time
responses:
  '202':
    description: "Métricas aceptadas para procesamiento"
  '400':
    description: "Payload inválido (schema validation error)"
  '429':
    description: "Rate limit excedido"
```

##### POST /assistant/query

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          query:
            type: string
            description: "Consulta en lenguaje natural"
          context:
            type: object
            properties:
              timeRange:
                type: string
                description: "Rango temporal (ej: 'last 30m')"
              metricFilter:
                type: array
                items:
                  type: string
responses:
  '200':
    description: "Respuesta del asistente"
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/AssistantResponse'
  '429':
    description: "LLM ocupado, reintentar"
```

### 1.2. AsyncAPI 3.0 — Eventos

**Archivo**: `openspec/specs/asyncapi.yaml` (por crear)

| Canal | Evento | Propósito | Status |
|-------|--------|-----------|--------|
| `anomaly/detected` | AnomalyEvent | Nueva anomalía detectada | ✅ Planificado |
| `alert/triggered` | AlertEvent | Alerta disparada | ✅ Planificado |
| `metrics/batch` | MetricBatchEvent | Lote de métricas procesado | 📝 Extensión futura |
| `system/health` | HealthEvent | Cambio de estado de salud | 📝 Extensión futura |

## 2. APIs Internas

### 2.1. ML Engine API (gRPC/HTTP interna)

| Método | Path | Propósito |
|--------|------|-----------|
| POST | `/ml/detect` | Detectar anomalías en feature vector |
| POST | `/ml/predict` | Generar predicción/forecast |
| GET | `/ml/status` | Estado del modelo (último entrenamiento, métricas) |
| POST | `/ml/train` | Iniciar entrenamiento batch |

### 2.2. LLM Server API (formato compatible OpenAI)

| Método | Path | Propósito |
|--------|------|-----------|
| POST | `/v1/chat/completions` | Chat completion con RAG |
| GET | `/v1/models` | Listar modelos disponibles |

## 3. Interfaces de Infraestructura

### 3.1. Puertos Expuestos

| Puerto | Servicio | Protocolo | Acceso |
|--------|----------|-----------|--------|
| 8000 | FastAPI (API pública) | HTTP | Público (con auth) |
| 8001 | FastAPI (health/metrics) | HTTP | Interno (docker network) |
| 8080 | LLM Server | HTTP | Interno |
| 9090 | Prometheus | HTTP | Interno (Grafana) |
| 3100 | Loki | HTTP | Interno (Grafana) |
| 3000 | Grafana | HTTP | Público (con auth) |
| 80 | Nginx (Dashboard) | HTTP | Público |
| 19999 | Netdata | HTTP | Interno |

### 3.2. Endpoints de Métricas (Prometheus)

| Endpoint | Formato | Propósito |
|----------|---------|-----------|
| `GET /metrics` | OpenMetrics | Métricas del backend FastAPI |
| `GET /metrics` | OpenMetrics | Métricas de Node Exporter |
| `GET /api/v1/targets` | JSON | Targets de Prometheus |

## 4. Interfaces de Notificación (Webhooks)

| Plataforma | Formato | Uso |
|------------|---------|-----|
| Discord | Webhook JSON | Alertas de seguridad y sistema |
| Slack | Webhook JSON | Alertas de seguridad y sistema |
| Email (SMTP) | SMTP | Alertas críticas (diario/resumen) |

## 5. Contratos de Datos

### 5.1. Formatos de Métricas

```yaml
Metric:
  type: object
  properties:
    name:
      type: string
      description: "Nombre de la métrica (ej: cpu.usage.user)"
    value:
      type: number
      description: "Valor numérico"
    timestamp:
      type: integer
      description: "Unix timestamp en segundos"
    tags:
      type: object
      additionalProperties:
        type: string
      description: "Etiquetas contextuales (host, service, region)"
    unit:
      type: string
      description: "Unidad de medida (percent, ms, count, bytes)"
```

### 5.2. Esquema de Anomalías

```yaml
Anomaly:
  type: object
  properties:
    id:
      type: string
      format: uuid
    metric_name:
      type: string
    detected_at:
      type: string
      format: date-time
    score:
      type: number
      description: "Puntaje de anomalía (0-1), > 0.8 es anómalo"
    severity:
      type: string
      enum: [low, medium, high, critical]
    detector:
      type: string
      enum: [isolation_forest, zscore, seasonal, ensemble]
    description:
      type: string
      description: "Descripción legible de la anomalía"
    metrics_snapshot:
      type: object
      description: "Métrica y ventana temporal del contexto"
```

### 5.3. Formato de Logs (Loki)

```yaml
LogEntry:
  type: object
  properties:
    timestamp:
      type: string
      format: date-time
    message:
      type: string
    level:
      type: string
      enum: [debug, info, warn, error, fatal]
    service:
      type: string
    host:
      type: string
    labels:
      type: object
      additionalProperties:
        type: string
```

## 6. Versionado de APIs

| Estrategia | Detalle |
|------------|---------|
| **Formato** | Versionado semántico en header (`Accept-Version: 1.0`) y URL (`/v1/metrics`) |
| **Breaking changes** | Nueva versión mayor, versión anterior deprecada con 3 meses de solapamiento |
| **Documentación** | Cada versión tiene su spec OpenAPI en `openspec/specs/openapi-v{MAJOR}.yaml` |
| **Compatibilidad** | Backward compatibility validada por contract tests en CI |
