// Verificación E2E del agente RUM contra una ingesta real (ISS-B-01, T9).
//
// Uso:
//   npm run build
//   INTELLOPS_API_KEY=ilp_... INTELLOPS_ENDPOINT=http://localhost:8000 \
//     node scripts/e2e.mjs
//
// Emite un page view con TTFB/FCP y una excepción no manejada, y falla si la
// ingesta no responde 202 con al menos un evento aceptado en cada endpoint.
import { setTimeout as delay } from "node:timers/promises";

import { init } from "../src/index.js";

const API_KEY = process.env.INTELLOPS_API_KEY;
const ENDPOINT = process.env.INTELLOPS_ENDPOINT || "http://localhost:8000";

if (!API_KEY) {
  console.error("Falta INTELLOPS_API_KEY (la API key se pide a la ingesta; nunca se versiona)");
  process.exit(2);
}

const responses = [];
const baseFetch = globalThis.fetch;
const fetch = async (url, init_) => {
  const response = await baseFetch(url, init_);
  const clone = response.clone();
  let body = null;
  try {
    body = await clone.json();
  } catch {
    body = null;
  }
  responses.push({ url, status: response.status, body });
  return response;
};

function target() {
  const listeners = new Map();
  return {
    listeners,
    addEventListener: (type, handler) => {
      if (!listeners.has(type)) listeners.set(type, []);
      listeners.get(type).push(handler);
    },
    removeEventListener: (type, handler) => {
      const list = listeners.get(type) || [];
      const index = list.indexOf(handler);
      if (index >= 0) list.splice(index, 1);
    },
    dispatch: (type, event = {}) => {
      for (const handler of listeners.get(type) || []) handler(event);
    },
  };
}

const memory = () => {
  const map = new Map();
  return {
    getItem: (key) => (map.has(key) ? map.get(key) : null),
    setItem: (key, value) => void map.set(key, String(value)),
    removeItem: (key) => void map.delete(key),
  };
};

const adapter = (storage) => ({
  get: (key) => storage.getItem(key),
  set: (key, value) => storage.setItem(key, value),
  remove: (key) => storage.removeItem(key),
});

const window = target();
const document = target();
const sessionStorage = memory();

const env = {
  window,
  document,
  navigator: { userAgent: "intellops-rum-e2e/1.0" },
  performance: {
    timeOrigin: Date.now(),
    getEntriesByType: (type) =>
      type === "navigation" ? [{ responseStart: 320, requestStart: 120 }] : [],
  },
  PerformanceObserver: undefined,
  fetch,
  AbortController: globalThis.AbortController,
  crypto: globalThis.crypto,
  location: { href: "https://shop.example.com/product/42?token=secret", origin: "https://shop.example.com" },
  storage: adapter(sessionStorage),
  optOutStorage: adapter(memory()),
};

const agent = init({ apiKey: API_KEY, endpoint: ENDPOINT, consent: true, sampleRate: 1 }, env);
if (!agent.enabled) {
  console.error(`El agente no se inicializó: ${agent.reason}`);
  process.exit(1);
}
console.log(`agente inicializado — sesión ${agent.sessionId}`);

// Page view: TTFB 200 ms (sin FCP observado, el flush lo envía solo).
await agent.flush();

// Excepción no manejada con PII, para verificar la redacción en la ingesta.
window.dispatch("error", new TypeError("e2e: render falló para federico@example.com"));
await agent.flush();
await delay(200);

let failures = 0;
for (const path of ["/telemetry/metrics", "/telemetry/exceptions"]) {
  const call = responses.find((item) => item.url.endsWith(path));
  if (!call) {
    console.error(`FALLA ${path}: no se envió ningún request`);
    failures += 1;
    continue;
  }
  if (call.status !== 202) {
    console.error(`FALLA ${path}: status ${call.status} — ${JSON.stringify(call.body)}`);
    failures += 1;
    continue;
  }
  const accepted = call.body && typeof call.body.accepted === "number" ? call.body.accepted : 0;
  const rejected = call.body && Array.isArray(call.body.rejected) ? call.body.rejected.length : 0;
  console.log(`OK ${path}: 202 accepted=${accepted} rejected=${rejected} batch=${call.body && call.body.batch_id}`);
  if (accepted < 1 || rejected !== 0) failures += 1;
}

console.log(`counters: ${JSON.stringify(agent.counters)}`);
agent.stop();
process.exit(failures === 0 ? 0 : 1);
