/**
 * Vista de heatmap UX — placeholder de la fase 3.
 *
 * El heatmap (tiempo × métrica, normalizado por fila) se implementa en la fase
 * 4 de ISS-B-05; esta vista sólo reserva la navegación y el contrato de props
 * para que `App` no cambie cuando llegue la implementación.
 */

import type { ApiError } from '../services/api';

export interface HeatmapViewProps {
  apiKey: string;
  onUnauthorized?: (error: ApiError) => void;
}

export function HeatmapView(_props: HeatmapViewProps) {
  return (
    <section className="view">
      <h2>Heatmap UX</h2>
      <p className="notice notice-empty">Heatmap de métricas por bucket: próximamente.</p>
    </section>
  );
}
