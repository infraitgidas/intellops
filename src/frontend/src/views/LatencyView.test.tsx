import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { LatencyView } from './LatencyView';
import {
  jsonResponse,
  makeAggregate,
  makeMetricType,
  makeProbe,
  neverResolves,
  requestsTo,
  stubApi,
} from '../test/stubApi';

const API_KEY = 'ilp_de_prueba_no_real';

const catalog = [
  makeMetricType({ metric_type_id: 1, name: 'FCP', description: 'First Contentful Paint' }),
  makeMetricType({ metric_type_id: 2, name: 'TTFB', description: 'Time To First Byte' }),
];

const aggregates = [
  makeAggregate({ metric_type_id: 2, timestamp: '2026-01-01T10:02:00Z', value: 300, session_count: 20 }),
  makeAggregate({ metric_type_id: 2, timestamp: '2026-01-01T10:00:00Z', value: 100, session_count: 10 }),
  makeAggregate({ metric_type_id: 2, timestamp: '2026-01-01T10:01:00Z', value: 200, session_count: 12 }),
];

const probes = [
  makeProbe({ timestamp: '2026-01-01T10:02:00Z' }),
  makeProbe({
    timestamp: '2026-01-01T10:01:00Z',
    available: false,
    http_status: 503,
    outcome: 'http_error',
    latency_ms: 1500,
  }),
];

function renderView() {
  return render(<LatencyView apiKey={API_KEY} />);
}

function windowSeconds(url: URL | undefined): number {
  const start = Date.parse(url?.searchParams.get('start') ?? '');
  const end = Date.parse(url?.searchParams.get('end') ?? '');
  return Math.round((end - start) / 1000);
}

describe('LatencyView (QS-2, QS-4)', () => {
  it('muestra el estado de carga mientras espera la API', () => {
    stubApi({ types: neverResolves, metrics: neverResolves, probes: neverResolves });

    renderView();

    expect(screen.getByRole('status')).toHaveTextContent(/cargando/i);
  });

  it('pinta la serie, el resumen y la tabla de sondas con el catálogo cargado', async () => {
    const fetchMock = stubApi({
      types: () => jsonResponse(catalog),
      metrics: () => jsonResponse(aggregates),
      probes: () => jsonResponse(probes),
    });

    const { container } = renderView();

    await waitFor(() => {
      expect(container.querySelector('polyline')).not.toBeNull();
    });

    // TTFB es la métrica por defecto y la ventana inicial es de 15 min / 60 s.
    expect(screen.getByLabelText(/métrica/i)).toHaveValue('2');
    expect(screen.getByLabelText(/ventana/i)).toHaveValue('15m');

    const query = requestsTo(fetchMock, '/metrics/query')[0];
    expect(query?.searchParams.get('metric_type')).toBe('2');
    expect(query?.searchParams.get('bucket_seconds')).toBe('60');
    expect(windowSeconds(query)).toBe(900);
    expect(requestsTo(fetchMock, '/metrics/probes')[0]?.searchParams.get('limit')).toBe('50');

    // Resumen: buckets, máximo, promedio y sesiones acumuladas.
    const summary = container.querySelector('figcaption')?.textContent ?? '';
    expect(summary).toContain('3 buckets');
    expect(summary).toContain('máx 300');
    expect(summary).toContain('prom 200');
    expect(summary).toContain('42 sesiones');

    // Tabla de sondas: encabezado + una fila por corrida.
    expect(screen.getAllByRole('row')).toHaveLength(3);
    expect(screen.getByText('503')).toBeInTheDocument();
    expect(screen.getByText('http_error')).toBeInTheDocument();
    expect(screen.getByText('Sí')).toBeInTheDocument();
    expect(screen.getByText('No')).toBeInTheDocument();
  });

  it('ordena la serie por timestamp aunque la API la devuelva desordenada', async () => {
    stubApi({
      types: () => jsonResponse(catalog),
      metrics: () => jsonResponse(aggregates),
      probes: () => jsonResponse(probes),
    });

    const { container } = renderView();

    await waitFor(() => {
      expect(container.querySelector('polyline')).not.toBeNull();
    });
    const xs = (container.querySelector('polyline')?.getAttribute('points') ?? '')
      .trim()
      .split(/\s+/)
      .map((pair) => Number(pair.split(',')[0]));
    expect([...xs].sort((a, b) => a - b)).toEqual(xs);
  });

  it('cambiar de ventana vuelve a consultar con el bucket del preset', async () => {
    const user = userEvent.setup();
    const fetchMock = stubApi({
      types: () => jsonResponse(catalog),
      metrics: () => jsonResponse(aggregates),
      probes: () => jsonResponse(probes),
    });

    renderView();
    await screen.findByRole('img', { name: /serie de ttfb/i });

    await user.selectOptions(screen.getByLabelText(/ventana/i), '24h');

    await waitFor(() => {
      expect(requestsTo(fetchMock, '/metrics/query')).toHaveLength(2);
    });
    const latest = requestsTo(fetchMock, '/metrics/query').at(-1);
    expect(latest?.searchParams.get('bucket_seconds')).toBe('900');
    expect(windowSeconds(latest)).toBe(86400);
    expect(latest?.searchParams.get('metric_type')).toBe('2');
  });

  it('cambiar de métrica consulta el metric_type elegido', async () => {
    const user = userEvent.setup();
    const fetchMock = stubApi({
      types: () => jsonResponse(catalog),
      metrics: () => jsonResponse(aggregates),
      probes: () => jsonResponse(probes),
    });

    renderView();
    await screen.findByRole('img', { name: /serie de ttfb/i });

    await user.selectOptions(screen.getByLabelText(/métrica/i), '1');

    await waitFor(() => {
      expect(requestsTo(fetchMock, '/metrics/query')).toHaveLength(2);
    });
    expect(requestsTo(fetchMock, '/metrics/query').at(-1)?.searchParams.get('metric_type')).toBe('1');
  });

  it('muestra el error y Reintentar vuelve a pedir los datos', async () => {
    let fail = true;
    const user = userEvent.setup();
    const fetchMock = stubApi({
      types: () => jsonResponse(catalog),
      metrics: () =>
        fail ? jsonResponse({ detail: 'internal error' }, 500) : jsonResponse(aggregates),
      probes: () => jsonResponse(probes),
    });

    const { container } = renderView();

    expect(await screen.findByText(/no se pudieron cargar los datos/i)).toBeInTheDocument();
    expect(screen.getByText('internal error')).toBeInTheDocument();
    expect(container.querySelector('polyline')).toBeNull();

    fail = false;
    await user.click(screen.getByRole('button', { name: /reintentar/i }));

    await waitFor(() => {
      expect(container.querySelector('polyline')).not.toBeNull();
    });
    expect(requestsTo(fetchMock, '/metrics/query')).toHaveLength(2);
  });

  it('muestra el estado vacío y no un gráfico en blanco', async () => {
    stubApi({
      types: () => jsonResponse(catalog),
      metrics: () => jsonResponse([]),
      probes: () => jsonResponse([]),
    });

    const { container } = renderView();

    expect(await screen.findByText(/sin datos en la ventana/i)).toBeInTheDocument();
    expect(container.querySelector('polyline')).toBeNull();
    expect(screen.queryByRole('img')).toBeNull();
  });
});
