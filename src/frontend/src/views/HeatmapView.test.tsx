import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { HeatmapView } from './HeatmapView';
import {
  jsonResponse,
  makeAggregate,
  makeMetricType,
  neverResolves,
  requestsTo,
  stubApi,
} from '../test/stubApi';

const API_KEY = 'ilp_de_prueba_no_real';

const catalog = [
  makeMetricType({ metric_type_id: 1, name: 'TTFB', description: 'Time To First Byte' }),
  makeMetricType({ metric_type_id: 2, name: 'JS_EXCEPTION_RATE', description: 'Tasa de errores' }),
];

// Dos escalas incomparables: TTFB en ms y la tasa en fracción.
const aggregates = [
  makeAggregate({ metric_type_id: 1, timestamp: '2026-01-01T15:00:00Z', value: 100, session_count: 3 }),
  makeAggregate({ metric_type_id: 1, timestamp: '2026-01-01T15:01:00Z', value: 300, session_count: 5 }),
  makeAggregate({ metric_type_id: 2, timestamp: '2026-01-01T15:00:00Z', value: 0.01, session_count: 2 }),
  makeAggregate({ metric_type_id: 2, timestamp: '2026-01-01T15:01:00Z', value: 0.03, session_count: 6 }),
];

function renderView() {
  return render(<HeatmapView apiKey={API_KEY} />);
}

function sectionSeconds(url: URL | undefined): number {
  const start = Date.parse(url?.searchParams.get('start') ?? '');
  const end = Date.parse(url?.searchParams.get('end') ?? '');
  return Math.round((end - start) / 1000);
}

function cell(metricTypeId: number, timestamp: string): HTMLElement | null {
  return document.querySelector<HTMLElement>(
    `[data-metric-type-id="${metricTypeId}"][data-timestamp="${timestamp}"]`,
  );
}

describe('HeatmapView (QS-3, QS-4)', () => {
  it('muestra el estado de carga mientras espera la API', () => {
    stubApi({ types: neverResolves, metrics: neverResolves });

    renderView();

    expect(screen.getByRole('status')).toHaveTextContent(/cargando el heatmap/i);
    expect(cell(1, '2026-01-01T15:00:00Z')).toBeNull();
  });

  it('hace UNA sola consulta sin metric_type y pinta la grilla', async () => {
    const fetchMock = stubApi({
      types: () => jsonResponse(catalog),
      metrics: () => jsonResponse(aggregates),
    });

    renderView();

    await waitFor(() => {
      expect(cell(1, '2026-01-01T15:00:00Z')).not.toBeNull();
    });

    const queries = requestsTo(fetchMock, '/metrics/query');
    expect(queries).toHaveLength(1);
    expect(queries[0]?.searchParams.get('metric_type')).toBeNull();
    expect(queries[0]?.searchParams.get('bucket_seconds')).toBe('60');
    expect(sectionSeconds(queries[0])).toBe(3_600);
    expect(requestsTo(fetchMock, '/metrics/list')).toHaveLength(1);
    expect(requestsTo(fetchMock, '/metrics/probes')).toHaveLength(0);
  });

  it('normaliza cada métrica contra su propia fila aunque las escalas difieran', async () => {
    stubApi({
      types: () => jsonResponse(catalog),
      metrics: () => jsonResponse(aggregates),
    });

    renderView();

    await waitFor(() => {
      expect(cell(1, '2026-01-01T15:01:00Z')).not.toBeNull();
    });

    // El máximo de 300 ms y el de 0.03 caen en el mismo extremo de la escala.
    expect(cell(1, '2026-01-01T15:01:00Z')).toHaveAttribute('data-ratio', '1.000');
    expect(cell(2, '2026-01-01T15:01:00Z')).toHaveAttribute('data-ratio', '1.000');
    expect(cell(1, '2026-01-01T15:00:00Z')).toHaveAttribute('data-ratio', '0.000');
    expect(cell(2, '2026-01-01T15:00:00Z')).toHaveAttribute('data-ratio', '0.000');
  });

  it('deja neutra la celda de un bucket sin datos para una fila', async () => {
    stubApi({
      types: () => jsonResponse(catalog),
      metrics: () =>
        jsonResponse(
          aggregates.filter(
            (row) => !(row.metric_type_id === 2 && row.timestamp === '2026-01-01T15:01:00Z'),
          ),
        ),
    });

    renderView();

    await waitFor(() => {
      expect(cell(2, '2026-01-01T15:01:00Z')).not.toBeNull();
    });

    const empty = cell(2, '2026-01-01T15:01:00Z');
    expect(empty).toHaveAttribute('data-empty', 'true');
    expect(empty).toHaveClass('heatmap-cell-empty');
  });

  it('la tabla accesible lista valor y session_count de cada celda', async () => {
    const user = userEvent.setup();
    stubApi({
      types: () => jsonResponse(catalog),
      metrics: () => jsonResponse(aggregates),
    });

    renderView();
    await screen.findByRole('button', { name: /ver como tabla/i });

    await user.click(screen.getByRole('button', { name: /ver como tabla/i }));

    const table = screen.getByRole('table');
    expect(table).toHaveTextContent('TTFB');
    expect(table).toHaveTextContent('100 · 3 sesiones');
    expect(table).toHaveTextContent('0.0300 · 6 sesiones');
  });

  it('cambiar de ventana consulta el bucket del preset de D4 y recalcula la grilla', async () => {
    const user = userEvent.setup();
    const fetchMock = stubApi({
      types: () => jsonResponse(catalog),
      metrics: () => jsonResponse(aggregates),
    });

    renderView();
    await screen.findByRole('button', { name: /ver como tabla/i });

    await user.selectOptions(screen.getByLabelText(/ventana/i), '24h');

    await waitFor(() => {
      expect(requestsTo(fetchMock, '/metrics/query')).toHaveLength(2);
    });
    const latest = requestsTo(fetchMock, '/metrics/query').at(-1);
    expect(latest?.searchParams.get('bucket_seconds')).toBe('900');
    expect(latest?.searchParams.get('metric_type')).toBeNull();
    expect(sectionSeconds(latest)).toBe(86_400);
  });

  it('muestra el error y Reintentar vuelve a pedir los datos', async () => {
    let fail = true;
    const user = userEvent.setup();
    const fetchMock = stubApi({
      types: () => jsonResponse(catalog),
      metrics: () => (fail ? jsonResponse({ detail: 'internal error' }, 500) : jsonResponse(aggregates)),
    });

    renderView();

    expect(await screen.findByText(/no se pudieron cargar los datos/i)).toBeInTheDocument();
    expect(screen.getByText('internal error')).toBeInTheDocument();
    expect(cell(1, '2026-01-01T15:00:00Z')).toBeNull();

    fail = false;
    await user.click(screen.getByRole('button', { name: /reintentar/i }));

    await waitFor(() => {
      expect(cell(1, '2026-01-01T15:00:00Z')).not.toBeNull();
    });
    expect(requestsTo(fetchMock, '/metrics/query')).toHaveLength(2);
  });

  it('muestra el estado vacío cuando no hay datos en la ventana', async () => {
    stubApi({
      types: () => jsonResponse(catalog),
      metrics: () => jsonResponse([]),
    });

    renderView();

    expect(await screen.findByText(/sin datos en la ventana/i)).toBeInTheDocument();
    expect(document.querySelector('.heatmap-grid')).toBeNull();
    expect(screen.queryByRole('table')).toBeNull();
  });
});
