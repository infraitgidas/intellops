import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SeriesChart } from './SeriesChart';
import type { SeriesPoint } from './SeriesChart';

const points: SeriesPoint[] = [
  { timestamp: '2026-01-01T10:00:00Z', value: 100, sessionCount: 4 },
  { timestamp: '2026-01-01T10:01:00Z', value: 200, sessionCount: 6 },
  { timestamp: '2026-01-01T10:02:00Z', value: 300, sessionCount: 8 },
];

describe('SeriesChart', () => {
  it('pinta un punto por bucket en una polyline', () => {
    const { container } = render(<SeriesChart points={points} label="TTFB" />);

    const polyline = container.querySelector('polyline');
    expect(polyline).not.toBeNull();
    expect(polyline?.getAttribute('points')?.trim().split(/\s+/)).toHaveLength(3);
  });

  it('expone título y descripción accesibles', () => {
    render(<SeriesChart points={points} label="TTFB" />);

    const chart = screen.getByRole('img', { name: /serie de ttfb/i });
    expect(chart).toBeInTheDocument();
    expect(chart.querySelector('desc')?.textContent).toMatch(/TTFB/);
    expect(chart.querySelector('desc')?.textContent).toMatch(/3 buckets/);
  });

  it('etiqueta numéricamente cada punto', () => {
    render(<SeriesChart points={points} label="TTFB" />);

    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('200')).toBeInTheDocument();
    expect(screen.getByText('300')).toBeInTheDocument();
  });

  it('ordena los puntos por timestamp aunque lleguen desordenados', () => {
    const unordered: SeriesPoint[] = [
      { timestamp: '2026-01-01T10:02:00Z', value: 300, sessionCount: 8 },
      { timestamp: '2026-01-01T10:00:00Z', value: 100, sessionCount: 4 },
      { timestamp: '2026-01-01T10:01:00Z', value: 200, sessionCount: 6 },
    ];
    const { container } = render(<SeriesChart points={unordered} label="TTFB" />);

    const coordinates = (container.querySelector('polyline')?.getAttribute('points') ?? '')
      .trim()
      .split(/\s+/)
      .map((pair) => Number(pair.split(',')[0]));
    expect(coordinates).toHaveLength(3);
    expect([...coordinates].sort((a, b) => a - b)).toEqual(coordinates);
  });
});
