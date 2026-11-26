/**
 * Formateo de números y fechas para la UI (español, sin dependencias).
 *
 * Los valores llegan con escalas muy distintas (TTFB en ms, tasa de
 * excepciones en fracción), así que la cantidad de decimales se deriva de la
 * magnitud y no de una unidad fija.
 */

const clockFormatter = new Intl.DateTimeFormat('es-AR', {
  hour: '2-digit',
  minute: '2-digit',
});

const dateTimeFormatter = new Intl.DateTimeFormat('es-AR', {
  day: '2-digit',
  month: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
});

/** Valor numérico legible; `—` cuando no es un número finito. */
export function formatNumber(value: number): string {
  if (!Number.isFinite(value)) {
    return '—';
  }
  const magnitude = Math.abs(value);
  if (magnitude >= 100) {
    return value.toFixed(0);
  }
  if (magnitude >= 1) {
    return value.toFixed(2);
  }
  return value.toFixed(4);
}

/** Hora del bucket (`HH:MM`); cae al ISO crudo si no se puede parsear. */
export function formatClock(timestamp: string): string {
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? timestamp : clockFormatter.format(date);
}

/** Fecha y hora (`dd/mm HH:MM`); cae al ISO crudo si no se puede parsear. */
export function formatDateTime(timestamp: string): string {
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? timestamp : dateTimeFormatter.format(date);
}
