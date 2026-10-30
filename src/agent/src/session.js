// Sesión del agente: identidad opaca en sessionStorage, rotación y muestreo.
// Contrato A.3 §2.1 (sesión) y §5 (muestreo).

import {
  DEFAULT_SAMPLE_RATE,
  SESSION_IDLE_TIMEOUT_MS,
  SESSION_MAX_LIFETIME_MS,
} from "./constants.js";

const SESSION_KEY = "intellops-session";

/** UUID v4 con `crypto.randomUUID` y fallback manual fuera de contexto seguro. */
export function createSessionId(crypto) {
  if (crypto && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  const bytes = new Uint8Array(16);
  if (crypto && typeof crypto.getRandomValues === "function") {
    crypto.getRandomValues(bytes);
  } else {
    for (let i = 0; i < bytes.length; i += 1) {
      bytes[i] = Math.floor(Math.random() * 256);
    }
  }
  bytes[6] = (bytes[6] & 0x0f) | 0x40; // versión 4
  bytes[8] = (bytes[8] & 0x3f) | 0x80; // variante RFC 4122
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0"));
  return (
    `${hex.slice(0, 4).join("")}-${hex.slice(4, 6).join("")}-` +
    `${hex.slice(6, 8).join("")}-${hex.slice(8, 10).join("")}-` +
    hex.slice(10, 16).join("")
  );
}

/** FNV-1a de 32 bits: hash estable y barato para el muestreo determinista. */
export function hash32(value) {
  let hash = 0x811c9dc5;
  for (let i = 0; i < value.length; i += 1) {
    hash ^= value.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash >>> 0;
}

/**
 * Decisión de muestreo a nivel de sesión: `hash(session_id) < rate * 2^32`.
 * Métricas y excepciones comparten la decisión para no mezclar sesiones.
 */
export function isSampled(sessionId, rate) {
  const effective = Number.isFinite(rate) ? rate : DEFAULT_SAMPLE_RATE;
  if (effective <= 0) return false;
  if (effective >= 1) return true;
  return hash32(sessionId) < effective * 4294967296;
}

/**
 * Sesión persistida: `{ id, createdAt, lastActivity }` en sessionStorage.
 * Se rota por inactividad (30 min) o por vida máxima (24 h).
 */
export function createSession(env, now) {
  const { storage, crypto } = env;
  const clock = now || (() => Date.now());
  const raw = storage.get(SESSION_KEY);
  let state = null;
  if (raw) {
    try {
      state = JSON.parse(raw);
    } catch {
      state = null;
    }
  }
  const current = clock();
  const expired =
    !state ||
    typeof state.id !== "string" ||
    !state.createdAt ||
    current - state.lastActivity > SESSION_IDLE_TIMEOUT_MS ||
    current - state.createdAt > SESSION_MAX_LIFETIME_MS;

  if (expired) {
    state = { id: createSessionId(crypto), createdAt: current, lastActivity: current };
  } else {
    state.lastActivity = current;
  }
  storage.set(SESSION_KEY, JSON.stringify(state));

  return {
    get id() {
      return state.id;
    },
    get createdAt() {
      return state.createdAt;
    },
    touch() {
      state.lastActivity = clock();
      storage.set(SESSION_KEY, JSON.stringify(state));
    },
  };
}
