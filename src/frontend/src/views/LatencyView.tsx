/**
 * Vista de latencias RUM (QS-2, ISS-B-05 D4).
 *
 * Catálogo (`/metrics/list`) → selector de métrica y de ventana (presets de D4)
 * → serie AVG por bucket (`/metrics/query`) → corridas de la sonda
 * (`/metrics/probes?limit=50`). Estados de carga/error/vacío explícitos y el
 * layout pasa a una columna por debajo de 720 px (QS-4).
 */

import { useState } from 'react';
import { EmptyState, ErrorState, LoadingState } from '../components/AsyncPanel';
import { ProbeTable } from '../components/ProbeTable';
import { SeriesChart, type SeriesPoint } from '../components/SeriesChart';
import { formatNumber } from '../format';
import { useApi } from '../hooks/useApi';
import { type ApiError, getMetrics, getMetricTypes, getProbes } from '../services/api';
import type { MetricAggregate, MetricTypeInfo, ProbeRun } from '../services/types';
import {
  buildWindow,
  WINDOW_PRESET_ORDER,
  WINDOW_PRESETS,
  type WindowPreset,
} from '../services/window';

/** Límite de corridas de la sonda que muestra la vista (QS-2). */
const PROBE_LIMIT = 50;

export interface LatencyViewProps {
  apiKey: string;
  /** 401/403: descarta la key y vuelve al gate (QS-1). */
  onUnauthorized?: (error: ApiError) => void;
}

export function LatencyView({ apiKey, onUnauthorized }: LatencyViewProps) {
  const catalog = useApi<MetricTypeInfo[]>(() => getMetricTypes(apiKey), [apiKey], {
    onUnauthorized,
  });
  const [selectedMetricId, setSelectedMetricId] = useState<number | null>(null);
  const [preset, setPreset] = useState<WindowPreset>('15m');

  const metricTypes = catalog.status === 'success' ? catalog.data : [];
  const selectedMetric =
    metricTypes.find((type) => type.metric_type_id === selectedMetricId) ??
    metricTypes.find((type) => type.name === 'TTFB') ??
    metricTypes[0] ??
    null;

  return (
    <section className="view">
      <h2>Latencias RUM</h2>
      <p className="view-help">
        Valor medio (AVG) por bucket de la ventana elegida, con las últimas corridas de la sonda
        HTTP.
      </p>

      {catalog.status === 'error' && (
        <ErrorState message={catalog.error.message} onRetry={catalog.reload} />
      )}
      {(catalog.status === 'idle' || catalog.status === 'loading') && (
        <LoadingState>Cargando el catálogo de métricas…</LoadingState>
      )}
      {catalog.status === 'success' && metricTypes.length === 0 && (
        <EmptyState>El catálogo no tiene métricas registradas.</EmptyState>
      )}

      {catalog.status === 'success' && metricTypes.length > 0 && (
        <>
          <div className="controls">
            <label htmlFor="metric-select">Métrica</label>
            <select
              id="metric-select"
              value={selectedMetric?.metric_type_id ?? ''}
              onChange={(event) => setSelectedMetricId(Number(event.target.value))}
            >
              {metricTypes.map((type) => (
                <option key={type.metric_type_id} value={type.metric_type_id}>
                  {type.name}
                </option>
              ))}
            </select>

            <label htmlFor="window-select">Ventana</label>
            <select
              id="window-select"
              value={preset}
              onChange={(event) => setPreset(event.target.value as WindowPreset)}
            >
              {WINDOW_PRESET_ORDER.map((key) => (
                <option key={key} value={key}>
                  {WINDOW_PRESETS[key].label}
                </option>
              ))}
            </select>
          </div>

          {selectedMetric === null ? (
            <LoadingState>Cargando el catálogo de métricas…</LoadingState>
          ) : (
            <LatencyDataPanel
              apiKey={apiKey}
              metricId={selectedMetric.metric_type_id}
              metricName={selectedMetric.name}
              preset={preset}
              onUnauthorized={onUnauthorized}
            />
          )}
        </>
      )}
    </section>
  );
}

interface LatencyData {
  series: SeriesPoint[];
  probes: ProbeRun[];
}

interface LatencyDataPanelProps {
  apiKey: string;
  metricId: number;
  metricName: string;
  preset: WindowPreset;
  onUnauthorized?: (error: ApiError) => void;
}

function LatencyDataPanel({
  apiKey,
  metricId,
  metricName,
  preset,
  onUnauthorized,
}: LatencyDataPanelProps) {
  const state = useApi<LatencyData>(
    async () => {
      const window = buildWindow(preset);
      const [aggregates, probes] = await Promise.all([
        getMetrics(
          {
            start: window.start,
            end: window.end,
            bucketSeconds: window.bucketSeconds,
            metricTypeId: metricId,
          },
          apiKey,
        ),
        getProbes(PROBE_LIMIT, apiKey),
      ]);
      return { series: toSeriesPoints(aggregates), probes: sortProbes(probes) };
    },
    [apiKey, metricId, preset],
    { onUnauthorized },
  );

  if (state.status === 'idle' || state.status === 'loading') {
    return <LoadingState>Cargando la ventana…</LoadingState>;
  }
  if (state.status === 'error') {
    return <ErrorState message={state.error.message} onRetry={state.reload} />;
  }

  return (
    <>
      {state.data.series.length === 0 ? (
        <EmptyState>Sin datos en la ventana</EmptyState>
      ) : (
        <SeriesSummary series={state.data.series} metricName={metricName} />
      )}
      <h3>Corridas de la sonda</h3>
      <ProbeTable runs={state.data.probes} />
    </>
  );
}

interface SeriesSummaryProps {
  series: SeriesPoint[];
  metricName: string;
}

/** Gráfico + resumen textual: buckets, máximo, promedio y sesiones. */
function SeriesSummary({ series, metricName }: SeriesSummaryProps) {
  const values = series.map((point) => point.value);
  const max = Math.max(...values);
  const average = values.reduce((total, value) => total + value, 0) / values.length;
  const sessions = series.reduce((total, point) => total + point.sessionCount, 0);

  return (
    <figure className="series">
      <SeriesChart points={series} label={metricName} />
      <figcaption className="summary">
        <span>{`${series.length} buckets`}</span>
        <span>{`máx ${formatNumber(max)}`}</span>
        <span>{`prom ${formatNumber(average)}`}</span>
        <span>{`${sessions} sesiones`}</span>
      </figcaption>
    </figure>
  );
}

/** `MetricAggregate` → punto de la serie, ordenado por `timestamp` ascendente. */
function toSeriesPoints(aggregates: MetricAggregate[]): SeriesPoint[] {
  return [...aggregates]
    .sort((left, right) => Date.parse(left.timestamp) - Date.parse(right.timestamp))
    .map((row) => ({
      timestamp: row.timestamp,
      value: row.value,
      sessionCount: row.session_count,
    }));
}

/** Corridas de la sonda: la más nueva primero, como las devuelve la API. */
function sortProbes(runs: ProbeRun[]): ProbeRun[] {
  return [...runs].sort((left, right) => Date.parse(right.timestamp) - Date.parse(left.timestamp));
}
