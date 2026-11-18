// Escenario de carga de la ingesta de IntellOps (ISS-C-03, LT-2..LT-4).
//
// Mide la latencia de `POST /telemetry/metrics` sobre la stack real del compose
// con una carga estándar y corta: 10 VUs durante 1 min, un lote de 10 eventos
// por iteración y `sleep(1)` entre iteraciones (≈100 eventos/s). El umbral de la
// v1 es p95 ≤ 500 ms con menos del 1 % de requests fallidos y el 100 % de los
// checks en verde (LT-3). k6 sale ≠ 0 si un umbral no se cumple.
//
// `setup()` provisiona solo lo que la ingesta necesita: login del Admin del
// seed → aplicación de carga `k6-load-<timestamp>` → API key. No hay
// credenciales previas ni datos que preparar a mano (LT-2, escenario "sin
// credenciales previas").
//
// `teardown()` NO borra la aplicación (D4): `DELETE /applications/{id}` responde
// 409 cuando la app ya tiene sesiones (FK RESTRICT), así que la limpieza real es
// `docker compose down -v` o SQL. Ver docs/operations/load-test.md §6.
//
// Variables de entorno (todas opcionales, D3):
//
//   BASE_URL        http://intellops-core:8000   base de la API (DNS del compose)
//   ADMIN_EMAIL     admin@intellops.local        Admin del seed
//   ADMIN_PASSWORD  admin-dev-password           password dev del seed
//   VUS             10                           VUs del escenario
//   DURATION        1m                           duración del escenario
//
// Se corre con `make load` (imagen `grafana/k6` pinneada en la red del compose);
// ver docs/operations/load-test.md.

import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomBytes } from 'k6/crypto';

const BASE_URL = (__ENV.BASE_URL || 'http://intellops-core:8000').replace(/\/+$/, '');
const ADMIN_EMAIL = __ENV.ADMIN_EMAIL || 'admin@intellops.local';
const ADMIN_PASSWORD = __ENV.ADMIN_PASSWORD || 'admin-dev-password';
const DURATION = __ENV.DURATION || '1m';
// `__ENV` siempre es string: la coerción explícita evita que el escenario se
// caiga por validación de opciones cuando VUS viene del entorno.
const VUS = parseInt(__ENV.VUS || '10', 10);

// Carga estándar (LT-3/D3): 10 eventos por iteración ≈ 100 eventos/s.
const BATCH_SIZE = 10;
// Rango realista de TTFB de frontend: por debajo del umbral de la v1 (500 ms),
// así los valores no disparan reglas de alerta durante la corrida.
const TTFB_MIN_MS = 120;
const TTFB_MAX_MS = 380;

export const options = {
  scenarios: {
    default: {
      executor: 'constant-vus',
      vus: VUS,
      duration: DURATION,
    },
  },
  // LT-3: p95 de las respuestas esperadas ≤ 500 ms, < 1 % de requests fallidos
  // y todos los checks en verde (202 con `accepted > 0`, D5).
  // `expected_response` es un system tag de `http_req_duration` (viene en
  // `--system-tags` por defecto), así que el selector es válido en k6 0.57.
  thresholds: {
    'http_req_duration{expected_response:true}': ['p(95)<=500'],
    http_req_failed: ['rate<0.01'],
    checks: ['rate==1'],
  },
};

