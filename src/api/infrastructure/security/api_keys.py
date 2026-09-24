"""API keys de ingesta — generación, hashing y redacción (SEC-5, IAUTH-4).

`generate_api_key` usa CSPRNG (secrets, 32 bytes ≥ 256 bits de entropía) y
devuelve `ilp_` + 43 chars base64url (SEC-8). `hash_api_key` persiste SOLO
el SHA-256 hex (64 chars); el plaintext nunca se persiste (CRED-1, SEC-7).
`redact_api_key` / `ApiKeyRedactionFilter` evitan que el plaintext aparezca
en logs, tracebacks y métricas (IAUTH-4, ADR-23).
"""

import base64
import hashlib
import logging
import re
import secrets
import traceback

DEFAULT_KEY_PREFIX = "ilp_"

# Prefijo + 43 chars base64url (generación de 32 bytes sin padding).
_API_KEY_RE = re.compile(r"\bilp_[A-Za-z0-9_-]{43}\b")
REDACTED_MARKER = "ilp_***REDACTED***"


def generate_api_key(prefix: str = DEFAULT_KEY_PREFIX) -> str:
    """Genera una API key: prefijo + 43 chars base64url (32 bytes)."""
    raw = secrets.token_bytes(32)
    encoded = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    return f"{prefix}{encoded}"


def hash_api_key(api_key: str) -> str:
    """Hash SHA-256 hex (64 chars) de la key — lo que se persiste."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def redact_api_key(text: str) -> str:
    """Reemplaza cualquier valor de API key (`ilp_<43 chars>`) por un
    marcador; deja el resto del texto intacto (IAUTH-4, ADR-23)."""
    return _API_KEY_RE.sub(REDACTED_MARKER, text)


class ApiKeyRedactionFilter(logging.Filter):
    """Filtro global de logs: redacta API keys en mensaje, args y tracebacks.

    Instalado en main.py sobre el root logger (ADR-23). `filter` muta el
    LogRecord ANTES del formateo del handler: si hay exc_info, lo formatea
    y redacta aquí (el Formatter ya no re-formatea porque exc_info=None).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info:
            exc_text = "".join(traceback.format_exception(*record.exc_info))
            record.exc_text = redact_api_key(exc_text)
            record.exc_info = None
        record.msg = redact_api_key(str(record.msg))
        if record.args:
            record.args = tuple(
                redact_api_key(arg) if isinstance(arg, str) else arg
                for arg in record.args
            )
        if hasattr(record, "message"):
            record.message = redact_api_key(record.message)
        return True
