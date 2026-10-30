// Constantes del contrato del agente RUM v0.1
// (docs/architecture/ContratoAgenteRUM.md, tarea A.3).

export const AGENT_VERSION = "1.0.0";

// §3: el envelope solo acepta "1.0"; un valor distinto produce 400 del batch.
export const SCHEMA_VERSION = "1.0";

// §2.3 — catálogo canónico de error_type (src/api/domain/services/ingest_policy.py).
export const ERROR_TYPES = [
  "Error",
  "EvalError",
  "RangeError",
  "ReferenceError",
  "SyntaxError",
  "TypeError",
  "URIError",
  "AggregateError",
  "InternalError",
  "UnhandledRejection",
  "Other",
];

// §5 — muestreo determinista por sesión.
export const DEFAULT_SAMPLE_RATE = 1.0;
export const MAX_EXCEPTIONS_PER_SESSION = 20;
export const EXCEPTION_DEDUP_WINDOW_MS = 60_000;

// §2.1 — rotación de sesión.
export const SESSION_IDLE_TIMEOUT_MS = 30 * 60_000;
export const SESSION_MAX_LIFETIME_MS = 24 * 60 * 60_000;

// §6 — batching.
export const FLUSH_METRICS_COUNT = 20;
export const FLUSH_EXCEPTIONS_COUNT = 5;
export const FLUSH_METRICS_INTERVAL_MS = 10_000;
export const FLUSH_EXCEPTIONS_INTERVAL_MS = 5_000;
export const MAX_EVENTS_PER_REQUEST = 400;
export const MAX_BYTES_PER_REQUEST = 32 * 1024;
export const MAX_QUEUED_EVENTS = 500;
export const MAX_METRICS_PER_EVENT = 50;

// §2.3 — límites del servidor que el agente trunca antes de enviar.
export const MAX_MESSAGE_LEN = 2000;
export const MAX_STACK_TRACE_LEN = 20_000;
export const MAX_ERROR_TYPE_LEN = 100;
export const MAX_USER_AGENT_LEN = 256;
export const MAX_PAGE_URL_LEN = 2048;

// §7 — reintentos y backoff.
// El contrato menciona "máximo 3 intentos" y una secuencia de backoff 1 s, 2 s
// y 4 s (§7), que no pueden darse juntas: 3 intentos usan 2 esperas. Se
// implementan 3 intentos con 1 s y 2 s, que es lo que verifica el checklist de
// QA (§12: "simular 503 y verificar 3 intentos con backoff").
export const MAX_ATTEMPTS = 3;
export const BACKOFF_MS = [1_000, 2_000];
export const BACKOFF_JITTER = 0.2;

// §7 — estados del circuito y del ciclo de vida.
export const NO_RETRY_STATUSES = [400, 401, 403, 429];
export const STOP_STATUSES = [401, 403];
