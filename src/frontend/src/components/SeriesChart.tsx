/**
 * Serie temporal en SVG (ISS-B-05 D1: sin librería de gráficos).
 *
 * Una `<polyline>` con un punto por bucket, color y escala lineales propios. La
 * accesibilidad no depende del color ni de la forma: `<title>`/`<desc>` nombran
 * la serie y cada punto lleva su valor como etiqueta numérica.
 */

import { useId } from 'react';
import { formatClock, formatNumber } from '../format';

export interface SeriesPoint {
  /** Inicio del bucket, ISO 8601 UTC. */
  timestamp: string;
  /** AVG del bucket. */
  value: number;
  /** Sesiones distintas del bucket. */
  sessionCount: number;
}

export interface SeriesChartProps {
  points: SeriesPoint[];
  /** Nombre de la métrica (`TTFB`), usado en el texto accesible. */
  label: string;
}

const WIDTH = 640;
const HEIGHT = 220;
const PADDING = { top: 28, right: 16, bottom: 30, left: 56 };
/** Por encima de este número de buckets las etiquetas por punto se solapan. */
const MAX_POINT_LABELS = 24;

export function SeriesChart({ points, label }: SeriesChartProps) {
  const titleId = useId();
  const descId = useId();

  if (points.length === 0) {
    return null;
  }

  const ordered = [...points].sort(
    (left, right) => Date.parse(left.timestamp) - Date.parse(right.timestamp),
  );
  const values = ordered.map((point) => point.value);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const span = max - min || 1;
  const innerWidth = WIDTH - PADDING.left - PADDING.right;
  const innerHeight = HEIGHT - PADDING.top - PADDING.bottom;
  const step = ordered.length > 1 ? innerWidth / (ordered.length - 1) : 0;

  const coordinates = ordered.map((point, index) => {
    const x = PADDING.left + (ordered.length > 1 ? index * step : innerWidth / 2);
    const y = PADDING.top + innerHeight - ((point.value - min) / span) * innerHeight;
    return { x, y };
  });

  const first = ordered[0];
  const last = ordered[ordered.length - 1];
  const polyline = coordinates.map(({ x, y }) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  const showPointLabels = ordered.length <= MAX_POINT_LABELS;

  return (
    <svg
      className="series-chart"
      role="img"
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      aria-labelledby={titleId}
      aria-describedby={descId}
    >
      <title id={titleId}>{`Serie de ${label} — ${ordered.length} buckets`}</title>
      <desc id={descId}>
        {`Valor medio de ${label} por bucket: ${ordered.length} buckets, mínimo ${formatNumber(
          min,
        )} y máximo ${formatNumber(max)}.`}
      </desc>

      <line
        className="chart-axis"
        x1={PADDING.left}
        y1={PADDING.top + innerHeight}
        x2={WIDTH - PADDING.right}
        y2={PADDING.top + innerHeight}
      />
      <line
        className="chart-axis"
        x1={PADDING.left}
        y1={PADDING.top}
        x2={PADDING.left}
        y2={PADDING.top + innerHeight}
      />

      {!showPointLabels && (
        <>
          <text className="chart-label" x={PADDING.left - 8} y={PADDING.top + 4} textAnchor="end">
            {formatNumber(max)}
          </text>
          <text
            className="chart-label"
            x={PADDING.left - 8}
            y={PADDING.top + innerHeight}
            textAnchor="end"
          >
            {formatNumber(min)}
          </text>
        </>
      )}

      <polyline className="chart-line" points={polyline} fill="none" />

      {coordinates.map(({ x, y }, index) => (
        <circle key={`point-${ordered[index]?.timestamp ?? index}`} className="chart-dot" cx={x} cy={y} r={3} />
      ))}

      {showPointLabels &&
        coordinates.map(({ x, y }, index) => {
          const point = ordered[index];
          if (point === undefined) {
            return null;
          }
          return (
            <text
              key={`label-${point.timestamp}`}
              className="chart-value"
              x={x}
              y={y - 8}
              textAnchor="middle"
            >
              {formatNumber(point.value)}
            </text>
          );
        })}

      {first !== undefined && (
        <text className="chart-label" x={PADDING.left} y={HEIGHT - 8}>
          {formatClock(first.timestamp)}
        </text>
      )}
      {last !== undefined && last !== first && (
        <text className="chart-label" x={WIDTH - PADDING.right} y={HEIGHT - 8} textAnchor="end">
          {formatClock(last.timestamp)}
        </text>
      )}
    </svg>
  );
}
