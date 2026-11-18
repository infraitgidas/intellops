import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useApi } from './useApi';
import { ApiError } from '../services/api';

describe('useApi (D4)', () => {
  it('pasa por loading y llega a success', async () => {
    const load = vi.fn<() => Promise<{ total: number }>>(() =>
      Promise.resolve({ total: 7 }),
    );

    const { result } = renderHook(() => useApi(load, []));

    expect(result.current.status).toBe('loading');
    await waitFor(() => {
      expect(result.current.status).toBe('success');
    });
    expect(result.current.status === 'success' ? result.current.data : null).toEqual({ total: 7 });
    expect(load).toHaveBeenCalledTimes(1);
  });

  it('expone el ApiError tipado en status error', async () => {
    const failure = new ApiError({ status: 500, code: 'http_500', message: 'la API falló' });
    const load = vi.fn<() => Promise<never>>(() => Promise.reject(failure));

    const { result } = renderHook(() => useApi(load, []));

    await waitFor(() => {
      expect(result.current.status).toBe('error');
    });
    expect(result.current.status === 'error' ? result.current.error.code : null).toBe('http_500');
    expect(result.current.status === 'error' ? result.current.error.message : null).toBe(
      'la API falló',
    );
  });

  it('reload vuelve a pedir y termina en success', async () => {
    const load = vi
      .fn<() => Promise<{ total: number }>>()
      .mockRejectedValueOnce(new ApiError({ status: 503, code: 'http_503', message: 'caída' }))
      .mockResolvedValueOnce({ total: 3 });

    const { result } = renderHook(() => useApi(load, []));
    await waitFor(() => {
      expect(result.current.status).toBe('error');
    });

    act(() => {
      result.current.reload();
    });

    await waitFor(() => {
      expect(result.current.status).toBe('success');
    });
    expect(load).toHaveBeenCalledTimes(2);
    expect(result.current.status === 'success' ? result.current.data : null).toEqual({ total: 3 });
  });

  it('un cambio de dependencias vuelve a loading y no muestra los datos viejos', async () => {
    let resolveFirst: ((value: string) => void) | undefined;
    const load = vi
      .fn<() => Promise<string>>()
      .mockImplementationOnce(
        () =>
          new Promise<string>((resolve) => {
            resolveFirst = resolve;
          }),
      )
      .mockResolvedValueOnce('nuevo');

    const { result, rerender } = renderHook(
      ({ metricId }: { metricId: number }) => useApi(() => load(), [metricId]),
      { initialProps: { metricId: 1 } },
    );

    act(() => {
      resolveFirst?.('viejo');
    });
    await waitFor(() => {
      expect(result.current.status).toBe('success');
    });
    expect(result.current.status === 'success' ? result.current.data : null).toBe('viejo');

    rerender({ metricId: 2 });

    expect(result.current.status).toBe('loading');
    await waitFor(() => {
      expect(result.current.status).toBe('success');
    });
    expect(result.current.status === 'success' ? result.current.data : null).toBe('nuevo');
  });

  it('una respuesta vieja no pisa a la request vigente', async () => {
    let resolveFirst: ((value: string) => void) | undefined;
    const load = vi
      .fn<() => Promise<string>>()
      .mockImplementationOnce(
        () =>
          new Promise<string>((resolve) => {
            resolveFirst = resolve;
          }),
      )
      .mockResolvedValueOnce('nuevo');

    const { result, rerender } = renderHook(
      ({ metricId }: { metricId: number }) => useApi(() => load(), [metricId]),
      { initialProps: { metricId: 1 } },
    );

    rerender({ metricId: 2 });
    await waitFor(() => {
      expect(result.current.status).toBe('success');
    });

    act(() => {
      resolveFirst?.('viejo');
    });

    expect(result.current.status === 'success' ? result.current.data : null).toBe('nuevo');
  });

  it('un 401 avisa al callback de autenticación', async () => {
    const onUnauthorized = vi.fn();
    const failure = new ApiError({
      status: 401,
      code: 'invalid_api_key',
      message: 'invalid or unknown API key',
    });
    const load = vi.fn<() => Promise<never>>(() => Promise.reject(failure));

    const { result } = renderHook(() => useApi(load, [], { onUnauthorized }));

    await waitFor(() => {
      expect(result.current.status).toBe('error');
    });
    expect(onUnauthorized).toHaveBeenCalledWith(failure);
  });

  it('no avisa al callback de autenticación ante un 500', async () => {
    const onUnauthorized = vi.fn();
    const load = vi
      .fn<() => Promise<never>>()
      .mockRejectedValue(new ApiError({ status: 500, code: 'http_500', message: 'boom' }));

    const { result } = renderHook(() => useApi(load, [], { onUnauthorized }));

    await waitFor(() => {
      expect(result.current.status).toBe('error');
    });
    expect(onUnauthorized).not.toHaveBeenCalled();
  });
});
