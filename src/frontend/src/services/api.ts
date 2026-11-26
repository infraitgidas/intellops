/**
 * Cliente HTTP único del panel (ISS-B-05 D4).
 *
 * Las tres llamadas del contrato de lectura (`/metrics/query`, `/metrics/list`,
 * `/metrics/probes`) exigen `X-API-Key`: el tenant sale de la key, nunca de un
 * parámetro. Cualquier fallo se normaliza a `ApiError` para que las vistas no
 * hagan `try/catch` sueltos ni dependan del shape crudo de FastAPI.
 */

import type { MetricAggregate, MetricTypeInfo, ProbeRun } from './types';

/** Base de la API; se puede sobreescribir en build con `VITE_API_BASE_URL`. */
export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
).replace(/\/+$/, '');

export interface ApiErrorInit {
  /** Código HTTP; 0 cuando la request no llegó a la API (red). */
  status: number;
  /** Código del contrato (`invalid_api_key`) o `http_<status>`/`network_error`. */
  code: string;
  /** Mensaje legible, sin la key. */
  message: string;
}

/** Error normalizado de la API: status HTTP + código del contrato + mensaje. */
export class ApiError extends Error {
  readonly status: number;

  readonly code: string;

  constructor(init: ApiErrorInit) {
    super(init.message);
    this.name = 'ApiError';
    this.status = init.status;
    this.code = init.code;
  }
}

export function isApiError(value: unknown): value is ApiError {
  return value instanceof ApiError;
}

/** 401/403 obligan a descartar la key y volver al gate (QS-1). */
export function isAuthError(error: ApiError): boolean {
  return error.status === 401 || error.status === 403;
}

/** Cualquier `throw` desconocido se convierte en `ApiError` (sin `any`). */
export function toApiError(error: unknown): ApiError {
  if (isApiError(error)) {
    return error;
  }
  if (error instanceof Error) {
    return new ApiError({ status: 0, code: 'network_error', message: error.message });
  }
  return new ApiError({
    status: 0,
    code: 'unknown_error',
    message: 'Error inesperado al consultar la API.',
  });
}

export interface MetricsQueryParams {
  /** Inicio de la ventana (ISO 8601 UTC). */
  start: string;
  /** Fin de la ventana (ISO 8601 UTC). */
  end: string;
  /** Tamaño del bucket en segundos (el contrato exige ≥ 60). */
  bucketSeconds: number;
  /** Filtro opcional por `metric_type_id`; el heatmap no lo envía. */
  metricTypeId?: number;
}

/** `GET /metrics/query` — AVG por bucket, orden bucket ascendente. */
export function getMetrics(
  params: MetricsQueryParams,
  apiKey: string,
): Promise<MetricAggregate[]> {
  const query = new URLSearchParams({
    start: params.start,
    end: params.end,
    bucket_seconds: String(params.bucketSeconds),
  });
  if (params.metricTypeId !== undefined) {
    query.set('metric_type', String(params.metricTypeId));
  }
  return request<MetricAggregate[]>(`/metrics/query?${query.toString()}`, apiKey);
}

/** `GET /metrics/list` — catálogo de `metric_type` de la plataforma. */
export function getMetricTypes(apiKey: string): Promise<MetricTypeInfo[]> {
  return request<MetricTypeInfo[]>('/metrics/list', apiKey);
}

/** `GET /metrics/probes?limit=1..500` — corridas de la sonda, más nueva primero. */
export function getProbes(limit: number, apiKey: string): Promise<ProbeRun[]> {
  const query = new URLSearchParams({ limit: String(limit) });
  return request<ProbeRun[]>(`/metrics/probes?${query.toString()}`, apiKey);
}

async function request<T>(path: string, apiKey: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { Accept: 'application/json', 'X-API-Key': apiKey },
    });
  } catch {
    throw new ApiError({
      status: 0,
      code: 'network_error',
      message: 'No se pudo conectar con la API.',
    });
  }

  if (!response.ok) {
    throw buildApiError(response.status, await readBody(response));
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError({
      status: response.status,
      code: 'invalid_response',
      message: 'La API devolvió una respuesta ilegible.',
    });
  }
}

async function readBody(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

/** Traduce el body de error: `{error:{code,message}}` (ADR-09) o `{detail}`. */
function buildApiError(status: number, body: unknown): ApiError {
  const fallbackCode = `http_${status}`;
  const fallbackMessage = defaultMessageFor(status);

  if (!isRecord(body)) {
    return new ApiError({ status, code: fallbackCode, message: fallbackMessage });
  }

  const code = readString(body['error'], 'code');
  const message = readString(body['error'], 'message');
  if (code !== null || message !== null) {
    return new ApiError({
      status,
      code: code ?? fallbackCode,
      message: message ?? fallbackMessage,
    });
  }

  const detail = body['detail'];
  if (typeof detail === 'string' && detail.length > 0) {
    return new ApiError({ status, code: fallbackCode, message: detail });
  }
  if (Array.isArray(detail)) {
    const details: unknown[] = detail;
    const messages = details
      .map((entry) => readString(entry, 'msg'))
      .filter((entry): entry is string => entry !== null);
    if (messages.length > 0) {
      return new ApiError({ status, code: fallbackCode, message: messages.join('; ') });
    }
  }

  return new ApiError({ status, code: fallbackCode, message: fallbackMessage });
}

function defaultMessageFor(status: number): string {
  switch (status) {
    case 401:
      return 'La API rechazó la API key (401).';
    case 403:
      return 'La aplicación de la API key está inactiva (403).';
    case 404:
      return 'El endpoint consultado no existe (404).';
    case 422:
      return 'La consulta no cumple el contrato (422).';
    default:
      return status >= 500
        ? `La API falló con status ${status}.`
        : `La API respondió con status ${status}.`;
  }
}

function readString(value: unknown, key: string): string | null {
  if (!isRecord(value)) {
    return null;
  }
  const field = value[key];
  return typeof field === 'string' && field.length > 0 ? field : null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}
