/**
 * Hook de la API key del operador (ISS-B-05 D2).
 *
 * La key vive SÓLO en `sessionStorage` bajo una única clave: muere al cerrar la
 * pestaña, nunca va a `localStorage`, a la URL ni al bundle. Un 401/403 de la
 * API se traduce en `ApiError` con `isAuthError` y el consumidor llama a
 * `clearKey()`, que descarta la key y devuelve al gate (QS-1).
 */

import { useCallback, useState } from 'react';

/** Única clave de `sessionStorage` para la API key. */
export const SESSION_KEY_STORAGE = 'intellops.api_key';

export function readSessionKey(): string | null {
  try {
    const value = window.sessionStorage.getItem(SESSION_KEY_STORAGE);
    return value !== null && value.length > 0 ? value : null;
  } catch {
    return null;
  }
}

export function writeSessionKey(apiKey: string): void {
  try {
    window.sessionStorage.setItem(SESSION_KEY_STORAGE, apiKey);
  } catch {
    // sessionStorage puede estar bloqueado (modo privado): se sigue en memoria.
  }
}

export function clearSessionKey(): void {
  try {
    window.sessionStorage.removeItem(SESSION_KEY_STORAGE);
  } catch {
    // Sin storage no hay nada que borrar.
  }
}

export interface SessionKeyState {
  apiKey: string | null;
  saveKey: (apiKey: string) => void;
  clearKey: () => void;
}

/** Estado de la key de la sesión actual (lee `sessionStorage` al montar). */
export function useSessionKey(): SessionKeyState {
  const [apiKey, setApiKey] = useState<string | null>(() => readSessionKey());

  const saveKey = useCallback((next: string) => {
    const trimmed = next.trim();
    if (trimmed.length === 0) {
      return;
    }
    writeSessionKey(trimmed);
    setApiKey(trimmed);
  }, []);

  const clearKey = useCallback(() => {
    clearSessionKey();
    setApiKey(null);
  }, []);

  return { apiKey, saveKey, clearKey };
}
