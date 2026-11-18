/**
 * Espejo TypeScript del contrato de lectura de métricas (ISS-B-05 D4).
 *
 * Los shapes replican `src/api/presentation/schemas/metrics.py` tal como los
 * expone la API: `MetricAggregateOut`, `MetricTypeInfoOut` y `ProbeRunOut`. No
 * se inventan campos que el contrato no publica (p. ej. `page_url`).
 */

/** Fila agregada de `GET /metrics/query`: `value` es el AVG del bucket. */
export interface MetricAggregate {
  application_id: string;
  metric_type_id: number;
  /** Inicio del bucket, ISO 8601 UTC. */
  timestamp: string;
  /** AVG(value) del bucket. */
  value: number;
  /** COUNT(DISTINCT session_id) del bucket. */
  session_count: number;
}

/** Entrada del catálogo `GET /metrics/list` (OAS-13). */
export interface MetricTypeInfo {
  metric_type_id: number;
  name: string;
  /** El contrato lo declara nullable aunque el OAS diga `string`. */
  description?: string | null;
}

/** Corrida de la sonda HTTP de `GET /metrics/probes` (B.13/T6). */
export interface ProbeRun {
  timestamp: string;
  target: string | null;
  http_status: number | null;
  outcome: string | null;
  latency_ms: number | null;
  available: boolean;
}
