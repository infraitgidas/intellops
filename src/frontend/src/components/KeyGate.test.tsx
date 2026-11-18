import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { KeyGate } from './KeyGate';
import { App } from '../App';
import { SESSION_KEY_STORAGE } from '../hooks/useSessionKey';
import { jsonResponse, stubApi } from '../test/stubApi';

const AUTH_ERROR_BODY = {
  error: { code: 'invalid_api_key', message: 'invalid or unknown API key' },
};

describe('KeyGate (QS-1)', () => {
  it('pide la key en un campo enmascarado y la entrega al conectar', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<KeyGate onSubmit={onSubmit} />);

    const input = screen.getByLabelText(/api key/i);
    expect(input).toHaveAttribute('type', 'password');

    await user.type(input, 'ilp_secreta_de_prueba');
    expect(screen.queryByText(/ilp_secreta_de_prueba/)).toBeNull();

    await user.click(screen.getByRole('button', { name: /conectar/i }));
    expect(onSubmit).toHaveBeenCalledWith('ilp_secreta_de_prueba');
  });

  it('no entrega una key vacía', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<KeyGate onSubmit={onSubmit} />);

    await user.click(screen.getByRole('button', { name: /conectar/i }));
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('muestra el mensaje del error de autenticación', () => {
    render(
      <KeyGate
        onSubmit={vi.fn()}
        error={{ code: 'invalid_api_key', message: 'invalid or unknown API key' }}
      />,
    );

    expect(screen.getByRole('alert')).toHaveTextContent('invalid_api_key');
  });
});

describe('gate de key en App (QS-1)', () => {
  it('sin key guardada no consulta /metrics/*', () => {
    window.sessionStorage.clear();
    const fetchMock = stubApi({});

    render(<App />);

    expect(screen.getByLabelText(/api key/i)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('un 401 descarta la key guardada y vuelve al gate con el mensaje', async () => {
    window.sessionStorage.setItem(SESSION_KEY_STORAGE, 'ilp_vencida');
    const fetchMock = stubApi({
      types: () => jsonResponse(AUTH_ERROR_BODY, 401),
      metrics: () => jsonResponse(AUTH_ERROR_BODY, 401),
      probes: () => jsonResponse(AUTH_ERROR_BODY, 401),
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('invalid_api_key');
    });
    expect(window.sessionStorage.getItem(SESSION_KEY_STORAGE)).toBeNull();
    expect(screen.getByLabelText(/api key/i)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalled();
  });

  it('con una key válida guarda la key y deja de mostrar el gate', async () => {
    window.sessionStorage.clear();
    const user = userEvent.setup();
    stubApi({
      types: () => jsonResponse([{ metric_type_id: 1, name: 'TTFB', description: null }]),
      metrics: () => jsonResponse([]),
      probes: () => jsonResponse([]),
    });

    render(<App />);
    await user.type(screen.getByLabelText(/api key/i), 'ilp_buena');
    await user.click(screen.getByRole('button', { name: /conectar/i }));

    expect(window.sessionStorage.getItem(SESSION_KEY_STORAGE)).toBe('ilp_buena');
    expect(screen.queryByLabelText(/api key/i)).toBeNull();
    expect(screen.getByRole('heading', { name: /latencias rum/i })).toBeInTheDocument();
  });
});