/** UUID v4 a partir de 16 bytes aleatorios (`session_id` es UUID en el contrato). */
function uuidv4() {
  const bytes = new Uint8Array(randomBytes(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40; // versión 4
  bytes[8] = (bytes[8] & 0x3f) | 0x80; // variante RFC 4122
  const hex = [];
  for (let i = 0; i < bytes.length; i += 1) {
    hex.push((bytes[i] + 0x100).toString(16).slice(1));
  }
  return (
    hex.slice(0, 4).join('') +
    '-' +
    hex.slice(4, 6).join('') +
    '-' +
    hex.slice(6, 8).join('') +
    '-' +
    hex.slice(8, 10).join('') +
    '-' +
    hex.slice(10, 16).join('')
  );
}

/** TTFB pseudoaleatorio dentro del rango realista (Math.random es por VU). */
function ttfbMs() {
  return Math.round((TTFB_MIN_MS + Math.random() * (TTFB_MAX_MS - TTFB_MIN_MS)) * 10) / 10;
}

/** Lote RUM de `BATCH_SIZE` eventos, un evento con una métrica TTFB por muestra. */
function metricBatch() {
  const timestamp = new Date().toISOString();
  const events = [];
  for (let i = 0; i < BATCH_SIZE; i += 1) {
    events.push({
      schema_version: '1.0',
      timestamp: timestamp,
      session_id: uuidv4(),
      metrics: [
        {
          type: 'TTFB',
          value: ttfbMs(),
          unit: 'ms',
          timestamp: timestamp,
        },
      ],
    });
  }
  return { schema_version: '1.0', events: events };
}

/**
 * Provisiona la API key de la corrida: login Admin → app `k6-load-<ts>` → key.
 * Un único request por paso: si algo falla, k6 aborta antes de medir (k6 no
 * reintenta `setup`) y el mensaje dice qué paso rompió.
 */
export function setup() {
  const login = http.post(
    `${BASE_URL}/auth/login`,
    JSON.stringify({ email: ADMIN_EMAIL, password: ADMIN_PASSWORD }),
    { headers: { 'Content-Type': 'application/json' }, tags: { name: 'setup/login' } }
  );
  check(login, { 'setup: login 200': (r) => r.status === 200 });
  const token = login.json('access_token');
  if (!token) {
    throw new Error(`setup/login: ${login.status} ${login.body}`);
  }

  const authHeaders = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
  const name = `k6-load-${new Date().toISOString().replace(/[-:.]/g, '').slice(0, 15)}Z`;
  const app = http.post(
    `${BASE_URL}/applications`,
    JSON.stringify({ name: name }),
    { headers: authHeaders, tags: { name: 'setup/applications' } }
  );
  check(app, { 'setup: aplicación 201': (r) => r.status === 201 });
  const appId = app.json('app_id');
  if (!appId) {
    throw new Error(`setup/applications: ${app.status} ${app.body}`);
  }

  const issued = http.post(`${BASE_URL}/applications/${appId}/api-key`, null, {
    headers: authHeaders,
    tags: { name: 'setup/api-key' },
  });
  check(issued, { 'setup: api key 201': (r) => r.status === 201 });
  const apiKey = issued.json('api_key');
  if (!apiKey) {
    throw new Error(`setup/api-key: ${issued.status} ${issued.body}`);
  }

  console.log(`app de carga: app_id=${appId} name=${name}`);
  return { apiKey: apiKey, appId: appId };
}

/** Una iteración: un lote de 10 eventos a la ingesta, check y `sleep(1)`. */
export default function (data) {
  const response = http.post(`${BASE_URL}/telemetry/metrics`, JSON.stringify(metricBatch()), {
    headers: { 'Content-Type': 'application/json', 'X-API-Key': data.apiKey },
  });

  // D5: un 202 con todo rechazado mediría la latencia de una ingesta que no
  // ingiere, así que el check exige `accepted > 0`.
  check(response, {
    'ingesta 202': (r) => r.status === 202,
    'ingesta acepta eventos': (r) => {
      try {
        return (r.json('accepted') || 0) > 0;
      } catch (error) {
        return false;
      }
    },
  });

  sleep(1);
}

/** Cierra diciendo dónde quedó la app de carga que no se borra (D4). */
export function teardown(data) {
  console.log(
    `teardown: la app de carga app_id=${data.appId} queda en la base (D4); ` +
      'ver docs/operations/load-test.md §6'
  );
}
