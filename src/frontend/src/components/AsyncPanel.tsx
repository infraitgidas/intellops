/**
 * Estados de espera de las vistas (QS-4): carga, error con reintento y vacío.
 *
 * Se centralizan para que ninguna vista muestre datos parciales como si
 * estuvieran completos ni duplique el botón "Reintentar".
 */

export interface LoadingStateProps {
  children: string;
}

/** Estado de carga: `role="status"` para que se anuncie a lectores de pantalla. */
export function LoadingState({ children }: LoadingStateProps) {
  return (
    <p className="notice notice-loading" role="status">
      {children}
    </p>
  );
}

export interface ErrorStateProps {
  /** Detalle devuelto por la API (nunca incluye la key). */
  message: string;
  onRetry: () => void;
  title?: string;
}

/** Error legible + botón de reintento (QS-4). */
export function ErrorState({
  message,
  onRetry,
  title = 'No se pudieron cargar los datos.',
}: ErrorStateProps) {
  return (
    <div className="notice notice-error">
      <p className="notice-title">{title}</p>
      <p className="notice-detail">{message}</p>
      <button type="button" onClick={onRetry}>
        Reintentar
      </button>
    </div>
  );
}

export interface EmptyStateProps {
  children: string;
}

/** Estado vacío explícito: nunca un gráfico en blanco (QS-2). */
export function EmptyState({ children }: EmptyStateProps) {
  return <p className="notice notice-empty">{children}</p>;
}
