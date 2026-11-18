import { vi } from 'vitest';
import type { Mock } from 'vitest';
import type { MetricAggregate, MetricTypeInfo, ProbeRun } from '../services/types';

/** Tipo de `fetch` que stubbean los tests (D5: `vi.stubGlobal`, sin MSW). */
export type FetchFn = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
export type FetchMock = Mock<FetchFn>;

/** Router mínimo por path: cada endpoint del contrato tiene su handler. */
export interface ApiStubHandlers {
  types?: () => Response | Promise<Response>;
  metrics?: () => Response | Promise<Response>;
  probes?: () => Response | Promise<Response>;
}

/** Respuesta JSON falsa: sólo se usa `ok`, `status` y `json()`. */
export function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as unknown as Response;
}

/** Respuesta que nunca llega: mantiene la vista en estado de carga. */
export function neverResolves(): Promise<Response> {
  return new Promise<Response>(() => {
    // deliberadamente pendiente
  });
}

/** Instala el stub global de `fetch` y devuelve el mock para inspeccionarlo. */
export function stubApi(handlers: ApiStubHandlers): FetchMock {
  const fetchMock = vi.fn<FetchFn>(async (input) => {
    const url = String(input);
    const handler = url.includes('/metrics/list')
      ? handlers.types
      : url.includes('/metrics/query')
        ? handlers.metrics
        : url.includes('/metrics/probes')
          ? handlers.probes
          : undefined;
    if (!handler) {
      return jsonResponse({ detail: `sin stub para ${url}` }, 404);
    }
    return handler();
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

/** URLs efectivamente pedidas, parseadas. */
export function requestUrls(fetchMock: FetchMock): URL[] {
  return fetchMock.mock.calls.map((call) => new URL(String(call[0])));
}

/** Sólo las requests a un path del contrato (p. ej. `/metrics/query`). */
export function requestsTo(fetchMock: FetchMock, path: string): URL[] {
  return requestUrls(fetchMock).filter((url) => url.pathname === path);
}

/** Cabeceras de la primera request al path indicado. */
export function headersOf(fetchMock: FetchMock, path: string): Record<string, string> {
  const call = fetchMock.mock.calls.find((entry) => String(entry[0]).includes(path));
  const raw = call?.[1]?.headers;
  if (raw === undefined) {
    return {};
  }
  if (raw instanceof Headers) {
    return Object.fromEntries(raw.entries());
  }
  if (Array.isArray(raw)) {
    return Object.fromEntries(raw);
  }
  return { ...raw };
}

const DEFAULT_APPLICATION_ID = '11111111-2222-3333-4444-555555555555';

export function makeAggregate(overrides: Partial<MetricAggregate> = {}): MetricAggregate {
  return {
    application_id: DEFAULT_APPLICATION_ID,
    metric_type_id: 1,
    timestamp: '2026-01-01T10:00:00Z',
    value: 100,
    session_count: 10,
    ...overrides,
  };
}

export function makeMetricType(overrides: Partial<MetricTypeInfo> = {}): MetricTypeInfo {
  return {
    metric_type_id: 1,
    name: 'TTFB',
    description: null,
    ...overrides,
  };
}

export function makeProbe(overrides: Partial<ProbeRun> = {}): ProbeRun {
  return {
    timestamp: '2026-01-01T10:00:00Z',
    target: 'http://localhost:8000/health',
    http_status: 200,
    outcome: 'ok',
    latency_ms: 42.5,
    available: true,
    ...overrides,
  };
}
