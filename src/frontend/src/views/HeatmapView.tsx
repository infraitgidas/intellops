/**
 * Vista de heatmap UX (QS-3, ISS-B-05 D3).
 *
 * UNA sola llamada a `/metrics/query` sin `metric_type` (todas las métricas en
 * una request) más `/metrics/list` para los nombres, con la ventana elegida
 * (presets de D4). El pivote y la normalización por fila viven en
 * `HeatmapGrid`. Estados de carga/error/vacío explícitos y el layout pasa a una
 * columna por debajo de 720 px (QS-4).
 */

import { useState } from 'react';
import { EmptyState, ErrorState, LoadingState } from '../components/AsyncPanel';
import { buildHeatmap, HeatmapGrid, type HeatmapModel } from '../components/HeatmapGrid';
import { useApi } from '../hooks/useApi';
import { type ApiError, getMetrics, getMetricTypes } from '../services/api';
import {
  buildWindow,
  WINDOW_PRESET_ORDER,
  WINDOW_PRESETS,
  type WindowPreset,
} from '../services/window';

export interface HeatmapViewProps {
  apiKey: string;
  /** 401/403: descarta la key y vuelve al gate (QS-1). */
  onUnauthorized?: (error: ApiError) => void;
}

interface HeatmapData {
  model: HeatmapModel;
}

export function HeatmapView({ apiKey, onUnauthorized }: HeatmapViewProps) {
  const [preset, setPreset] = useState<WindowPreset>('1h');

  const state = useApi<HeatmapData>(
    async () => {
      const window = buildWindow(preset);
      const [aggregates, catalog] = await Promise.all([
        getMetrics(
          {
            start: window.start,
            end: window.end,
            bucketSeconds: window.bucketSeconds,
          },
          apiKey,
        ),
        getMetricTypes(apiKey),
      ]);
      return { model: buildHeatmap(aggregates, catalog) };
    },
    [apiKey, preset],
    { onUnauthorized },
  );

  return (
    <section className="view">
      <h2>Heatmap UX</h2>
      <p className="view-help">
        Cada fila es una métrica y cada columna un bucket de tiempo: el color es el valor medio
        (AVG) del bucket normalizado contra el mínimo y el máximo de su propia fila, así que
        métricas con escalas distintas se leen sin saturarse entre sí. Una celda gris es un bucket
        sin datos para esa métrica, nunca un valor interpolado.
      </p>

      <div className="controls">
        <label htmlFor="heatmap-window">Ventana</label>
        <select
          id="heatmap-window"
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

      {(state.status === 'idle' || state.status === 'loading') && (
        <LoadingState>Cargando el heatmap…</LoadingState>
      )}
      {state.status === 'error' && (
        <ErrorState message={state.error.message} onRetry={state.reload} />
      )}
      {state.status === 'success' &&
        (state.data.model.rows.length === 0 ? (
          <EmptyState>Sin datos en la ventana</EmptyState>
        ) : (
          <HeatmapGrid model={state.data.model} />
        ))}
    </section>
  );
}
