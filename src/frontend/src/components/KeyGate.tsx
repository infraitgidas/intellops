/**
 * Gate de la API key (QS-1, D2).
 *
 * El operador pega la key (`ilp_…`) y se guarda en `sessionStorage`. El campo
 * es de tipo `password` y la key no se refleja en ningún otro lugar de la UI.
 */

import { type FormEvent, useId, useState } from 'react';

export interface KeyGateError {
  code: string;
  message: string;
}

export interface KeyGateProps {
  onSubmit: (apiKey: string) => void;
  /** Error de la API que devolvió al operador al gate (p. ej. 401). */
  error?: KeyGateError | null;
}

export function KeyGate({ onSubmit, error = null }: KeyGateProps) {
  const [value, setValue] = useState('');
  const inputId = useId();
  const hintId = useId();

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = value.trim();
    if (trimmed.length === 0) {
      return;
    }
    onSubmit(trimmed);
  };

  return (
    <main className="gate">
      <h1>IntellOps — panel de operación</h1>
      <p id={hintId} className="gate-hint">
        Pegá la API key de la aplicación (<code>ilp_…</code>). Se guarda sólo en esta pestaña
        (<code>sessionStorage</code>) y se descarta cuando la API la rechaza.
      </p>
      <form className="gate-form" onSubmit={handleSubmit}>
        <label htmlFor={inputId}>API key</label>
        <input
          id={inputId}
          type="password"
          name="apiKey"
          autoComplete="off"
          spellCheck={false}
          aria-describedby={hintId}
          value={value}
          onChange={(event) => setValue(event.target.value)}
        />
        <button type="submit">Conectar</button>
      </form>
      {error !== null && (
        <p className="notice notice-error" role="alert">
          {error.code}: {error.message}
        </p>
      )}
    </main>
  );
}
