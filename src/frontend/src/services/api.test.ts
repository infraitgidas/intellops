import { describe, expect, it, vi } from 'vitest';
import {
  API_BASE_URL,
  ApiError,
  getMetricTypes,
  getMetrics,
  getProbes,
  isAuthError,
} from './api';
import { headersOf, jsonResponse, requestUrls, stubApi } from '../test/stubApi';

const API_KEY = 'ilp_de_prueba_no_real';

describe('cliente HTTP de /metrics (D4)', () => {
  it('usa la base local por defecto', () => {
    expect(API_BASE_URL).toBe('http://localhost:8000');
  });

  it('getMetrics envía la key, los parámetros del contrato y devuelve el arreglo', async () => {
    const aggregates = [
      {
        application_id: '11111111-2222-3333-4444-555555555555',
        metric_type_id: 3,
        timestamp: '2026-01-01T10:00:00Z',
        value: 123.5,
        session_count: 4,
      },
    ];
    const fetchMock = stubApi({ metrics: () => jsonResponse(aggregates) });

    const result = await getMetrics(
      {
        start: '2026-01-01T09:45:00.000Z',
        end: '2026-01-01T10:00:00.000Z',
        bucketSeconds: 60,
        metricTypeId: 3,
      },
      API_KEY,
    );

    expect(result).toEqual(aggregates);
    const [url] = requestUrls(fetchMock);
    expect(url?.origin + url?.pathname).toBe(`${API_BASE_URL}/metrics/query`);
    expect(url?.searchParams.get('start')).toBe('2026-01-01T09:45:00.000Z');
    expect(url?.searchParams.get('end')).toBe('2026-01-01T10:00:00.000Z');
    expect(url?.searchParams.get('bucket_seconds')).toBe('60');
    expect(url?.searchParams.get('metric_type')).toBe('3');
    expect(headersOf(fetchMock, '/metrics/query')['X-API-Key']).toBe(API_KEY);
  });

  it('omite metric_type cuando la consulta no filtra por métrica (heatmap)', async () => {
    const fetchMock = stubApi({ metrics: () => jsonResponse([]) });

    await getMetrics(
      {
        start: '2026-01-01T09:45:00.000Z',
        end: '2026-01-01T10:00:00.000Z',
        bucketSeconds: 300,
      },
      API_KEY,
    );

    const [url] = requestUrls(fetchMock);
    expect(url?.searchParams.has('metric_type')).toBe(false);
    expect(url?.searchParams.get('bucket_seconds')).toBe('300');
  });

  it('getMetricTypes pega en /metrics/list y tolera description null', async () => {
    const types = [{ metric_type_id: 1, name: 'TTFB', description: null }];
    const fetchMock = stubApi({ types: () => jsonResponse(types) });

    await expect(getMetricTypes(API_KEY)).resolves.toEqual(types);
    expect(requestUrls(fetchMock)[0]?.pathname).toBe('/metrics/list');
    expect(headersOf(fetchMock, '/metrics/list')['X-API-Key']).toBe(API_KEY);
  });

  it('getProbes pide el límite en la query-string', async () => {
    const fetchMock = stubApi({ probes: () => jsonResponse([]) });

    await expect(getProbes(50, API_KEY)).resolves.toEqual([]);
    const [url] = requestUrls(fetchMock);
    expect(url?.pathname).toBe('/metrics/probes');
    expect(url?.searchParams.get('limit')).toBe('50');
  });

  it('mapea el envelope {error} del contrato a ApiError', async () => {
    stubApi({
      types: () =>
        jsonResponse(
          { error: { code: 'invalid_api_key', message: 'invalid or unknown API key' } },
          401,
        ),
    });

    const failure = await getMetricTypes(API_KEY).catch((error: unknown) => error);

    expect(failure).toBeInstanceOf(ApiError);
    expect(failure).toMatchObject({
      status: 401,
      code: 'invalid_api_key',
      message: 'invalid or unknown API key',
    });
    expect(isAuthError(failure as ApiError)).toBe(true);
  });

  it('mapea el {detail} de FastAPI (422) sin perder el mensaje', async () => {
    stubApi({
      metrics: () =>
        jsonResponse({ detail: [{ msg: 'bucket_seconds must be at least 60' }] }, 422),
    });

    const failure = await getMetrics({ start: 'a', end: 'b', bucketSeconds: 30 }, API_KEY).catch(
      (error: unknown) => error,
    );

    expect(failure).toBeInstanceOf(ApiError);
    expect(failure).toMatchObject({ status: 422, code: 'http_422' });
    expect((failure as ApiError).message).toContain('bucket_seconds must be at least 60');
    expect(isAuthError(failure as ApiError)).toBe(false);
  });

  it('convierte un fallo de red en ApiError de status 0', async () => {
    const fetchMock = vi.fn<() => Promise<Response>>(() =>
      Promise.reject(new TypeError('Failed to fetch')),
    );
    vi.stubGlobal('fetch', fetchMock);

    const failure = await getProbes(50, API_KEY).catch((error: unknown) => error);

    expect(failure).toBeInstanceOf(ApiError);
    expect(failure).toMatchObject({ status: 0, code: 'network_error' });
  });

  it('no filtra la key en el mensaje de error (403 app_inactive)', async () => {
    stubApi({
      probes: () => jsonResponse({ error: { code: 'app_inactive', message: 'app inactive' } }, 403),
    });

    const failure = await getProbes(50, API_KEY).catch((error: unknown) => error);

    expect(failure).toMatchObject({ status: 403, code: 'app_inactive' });
    expect((failure as ApiError).message).not.toContain(API_KEY);
    expect((failure as ApiError).message).toBe('app inactive');
  });
});
