/**
 * Tabla de corridas de la sonda HTTP (QS-2, B.13).
 *
 * Muestra una fila por ejecución con `available`, `http_status`, `latency_ms` y
 * `outcome`; los campos que la sonda no pudo leer llegan `null` y se muestran
 * como `—`. El contenedor scrollea horizontalmente en pantallas angostas
 * (QS-4) sin romper el ancho de la página.
 */

import { formatDateTime, formatNumber } from '../format';
import type { ProbeRun } from '../services/types';

export interface ProbeTableProps {
  runs: ProbeRun[];
}

export function ProbeTable({ runs }: ProbeTableProps) {
  if (runs.length === 0) {
    return <p className="notice notice-empty">Sin corridas de la sonda en el período.</p>;
  }

  return (
    <div className="table-scroll">
      <table className="probe-table">
        <caption>{`Últimas ${runs.length} corridas de la sonda HTTP`}</caption>
        <thead>
          <tr>
            <th scope="col">Hora</th>
            <th scope="col">Destino</th>
            <th scope="col">HTTP</th>
            <th scope="col">Resultado</th>
            <th scope="col">Latencia (ms)</th>
            <th scope="col">Disponible</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={`${run.timestamp}-${run.target ?? 'sin-destino'}-${run.outcome ?? 'sin-resultado'}`}>
              <td>{formatDateTime(run.timestamp)}</td>
              <td>{run.target ?? '—'}</td>
              <td>{run.http_status ?? '—'}</td>
              <td>{run.outcome ?? '—'}</td>
              <td>{run.latency_ms === null ? '—' : formatNumber(run.latency_ms)}</td>
              <td>{run.available ? 'Sí' : 'No'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
