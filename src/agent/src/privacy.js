// Privacidad del agente RUM — contrato A.3 §9.
//
// Regla de oro: nada de query strings, fragmentos, cookies, IP ni PII sale del
// navegador. El saneado y la redacción ocurren ANTES del truncado, para que un
// recorte no deje media credencial en el payload.

import {
  MAX_MESSAGE_LEN,
  MAX_PAGE_URL_LEN,
  MAX_STACK_TRACE_LEN,
  MAX_USER_AGENT_LEN,
} from "./constants.js";

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const NUMERIC_SEGMENT_RE = /^\d+$/;

// Credenciales: email, tokens bearer/basic, API keys de la ingesta, y pares
// `clave=valor` con nombre sensible (password, token, secret, api_key, ...).
const EMAIL_RE = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;
const BEARER_RE = /\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]+/gi;
const API_KEY_RE = /\b(ilp|sk|pk|ghp|gho|xox[baprs])[_-][A-Za-z0-9_-]{8,}/g;
const SECRET_PAIR_RE =
  /(^|[?&;,\s])((?:password|passwd|pwd|token|secret|api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|session[_-]?id|sig|signature|key)=)[^&;,\s"'}]+/gi;
const JWT_RE = /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}/g;

/** Redacta credenciales y PII de un texto libre (message o stack trace). */
export function redact(text) {
  if (typeof text !== "string" || text === "") return "";
  return text
    .replace(BEARER_RE, "$1 [REDACTED]")
    .replace(API_KEY_RE, "[REDACTED]")
    .replace(JWT_RE, "[REDACTED]")
    .replace(EMAIL_RE, "[REDACTED]")
    .replace(SECRET_PAIR_RE, "$1$2[REDACTED]");
}

/**
 * Sanea una URL: descarta query y fragmento, reemplaza segmentos numéricos o
 * UUID por `{id}` y limita el largo. §9 del contrato.
 */
export function sanitizeUrl(url, origin) {
  if (typeof url !== "string" || url === "") return "";
  let parsed;
  try {
    parsed = new URL(url, origin || "http://localhost");
  } catch {
    return "";
  }
  const segments = parsed.pathname
    .split("/")
    .map((segment) =>
      NUMERIC_SEGMENT_RE.test(segment) || UUID_RE.test(segment)
        ? "{id}"
        : segment,
    );
  const clean = segments.join("/");
  const result = `${parsed.origin}${clean}`;
  return result.length > MAX_PAGE_URL_LEN
    ? result.slice(0, MAX_PAGE_URL_LEN)
    : result;
}

/** Trunca el user agent al límite del contrato. */
export function truncateUserAgent(value) {
  return typeof value === "string" ? value.slice(0, MAX_USER_AGENT_LEN) : "";
}

/** Aplica redacción y después trunca: el recorte nunca deja media credencial. */
export function safeMessage(value) {
  return redact(String(value ?? "")).slice(0, MAX_MESSAGE_LEN);
}

export function safeStackTrace(value) {
  if (value === undefined || value === null) return undefined;
  const text = redact(String(value)).slice(0, MAX_STACK_TRACE_LEN);
  return text === "" ? undefined : text;
}

/**
 * ¿El usuario dio consentimiento de recolección? Sin consentimiento explícito
 * el agente no se inicializa (§9). DNT y GPC detienen la recolección, igual que
 * la clave de opt-out en localStorage.
 */
export function isCollectionAllowed(env, consent) {
  if (consent !== true) return false;
  const { navigator = {}, storage } = env;
  if (navigator.doNotTrack === "1" || navigator.doNotTrack === "yes") {
    return false;
  }
  if (navigator.globalPrivacyControl === true) return false;
  return storage.get("intellops-optout") === null;
}
