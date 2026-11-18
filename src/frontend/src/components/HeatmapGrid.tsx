/**
 * Grilla del heatmap UX (QS-3, ISS-B-05 D3).
 *
 * Filas = `metric_type` del catálogo con al menos un bucket con datos (en orden
 * de catálogo), columnas = unión ordenada de `timestamp` de la respuesta, y
 * color = `value` normalizado **por fila**: TTFB en ms y una tasa en fracción no
 * comparten escala. Una celda sin dato queda neutra (`--cell-empty`) y nunca se
 * interpola; una fila con máximo == mínimo usa el color medio (sin dividir por
 * cero).
 *
 * El color no es el único canal: cada celda expone `name`, hora del bucket,
 * `value` y `session_count` en `title`/`aria-label`, hay una leyenda con texto y
 * el botón "Ver como tabla" renderiza una `<table>` con los mismos números.
 */

import { Fragment, useState } from 'react';
import { formatClock, formatDateTime, formatNumber } from '../format';
import type { MetricAggregate, MetricTypeInfo } from '../services/types';

export interface HeatmapCell {
  /** Inicio del bucket, ISO 8601 UTC. */
  timestamp: string;
  /** AVG del bucket; `null` cuando no hay filas para esa métrica en el bucket. */
  value: number | null;
  /** Sesiones distintas del bucket; `null` cuando no hay dato. */
  sessionCount: number | null;
  /** Posición en la escala de la fila (0 = mínimo, 1 = máximo); `null` = sin dato. */
  ratio: number | null;
}

export interface HeatmapRow {
  metricTypeId: number;
  name: string;
  /** Mínimo de la fila (sólo buckets con datos). */
  min: number;
  /** Máximo de la fila (sólo buckets con datos). */
  max: number;
  cells: HeatmapCell[];
}

export interface HeatmapModel {
  columns: string[];
  rows: HeatmapRow[];
}

/** Ratio del punto medio: se usa cuando la fila tiene máximo == mínimo. */
const MID_RATIO = 0.5;

/**
 * Pivotea la respuesta de `/metrics/query` (todas las métricas, una request) en
 * filas × columnas normalizadas por fila.
 *
 * Los `metric_type_id` que no están en el catálogo no tienen nombre y se omiten:
 * la fila se nombra con `/metrics/list` (D3). Si la API repitiera una fila para
 * el mismo (métrica, bucket), gana la última.
 */
