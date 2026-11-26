/**
 * Shell de la SPA (QS-1): gate de API key por delante de las dos vistas.
 *
 * Sin key en `sessionStorage` no se monta ninguna vista, así que no hay ninguna
 * llamada a `/metrics/*` antes de que el operador pegue la key. Un 401/403 que
 * reporta `useApi` descarta la key y devuelve al gate con el mensaje de la API.
 */

import { useCallback, useState } from 'react';
import { KeyGate } from './components/KeyGate';
import { useSessionKey } from './hooks/useSessionKey';
import type { ApiError } from './services/api';
import { HeatmapView } from './views/HeatmapView';
import { LatencyView } from './views/LatencyView';

type TabId = 'latency' | 'heatmap';

const TABS: ReadonlyArray<{ id: TabId; label: string }> = [
  { id: 'latency', label: 'Latencias' },
  { id: 'heatmap', label: 'Heatmap UX' },
];

export function App() {
  const { apiKey, saveKey, clearKey } = useSessionKey();
  const [authError, setAuthError] = useState<ApiError | null>(null);
  const [tab, setTab] = useState<TabId>('latency');

  const handleUnauthorized = useCallback(
    (error: ApiError) => {
      clearKey();
      setAuthError(error);
    },
    [clearKey],
  );

  const handleConnect = useCallback(
    (key: string) => {
      setAuthError(null);
      saveKey(key);
    },
    [saveKey],
  );

  if (apiKey === null) {
    return <KeyGate onSubmit={handleConnect} error={authError} />;
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>IntellOps</h1>
        <p className="view-help">Observabilidad de la experiencia: latencias RUM y heatmap UX.</p>
        <button type="button" className="secondary" onClick={clearKey}>
          Desconectar
        </button>
      </header>

      <nav className="tabs" aria-label="Vistas">
        {TABS.map((entry) => (
          <button
            key={entry.id}
            type="button"
            aria-pressed={tab === entry.id}
            onClick={() => setTab(entry.id)}
          >
            {entry.label}
          </button>
        ))}
      </nav>

      <main className="app-main">
        {tab === 'latency' ? (
          <LatencyView apiKey={apiKey} onUnauthorized={handleUnauthorized} />
        ) : (
          <HeatmapView apiKey={apiKey} onUnauthorized={handleUnauthorized} />
        )}
      </main>
    </div>
  );
}
