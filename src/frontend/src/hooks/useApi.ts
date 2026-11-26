/**
 * Estado de una consulta a la API (ISS-B-05 D4).
 *
 * Unión discriminada `idle | loading | error | success` + `reload()`: las
 * vistas no manejan `try/catch` ni renderizan datos viejos como si fueran
 * nuevos (al cambiar deps el estado vuelve a `loading` y una respuesta vieja
 * nunca pisa a la request vigente).
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { type ApiError, isAuthError, toApiError } from '../services/api';

interface ApiStateBase {
  reload: () => void;
}

export type ApiState<T> =
  | (ApiStateBase & { status: 'idle' })
  | (ApiStateBase & { status: 'loading' })
  | (ApiStateBase & { status: 'error'; error: ApiError })
  | (ApiStateBase & { status: 'success'; data: T });

export interface UseApiOptions {
  /** Se invoca ante 401/403 para descartar la key y volver al gate (QS-1). */
  onUnauthorized?: (error: ApiError) => void;
}

type InternalState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; error: ApiError }
  | { status: 'success'; data: T };

/**
 * Ejecuta `load()` cuando cambian `deps` (o ante `reload()`).
 *
 * `deps` debe tener tamaño constante entre renders: es la lista de
 * dependencias real del request, igual que en un `useEffect`.
 */
export function useApi<T>(
  load: () => Promise<T>,
  deps: readonly unknown[],
  options: UseApiOptions = {},
): ApiState<T> {
  const [state, setState] = useState<InternalState<T>>({ status: 'idle' });
  const [attempt, setAttempt] = useState(0);

  const unauthorizedHandler = useRef(options.onUnauthorized);
  useEffect(() => {
    unauthorizedHandler.current = options.onUnauthorized;
  }, [options.onUnauthorized]);

  const reload = useCallback(() => {
    setAttempt((current) => current + 1);
  }, []);

  useEffect(() => {
    let active = true;
    setState({ status: 'loading' });

    load().then(
      (data) => {
        if (active) {
          setState({ status: 'success', data });
        }
      },
      (error: unknown) => {
        if (!active) {
          return;
        }
        const apiError = toApiError(error);
        if (isAuthError(apiError)) {
          unauthorizedHandler.current?.(apiError);
        }
        setState({ status: 'error', error: apiError });
      },
    );

    return () => {
      active = false;
    };
    // `load` se recrea en cada render; el disparo lo definen `deps` + `attempt`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, attempt]);

  if (state.status === 'success') {
    return { status: 'success', data: state.data, reload };
  }
  if (state.status === 'error') {
    return { status: 'error', error: state.error, reload };
  }
  if (state.status === 'loading') {
    return { status: 'loading', reload };
  }
  return { status: 'idle', reload };
}
