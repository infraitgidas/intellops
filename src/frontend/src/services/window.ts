/**
 * Presets de ventana de la vista de latencias (ISS-B-05 D4).
 *
 * La tabla es normativa: el `bucket_seconds` siempre es ≥ 60 y la ventana ≤ 7
 * días, que es lo que valida `QueryService` en el backend.
 */

export type WindowPreset = '15m' | '1h' | '6h' | '24h';

export interface WindowPresetSpec {
  /** Etiqueta en la UI (español). */
  readonly label: string;
  /** Ventana en segundos. */
  readonly seconds: number;
  /** Tamaño de bucket en segundos. */
  readonly bucketSeconds: number;
}

export const WINDOW_PRESETS: Record<WindowPreset, WindowPresetSpec> = {
  '15m': { label: '15 min', seconds: 900, bucketSeconds: 60 },
  '1h': { label: '1 h', seconds: 3_600, bucketSeconds: 60 },
  '6h': { label: '6 h', seconds: 21_600, bucketSeconds: 300 },
  '24h': { label: '24 h', seconds: 86_400, bucketSeconds: 900 },
};

export const WINDOW_PRESET_ORDER: readonly WindowPreset[] = ['15m', '1h', '6h', '24h'];

export interface MetricsWindow {
  /** Inicio de la ventana, ISO 8601 UTC. */
  start: string;
  /** Fin de la ventana, ISO 8601 UTC. */
  end: string;
  bucketSeconds: number;
}

/**
 * Ventana concreta para un preset, anclada a `now`.
 *
 * Se calcula dentro del cargador de datos (no en el render) para que cada
 * request use el "ahora" real y no una ventana congelada.
 */
export function buildWindow(preset: WindowPreset, now: Date = new Date()): MetricsWindow {
  const spec = WINDOW_PRESETS[preset];
  return {
    start: new Date(now.getTime() - spec.seconds * 1000).toISOString(),
    end: now.toISOString(),
    bucketSeconds: spec.bucketSeconds,
  };
}