export function buildHeatmap(
  aggregates: readonly MetricAggregate[],
  catalog: readonly MetricTypeInfo[],
): HeatmapModel {
  const columns = [...new Set(aggregates.map((row) => row.timestamp))].sort(
    (left, right) => Date.parse(left) - Date.parse(right),
  );

  const byCell = new Map<string, MetricAggregate>();
  for (const aggregate of aggregates) {
    byCell.set(`${aggregate.metric_type_id}|${aggregate.timestamp}`, aggregate);
  }

  const rows: HeatmapRow[] = [];
  for (const metricType of catalog) {
    const present = columns
      .map((timestamp) => byCell.get(`${metricType.metric_type_id}|${timestamp}`))
      .filter((aggregate): aggregate is MetricAggregate => aggregate !== undefined);

    if (present.length === 0) {
      continue;
    }

    const values = present.map((aggregate) => aggregate.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min;

    rows.push({
      metricTypeId: metricType.metric_type_id,
      name: metricType.name,
      min,
      max,
      cells: columns.map((timestamp) => {
        const aggregate = byCell.get(`${metricType.metric_type_id}|${timestamp}`);
        if (aggregate === undefined) {
          return { timestamp, value: null, sessionCount: null, ratio: null };
        }
        return {
          timestamp,
          value: aggregate.value,
          sessionCount: aggregate.session_count,
          ratio: span === 0 ? MID_RATIO : (aggregate.value - min) / span,
        };
      }),
    });
  }

  return { columns, rows };
}

/** Color de una celda con dato: verde del tema, de oscuro (mínimo) a claro (máximo). */
export function cellColor(ratio: number): string {
  const clamped = Math.min(1, Math.max(0, ratio));
  const lightness = 20 + clamped * 40;
  const saturation = 45 + clamped * 25;
  return `hsl(160 ${saturation.toFixed(1)}% ${lightness.toFixed(1)}%)`;
}

export interface HeatmapGridProps {
  model: HeatmapModel;
}

export function HeatmapGrid({ model }: HeatmapGridProps) {
  const [showTable, setShowTable] = useState(false);

  return (
    <div className="heatmap">
      <div className="heatmap-toolbar">
        <button
          type="button"
          aria-pressed={showTable}
          onClick={() => setShowTable((current) => !current)}
        >
          {showTable ? 'Ver como grilla' : 'Ver como tabla'}
        </button>
      </div>

      {showTable ? (
        <HeatmapTable model={model} />
      ) : (
        <div className="heatmap-scroll">
          <div
            className="heatmap-grid"
            style={{
              gridTemplateColumns: `minmax(7rem, max-content) repeat(${model.columns.length}, minmax(1.4rem, 1fr))`,
            }}
          >
            <div className="heatmap-corner" aria-hidden="true" />
            {model.columns.map((timestamp) => (
              <div className="heatmap-col-label" key={timestamp} title={formatDateTime(timestamp)}>
                {formatClock(timestamp)}
              </div>
            ))}

            {model.rows.map((row) => (
              <Fragment key={row.metricTypeId}>
                <div className="heatmap-row-label">
                  <span className="heatmap-row-name">{row.name}</span>
                  <span className="heatmap-row-range">
                    {`${formatNumber(row.min)} – ${formatNumber(row.max)}`}
                  </span>
                </div>
                {row.cells.map((cell) => (
                  <HeatmapCellView
                    key={cell.timestamp}
                    metricTypeId={row.metricTypeId}
                    name={row.name}
                    cell={cell}
                  />
                ))}
              </Fragment>
            ))}
          </div>
        </div>
      )}

      <HeatmapLegend />
    </div>
  );
}

interface HeatmapCellViewProps {
  metricTypeId: number;
  name: string;
  cell: HeatmapCell;
}

function HeatmapCellView({ metricTypeId, name, cell }: HeatmapCellViewProps) {
  const base = `${name} · ${formatClock(cell.timestamp)}`;

  if (cell.value === null || cell.sessionCount === null || cell.ratio === null) {
    const label = `${base} · sin datos`;
    return (
      <div
        className="heatmap-cell heatmap-cell-empty"
        role="img"
        data-metric-type-id={metricTypeId}
        data-timestamp={cell.timestamp}
        data-empty="true"
        title={label}
        aria-label={label}
      />
    );
  }

  const label = `${base} · valor ${formatNumber(cell.value)} · ${cell.sessionCount} sesiones`;
  return (
    <div
      className="heatmap-cell"
      role="img"
      data-metric-type-id={metricTypeId}
      data-timestamp={cell.timestamp}
      data-empty="false"
      data-ratio={cell.ratio.toFixed(3)}
      style={{ backgroundColor: cellColor(cell.ratio) }}
      title={label}
      aria-label={label}
    />
  );
}

interface HeatmapTableProps {
  model: HeatmapModel;
}

/** Tabla alternativa accesible: los mismos números que la grilla, sin color. */
function HeatmapTable({ model }: HeatmapTableProps) {
  return (
    <div className="table-scroll">
      <table className="heatmap-table">
        <caption>
          {`Heatmap de ${model.rows.length} métricas por ${model.columns.length} buckets (valor · sesiones)`}
        </caption>
        <thead>
          <tr>
            <th scope="col">Métrica</th>
            {model.columns.map((timestamp) => (
              <th scope="col" key={timestamp}>
                {formatClock(timestamp)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {model.rows.map((row) => (
            <tr key={row.metricTypeId}>
              <th scope="row">{row.name}</th>
              {row.cells.map((cell) => (
                <td key={cell.timestamp}>
                  {cell.value === null || cell.sessionCount === null
                    ? '—'
                    : `${formatNumber(cell.value)} · ${cell.sessionCount} sesiones`}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Leyenda con texto: la escala es relativa a cada fila y el gris es "sin datos". */
export function HeatmapLegend() {
  const stops = [0, 0.25, 0.5, 0.75, 1];

  return (
    <div className="heatmap-legend">
      <p className="heatmap-legend-title">Escala relativa por fila</p>
      <div
        className="heatmap-legend-ramp"
        role="img"
        aria-label="Rampa de color: 0 % es el mínimo de la fila y 100 % su máximo"
      >
        {stops.map((stop) => (
          <span
            key={stop}
            className="heatmap-legend-swatch"
            style={{ backgroundColor: cellColor(stop) }}
          />
        ))}
        <span className="heatmap-legend-swatch heatmap-legend-swatch-empty" />
      </div>
      <p className="heatmap-legend-help">
        0 % = mínimo de la fila · 100 % = máximo de la fila. Cada fila usa su propio rango, así
        que TTFB (ms) y una tasa (fracción) no comparten escala. Gris = bucket sin datos: no se
        interpola.
      </p>
    </div>
  );
}
