// Agente RUM de navegador — punto de entrada.
// Implementa el contrato A.3 v0.1 (docs/architecture/ContratoAgenteRUM.md).
// Sin dependencias de runtime: el bundle es un IIFE minificado (≤ 30 KB gzip).

import {
  AGENT_VERSION,
  DEFAULT_SAMPLE_RATE,
  FLUSH_EXCEPTIONS_COUNT,
  FLUSH_EXCEPTIONS_INTERVAL_MS,
  FLUSH_METRICS_COUNT,
  FLUSH_METRICS_INTERVAL_MS,
  MAX_METRICS_PER_EVENT,
  SCHEMA_VERSION,
} from "./constants.js";
import { buildPageViewMetrics, createExceptionGate, normalizeException, observeFcp, readTtfb } from "./capture.js";
import { createQueue, splitIntoRequests } from "./queue.js";
import { createTransport } from "./transport.js";
import { isCollectionAllowed, sanitizeUrl, truncateUserAgent } from "./privacy.js";
import { createSession, isSampled } from "./session.js";

/** Envuelve un Storage del navegador; degrada a memoria si no está disponible. */
function createStorage(getter) {
  let storage = null;
  try {
    storage = getter();
    const probe = "__intellops_probe__";
    storage.setItem(probe, probe);
    storage.removeItem(probe);
  } catch {
    storage = null;
  }
  const memory = new Map();
  return {
    get(key) {
      if (storage) {
        try {
          return storage.getItem(key);
        } catch {
          return memory.has(key) ? memory.get(key) : null;
        }
      }
      return memory.has(key) ? memory.get(key) : null;
    },
    set(key, value) {
      if (storage) {
        try {
          storage.setItem(key, value);
          return;
        } catch {
          /* cuota o modo privado: cae a memoria */
        }
      }
      memory.set(key, value);
    },
    remove(key) {
      if (storage) {
        try {
          storage.removeItem(key);
        } catch {
          /* ignora */
        }
      }
      memory.delete(key);
    },
  };
}

/** Construye el entorno desde el objeto global del navegador. */
export function browserEnv(scope) {
  const view = scope || (typeof globalThis !== "undefined" ? globalThis : {});
  return {
    window: view,
    document: view.document,
    navigator: view.navigator || {},
    performance: view.performance,
    PerformanceObserver: view.PerformanceObserver,
    fetch: typeof view.fetch === "function" ? view.fetch.bind(view) : undefined,
    AbortController: view.AbortController,
    crypto: view.crypto,
    location: view.location,
    storage: createStorage(() => view.sessionStorage),
    optOutStorage: createStorage(() => view.localStorage),
  };
}

