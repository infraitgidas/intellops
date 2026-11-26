import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { buildHeatmap, HeatmapGrid } from './HeatmapGrid';
import { formatClock } from '../format';
import { makeAggregate, makeMetricType } from '../test/stubApi';
import type { MetricAggregate, MetricTypeInfo } from '../services/types';

const catalog: MetricTypeInfo[] = [
  makeMetricType({ metric_type_id: 1, name: 'TTFB', description: 'Time To First Byte' }),
  makeMetricType({ metric_type_id: 2, name: 'JS_EXCEPTION_RATE', description: 'Tasa de errores' }),
  makeMetricType({ metric_type_id: 3, name: 'LCP', description: 'Largest Contentful Paint' }),
  makeMetricType({ metric_type_id: 4, name: 'CLS', description: 'Cumulative Layout Shift' }),
];

// TTFB en ms (~200), JS_EXCEPTION_RATE en fracción (~0.02) y CLS con un solo
// bucket (máximo == mínimo). LCP no tiene datos. El bucket de las 15:01 no
// existe para JS_EXCEPTION_RATE: esa celda debe quedar neutra.
const aggregates: MetricAggregate[] = [
  makeAggregate({ metric_type_id: 1, timestamp: '2026-01-01T15:02:00Z', value: 300, session_count: 5 }),
  makeAggregate({ metric_type_id: 1, timestamp: '2026-01-01T15:00:00Z', value: 100, session_count: 3 }),
  makeAggregate({ metric_type_id: 1, timestamp: '2026-01-01T15:01:00Z', value: 200, session_count: 4 }),
  makeAggregate({ metric_type_id: 2, timestamp: '2026-01-01T15:00:00Z', value: 0.01, session_count: 2 }),
  makeAggregate({ metric_type_id: 2, timestamp: '2026-01-01T15:02:00Z', value: 0.03, session_count: 6 }),
  makeAggregate({ metric_type_id: 4, timestamp: '2026-01-01T15:00:00Z', value: 0.05, session_count: 1 }),
];

const model = buildHeatmap(aggregates, catalog);

function cellOf(metricTypeId: number, timestamp: string): HTMLElement {
  const cell = document.querySelector<HTMLElement>(
    `[data-metric-type-id="${metricTypeId}"][data-timestamp="${timestamp}"]`,
  );
  if (cell === null) {
    throw new Error(`sin celda para metric_type ${metricTypeId} en ${timestamp}`);
  }
  return cell;
}

describe('buildHeatmap (QS-3)', () => {
  it('arma filas sólo con métricas que tienen datos, en orden de catálogo', () => {
    expect(model.rows.map((row) => row.name)).toEqual(['TTFB', 'JS_EXCEPTION_RATE', 'CLS']);
  });

  it('usa la unión ordenada de timestamps como columnas', () => {
    expect(model.columns).toEqual([
      '2026-01-01T15:00:00Z',
      '2026-01-01T15:01:00Z',
      '2026-01-01T15:02:00Z',
    ]);
  });

  it('normaliza el ratio como (value - min) / (max - min), tal como lo pinta la grilla', () => {
    const ttfb = model.rows.find((row) => row.name === 'TTFB');
    expect(ttfb?.cells.map((cell) => cell.ratio)).toEqual([0, 0.5, 1]);
    const rate = model.rows.find((row) => row.name === 'JS_EXCEPTION_RATE');
    expect(rate?.cells.map((cell) => cell.ratio)).toEqual([0, null, 1]);
  });
});

describe('HeatmapGrid (QS-3)', () => {
  it('normaliza cada fila contra su propio mínimo y máximo', () => {
    render(<HeatmapGrid model={model} />);

    // TTFB ~200 ms y JS_EXCEPTION_RATE ~0.02 comparten el mismo ratio relativo.
    expect(cellOf(1, '2026-01-01T15:00:00Z')).toHaveAttribute('data-ratio', '0.000');
    expect(cellOf(1, '2026-01-01T15:02:00Z')).toHaveAttribute('data-ratio', '1.000');
    expect(cellOf(2, '2026-01-01T15:00:00Z')).toHaveAttribute('data-ratio', '0.000');
    expect(cellOf(2, '2026-01-01T15:02:00Z')).toHaveAttribute('data-ratio', '1.000');
  });

  it('pinta neutra la celda de un bucket sin datos, sin interpolar', () => {
    render(<HeatmapGrid model={model} />);

    const empty = cellOf(2, '2026-01-01T15:01:00Z');
    expect(empty).toHaveAttribute('data-empty', 'true');
    expect(empty).toHaveClass('heatmap-cell-empty');
    expect(empty).not.toHaveAttribute('data-ratio');
    expect(empty).toHaveAttribute('title', expect.stringContaining('sin datos'));
  });

  it('no divide por cero cuando el máximo de la fila es igual al mínimo', () => {
    render(<HeatmapGrid model={model} />);

    const single = cellOf(4, '2026-01-01T15:00:00Z');
    expect(single).toHaveAttribute('data-empty', 'false');
    expect(single).toHaveAttribute('data-ratio', '0.500');
  });

  it('expone nombre, hora del bucket, valor y sesiones en cada celda', () => {
    render(<HeatmapGrid model={model} />);

    const cell = cellOf(1, '2026-01-01T15:02:00Z');
    const expected = `TTFB · ${formatClock('2026-01-01T15:02:00Z')} · valor 300 · 5 sesiones`;
    expect(cell).toHaveAttribute('aria-label', expected);
    expect(cell).toHaveAttribute('title', expected);
  });

  it('muestra la leyenda con la escala relativa por fila y la celda neutra', () => {
    render(<HeatmapGrid model={model} />);

    expect(screen.getByText(/0 %/)).toBeInTheDocument();
    expect(screen.getByText(/100 %/)).toBeInTheDocument();
    expect(screen.getByText(/sin datos: no se interpola/i)).toBeInTheDocument();
  });

  it('Ver como tabla lista los mismos valores y session_count', async () => {
    const user = userEvent.setup();
    render(<HeatmapGrid model={model} />);

    const toggle = screen.getByRole('button', { name: /ver como tabla/i });
    expect(toggle).toHaveAttribute('aria-pressed', 'false');
    expect(screen.queryByRole('table')).toBeNull();

    await user.click(toggle);

    expect(toggle).toHaveAttribute('aria-pressed', 'true');
    const table = screen.getByRole('table');
    expect(table).toBeInTheDocument();
    expect(table.querySelectorAll('tbody tr')).toHaveLength(3);

    // Encabezados de columna: una hora por bucket.
    expect(screen.getAllByRole('columnheader')).toHaveLength(model.columns.length + 1);
    // Fila de TTFB: valor formateado + sesiones en la celda del bucket 15:02.
    const ttfbRow = screen.getByRole('rowheader', { name: /ttfb/i }).closest('tr');
    expect(ttfbRow).not.toBeNull();
    const cells = [...(ttfbRow?.querySelectorAll('td') ?? [])].map((cell) => cell.textContent);
    expect(cells[0]).toBe('100 · 3 sesiones');
    expect(cells[2]).toBe('300 · 5 sesiones');
    // Bucket sin datos para esa fila: guion, no un valor interpolado.
    expect(cells[1]).toBe('200 · 4 sesiones');
    const rateRow = screen.getByRole('rowheader', { name: /js_exception_rate/i }).closest('tr');
    const rateCells = [...(rateRow?.querySelectorAll('td') ?? [])].map((cell) => cell.textContent);
    expect(rateCells[1]).toBe('—');
  });
});
