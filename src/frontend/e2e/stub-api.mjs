#!/usr/bin/env node
/**
 * API stub del smoke E2E (ISS-B-05 D5 / QS-6).
 *
 * Servidor `node:http` sin dependencias en el puerto 8099. Implementa los tres
 * endpoints de lectura con datos deterministas y exige `X-API-Key` como la API
 * real. El error de autenticación usa el envelope de ADR-09 (`{error:{code,
 * message}}`), que es exactamente lo que parsea `src/services/api.ts`.
 *
 * El SPA compilado con `npm run build:e2e` apunta a `http://127.0.0.1:8099`.
 */

import { createServer } from 'node:http';

const PORT = 8099;
/** Key que acepta el stub; cualquier otra devuelve 401. */
const VALID_API_KEY = 'ilp_stub_valida';

const APPLICATION_ID = '11111111-2222-3333-4444-555555555555';
/** Ancla fija para que los buckets sean deterministas entre corridas. */
const ANCHOR_MS = Date.parse('2026-01-01T00:00:00Z');
const DEFAULT_BUCKET_SECONDS = 60;
const BUCKET_COUNT = 3;

const METRIC_TYPES = [
  { metric_type_id: 1, name: 'TTFB', description: 'Time To First Byte' },
  { metric_type_id: 2, name: 'JS_EXCEPTION_RATE', description: 'Tasa de errores no capturados' },
  { metric_type_id: 3, name: 'LCP', description: 'Largest Contentful Paint' },
];

/** Valores deterministas por métrica: dos escalas bien distintas (ms vs fracción). */
const SERIES = {
  1: [210, 240, 260],
  2: [0.01, 0.02, 0.03],
  3: [1800, 1900, 2100],
};

const PROBES = [
  {
    timestamp: '2026-01-01T00:02:00Z',
    target: 'http://127.0.0.1:8000/health',
    http_status: 200,
    outcome: 'ok',
    latency_ms: 42.5,
    available: true,
  },
  {
    timestamp: '2026-01-01T00:01:00Z',
    target: 'http://127.0.0.1:8000/health',
    http_status: 200,
    outcome: 'ok',
    latency_ms: 51.2,
    available: true,
  },
  {
    timestamp: '2026-01-01T00:00:00Z',
    target: 'http://127.0.0.1:8000/health',
    http_status: 503,
    outcome: 'http_error',
    latency_ms: 1500,
    available: false,
  },
];

const AUTH_ERROR_BODY = {
  error: { code: 'invalid_api_key', message: 'invalid or unknown API key' },
};

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'X-API-Key, Content-Type, Accept',
  'Access-Control-Max-Age': '600',
};

function sendJson(response, status, body) {
  const payload = JSON.stringify(body);
  response.writeHead(status, {
    ...CORS_HEADERS,
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(payload),
  });
  response.end(payload);
}

/** Buckets deterministas anclados a `start` (o al ancla fija) y al `bucket_seconds`. */
function buildAggregates(searchParams) {
  const rawStart = searchParams.get('start');
  const parsedStart = rawStart === null ? Number.NaN : Date.parse(rawStart);
  const startMs = Number.isNaN(parsedStart) ? ANCHOR_MS : parsedStart;

  const rawBucket = Number(searchParams.get('bucket_seconds') ?? DEFAULT_BUCKET_SECONDS);
  const bucketSeconds =
    Number.isFinite(rawBucket) && rawBucket >= 60 ? rawBucket : DEFAULT_BUCKET_SECONDS;

  const metricFilter = searchParams.get('metric_type');
  const metricIds =
    metricFilter === null
      ? Object.keys(SERIES).map(Number)
      : [Number(metricFilter)].filter((id) => id in SERIES);

  const rows = [];
  for (const metricTypeId of metricIds) {
    const values = SERIES[metricTypeId];
    for (let index = 0; index < BUCKET_COUNT; index += 1) {
      rows.push({
        application_id: APPLICATION_ID,
        metric_type_id: metricTypeId,
        timestamp: new Date(startMs + index * bucketSeconds * 1000).toISOString(),
        value: values[index],
        session_count: 10 + index,
      });
    }
  }
  return rows;
}

function handle(request, response) {
  if (request.method === 'OPTIONS') {
    response.writeHead(204, CORS_HEADERS);
    response.end();
    return;
  }

  if (request.method !== 'GET') {
    sendJson(response, 405, { error: { code: 'method_not_allowed', message: 'method not allowed' } });
    return;
  }

  if (request.headers['x-api-key'] !== VALID_API_KEY) {
    sendJson(response, 401, AUTH_ERROR_BODY);
    return;
  }

  const url = new URL(request.url ?? '/', `http://127.0.0.1:${PORT}`);
  switch (url.pathname) {
    case '/metrics/list':
      sendJson(response, 200, METRIC_TYPES);
      return;
    case '/metrics/query':
      sendJson(response, 200, buildAggregates(url.searchParams));
      return;
    case '/metrics/probes': {
      const rawLimit = Number(url.searchParams.get('limit') ?? '50');
      const limit = Number.isFinite(rawLimit) ? Math.min(500, Math.max(1, rawLimit)) : 50;
      sendJson(response, 200, PROBES.slice(0, limit));
      return;
    }
    default:
      sendJson(response, 404, { error: { code: 'not_found', message: 'not found' } });
  }
}

const server = createServer(handle);
server.listen(PORT, '127.0.0.1', () => {
  console.log(`stub-api escuchando en http://127.0.0.1:${PORT}`);
});