/** Punto de entrada del contrato: `IntellOpsRUM.init({ apiKey, endpoint, ... })`. */
export function init(config, env) {
  const cfg = config || {};
  if (!cfg.apiKey || !cfg.endpoint) {
    throw new Error("IntellOpsRUM.init requiere apiKey y endpoint");
  }
  const runtime = env || browserEnv();
  if (!isCollectionAllowed({ navigator: runtime.navigator, storage: runtime.optOutStorage }, cfg.consent !== false)) {
    return { enabled: false, reason: "not_allowed" };
  }
  if (typeof runtime.fetch !== "function") {
    return { enabled: false, reason: "no_fetch" };
  }

  const sampleRate = Number.isFinite(cfg.sampleRate) ? cfg.sampleRate : DEFAULT_SAMPLE_RATE;
  const session = createSession(runtime);
  const sampled = isSampled(session.id, sampleRate);

  const counters = { sent: 0, dropped: 0, rejected: 0, failed: 0 };
  if (!sampled) {
    return { enabled: false, reason: "not_sampled", sessionId: session.id, counters };
  }

  const metricsQueue = createQueue();
  const exceptionsQueue = createQueue();
  const gate = createExceptionGate();
  const transport = createTransport(runtime, {
    apiKey: cfg.apiKey,
    endpoint: cfg.endpoint.replace(/\/$/, ""),
    timeoutMs: cfg.timeoutMs,
  });

  const pageUrl = sanitizeUrl(
    cfg.pageUrl || (runtime.location && runtime.location.href),
    runtime.location && runtime.location.origin,
  );
  const userAgent = truncateUserAgent(runtime.navigator.userAgent);
  const timers = [];

  function enqueueMetrics(ttfb, fcp) {
    const metrics = buildPageViewMetrics(ttfb, fcp);
    if (metrics.length === 0) return;
    const metadata = { sample_rate: sampleRate, agent_version: AGENT_VERSION };
    const event = {
      schema_version: SCHEMA_VERSION,
      timestamp: envelopeTimestamp(runtime.performance),
      session_id: session.id,
      metrics: metrics
        .slice(0, MAX_METRICS_PER_EVENT)
        .map((metric) => ({ ...metric, page_url: pageUrl, metadata })),
    };
    // §2.2: `user_agent` se consume desde el metadata DEL EVENTO
    // (queue.py:253-263); en metrics[].metadata no llega a user_session.
    if (userAgent) event.metadata = { user_agent: userAgent };
    metricsQueue.push(event);
    session.touch();
    maybeFlush();
  }

  function enqueueException(source, isRejection) {
    const normalized = normalizeException(source, isRejection);
    if (!gate(normalized.errorType, normalized.message).accepted) {
      counters.dropped += 1;
      return;
    }
    const event = {
      schema_version: SCHEMA_VERSION,
      error_type: normalized.errorType,
      message: normalized.message,
      session_id: session.id,
      timestamp: new Date().toISOString(),
      sample_rate: sampleRate,
    };
    if (normalized.stackTrace) event.stack_trace = normalized.stackTrace;
    exceptionsQueue.push(event);
    maybeFlush();
  }

  async function flushQueue(queue, path, force) {
    const threshold = path.endsWith("exceptions") ? FLUSH_EXCEPTIONS_COUNT : FLUSH_METRICS_COUNT;
    if (!force && queue.length < threshold) return;
    const events = queue.take(queue.length);
    if (events.length === 0) return;
    for (const chunk of splitIntoRequests(events)) {
      const result = await transport.send(path, {
        schema_version: SCHEMA_VERSION,
        events: chunk,
      });
      if (result.ok) {
        counters.sent += chunk.length;
        const rejected = result.body && result.body.rejected;
        if (Array.isArray(rejected) && rejected.length > 0) {
          counters.rejected += rejected.length;
        }
      } else {
        counters.failed += chunk.length;
      }
      if (transport.stopped) break;
    }
  }

  function maybeFlush() {
    void flushQueue(metricsQueue, "/telemetry/metrics", false);
    void flushQueue(exceptionsQueue, "/telemetry/exceptions", false);
  }

  function flushAll() {
    settlePendingPageView();
    return Promise.all([
      flushQueue(metricsQueue, "/telemetry/metrics", true),
      flushQueue(exceptionsQueue, "/telemetry/exceptions", true),
    ]);
  }

  // TTFB del page view actual. El page view queda pendiente hasta que llega FCP
  // o hasta el próximo flush: así un solo RumEvent transporta ambas métricas y
  // un FCP ausente se envía como TTFB solo, nunca como 0 (§2.2).
  let pendingPageView = { ttfb: readTtfb(runtime.performance) };

  function settlePendingPageView() {
    if (!pendingPageView || pendingPageView.ttfb === undefined) {
      pendingPageView = null;
      return;
    }
    const { ttfb } = pendingPageView;
    pendingPageView = null;
    enqueueMetrics(ttfb, undefined);
  }

  const disconnectFcp = observeFcp(runtime, (value) => {
    if (!pendingPageView) return;
    const { ttfb } = pendingPageView;
    pendingPageView = null;
    enqueueMetrics(ttfb, value);
  });

  const errorListener = (event) => enqueueException(event, false);
  const rejectionListener = (event) => enqueueException(event, true);
  const view = runtime.window;
  if (view && typeof view.addEventListener === "function") {
    view.addEventListener("error", errorListener);
    view.addEventListener("unhandledrejection", rejectionListener);
  }
  if (runtime.document && typeof runtime.document.addEventListener === "function") {
    runtime.document.addEventListener("visibilitychange", () => {
      if (runtime.document.visibilityState === "hidden") void flushAll();
    });
  }
  if (view && typeof view.addEventListener === "function") {
    view.addEventListener("pagehide", () => {
      void flushAll();
    });
  }

  timers.push(
    setInterval(() => {
      settlePendingPageView();
      void flushQueue(metricsQueue, "/telemetry/metrics", false);
    }, FLUSH_METRICS_INTERVAL_MS),
    setInterval(() => void flushQueue(exceptionsQueue, "/telemetry/exceptions", false), FLUSH_EXCEPTIONS_INTERVAL_MS),
  );

  return {
    enabled: true,
    sessionId: session.id,
    sampleRate,
    counters,
    flush: flushAll,
    stop() {
      timers.forEach((timer) => clearTimeout(timer));
      disconnectFcp();
      if (view && typeof view.removeEventListener === "function") {
        view.removeEventListener("error", errorListener);
        view.removeEventListener("unhandledrejection", rejectionListener);
      }
    },
  };
}

/** §2.2: el timestamp del envelope es el `timeOrigin` de la navegación. */
function envelopeTimestamp(performance) {
  const origin = performance && Number.isFinite(performance.timeOrigin) ? performance.timeOrigin : Date.now();
  return new Date(Math.floor(origin)).toISOString();
}

export default { init, browserEnv, version: AGENT_VERSION };
