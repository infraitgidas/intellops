// Transporte del agente: `fetch` con keepalive y `X-API-Key`, reintentos con
// backoff y circuito abierto ante credenciales inválidas.
// Contrato A.3 §4 (transporte), §7 (reintentos) y §8 (CORS).

import {
  BACKOFF_JITTER,
  BACKOFF_MS,
  MAX_ATTEMPTS,
  NO_RETRY_STATUSES,
  STOP_STATUSES,
} from "./constants.js";

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** Jitter de ±20 % sobre el backoff nominal (§7). */
export function backoffDelay(attempt, random) {
  const base = BACKOFF_MS[Math.min(attempt, BACKOFF_MS.length - 1)];
  const rand = random || Math.random;
  const delta = base * BACKOFF_JITTER;
  return Math.round(base - delta + rand() * delta * 2);
}

/**
 * Cliente de ingesta. Devuelve `{ ok, status, body }`; `ok` es false solo cuando
 * el batch no debe reintentarse. `sendBeacon` no se usa nunca: el API no acepta
 * headers y la API key viaja en `X-API-Key` (§4).
 */
export function createTransport(env, options) {
  const { fetch, AbortController } = env;
  const { apiKey, endpoint, timeoutMs = 10_000 } = options;
  const random = options.random || Math.random;
  const sleep = options.sleep || wait;
  let stopped = false;

  function request(url, payload) {
    const controller =
      typeof AbortController === "function" ? new AbortController() : null;
    const timer = controller
      ? setTimeout(() => controller.abort(), timeoutMs)
      : null;
    const init = {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
      body: JSON.stringify(payload),
      keepalive: true,
      mode: "cors",
      credentials: "omit",
    };
    if (controller) init.signal = controller.signal;
    return Promise.resolve()
      .then(() => fetch(url, init))
      .finally(() => {
        if (timer) clearTimeout(timer);
      });
  }

  return {
    get stopped() {
      return stopped;
    },
    async send(path, payload) {
      if (stopped) return { ok: false, status: 0, reason: "circuit_open" };
      const url = `${endpoint}${path}`;
      for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt += 1) {
        let response;
        try {
          response = await request(url, payload);
        } catch {
          response = null; // error de red o timeout: reintentable (§7)
        }

        if (response && response.ok) {
          let body = null;
          try {
            body = await response.json();
          } catch {
            body = null;
          }
          return { ok: true, status: response.status, body };
        }

        const status = response ? response.status : 0;
        if (STOP_STATUSES.includes(status)) {
          stopped = true; // 401/403: circuito abierto en esta página
          return { ok: false, status, reason: "stopped" };
        }
        if (NO_RETRY_STATUSES.includes(status)) {
          return { ok: false, status, reason: "permanent" };
        }
        if (attempt === MAX_ATTEMPTS - 1) {
          return { ok: false, status, reason: "exhausted" };
        }
        await sleep(backoffDelay(attempt, random));
      }
      return { ok: false, status: 0, reason: "exhausted" };
    },
  };
}
