// Captura de TTFB, FCP y excepciones JS no manejadas.
// Contrato A.3 §2.2 (métricas), §2.3 (excepciones) y §5 (topes por sesión).

import {
  ERROR_TYPES,
  EXCEPTION_DEDUP_WINDOW_MS,
  MAX_ERROR_TYPE_LEN,
  MAX_EXCEPTIONS_PER_SESSION,
  MAX_METRICS_PER_EVENT,
} from "./constants.js";
import { safeMessage, safeStackTrace } from "./privacy.js";

const ERROR_TYPE_SET = new Set(ERROR_TYPES);

/** Normaliza `error.name` al catálogo canónico; desconocido cae en `Other`. */
export function canonicalErrorType(name, isRejection) {
  if (isRejection) return "UnhandledRejection";
  if (typeof name !== "string" || name === "") return "Other";
  return ERROR_TYPE_SET.has(name) ? name : "Other";
}

/**
 * TTFB de la navegación: `responseStart - requestStart`, en ms.
 * Devuelve `undefined` cuando la Navigation Timing API no está disponible o
 * cuando el valor no es finito: nunca se inventa un 0 (§2.2).
 */
export function readTtfb(performance) {
  if (!performance || typeof performance.getEntriesByType !== "function") {
    return undefined;
  }
  const [navigation] = performance.getEntriesByType("navigation") || [];
  if (!navigation) return undefined;
  const { responseStart, requestStart } = navigation;
  if (!Number.isFinite(responseStart) || !Number.isFinite(requestStart)) {
    return undefined;
  }
  const value = responseStart - requestStart;
  return value >= 0 ? Math.round(value) : undefined;
}

/**
 * FCP observado con PerformanceObserver y, como respaldo, con las entradas de
 * paint ya registradas. Sin FCP no se envía la métrica.
 */
export function observeFcp(env, onFcp) {
  const { performance, PerformanceObserver } = env;
  const emit = (value) => {
    if (Number.isFinite(value) && value >= 0) onFcp(Math.round(value));
  };

  const existing =
    performance && typeof performance.getEntriesByType === "function"
      ? performance.getEntriesByType("paint") || []
      : [];
  const found = existing.find(
    (entry) => entry && entry.name === "first-contentful-paint",
  );
  if (found) {
    emit(found.startTime);
    return () => {};
  }

  if (typeof PerformanceObserver !== "function") return () => {};
  let observer;
  try {
    observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === "first-contentful-paint") {
          emit(entry.startTime);
          observer.disconnect();
        }
      }
    });
    observer.observe({ type: "paint", buffered: true });
  } catch {
    return () => {};
  }
  return () => {
    if (observer) observer.disconnect();
  };
}

/** Métricas de un page view: TTFB y, si ocurrió, FCP. Nunca un 0 inventado. */
export function buildPageViewMetrics(ttfb, fcp) {
  const metrics = [];
  if (ttfb !== undefined) metrics.push({ type: "TTFB", value: ttfb, unit: "ms" });
  if (fcp !== undefined) metrics.push({ type: "FCP", value: fcp, unit: "ms" });
  return metrics.slice(0, MAX_METRICS_PER_EVENT);
}

/**
 * Registro de excepciones con deduplicación por huella (60 s) y tope de 20 por
 * sesión. Devuelve `{ accepted, reason }` para poder contabilizar los descartes.
 */
export function createExceptionGate(now) {
  const clock = now || (() => Date.now());
  const seen = new Map();
  let accepted = 0;

  return function accept(errorType, message) {
    if (accepted >= MAX_EXCEPTIONS_PER_SESSION) {
      return { accepted: false, reason: "session_cap" };
    }
    const fingerprint = `${errorType}:${safeMessage(message)}`;
    const current = clock();
    for (const [key, timestamp] of seen) {
      if (current - timestamp > EXCEPTION_DEDUP_WINDOW_MS) seen.delete(key);
    }
    if (seen.has(fingerprint)) {
      return { accepted: false, reason: "duplicate" };
    }
    seen.set(fingerprint, current);
    accepted += 1;
    return { accepted: true };
  };
}

/** Normaliza el payload de `window.onerror` / `unhandledrejection`. */
export function normalizeException(source, isRejection) {
  let error = source;
  let message = "";
  if (isRejection) {
    error = source && source.reason !== undefined ? source.reason : source;
    message = error && error.message ? error.message : String(error ?? "");
  } else if (source && typeof source === "object" && "message" in source) {
    message = source.message;
  } else {
    message = String(source ?? "");
  }
  const name = error && typeof error === "object" ? error.name : undefined;
  const stack = error && typeof error === "object" ? error.stack : undefined;
  const errorType = canonicalErrorType(name, isRejection).slice(
    0,
    MAX_ERROR_TYPE_LEN,
  );
  return {
    errorType,
    message: safeMessage(message === "" ? errorType : message),
    stackTrace: safeStackTrace(stack),
  };
}
