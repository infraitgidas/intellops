"""Utilidades dormidas de API keys (ADR-03, SEC-5).

Generación y hashing listos para S2-02; sin wiring en endpoints durante
S2-01 (schema en 0002, uso posterior).
"""

import base64
import hashlib
import secrets

DEFAULT_KEY_PREFIX = "ilp_"


def generate_api_key(prefix: str = DEFAULT_KEY_PREFIX) -> str:
    """Genera una API key: prefijo + 43 chars base64url (32 bytes)."""
    raw = secrets.token_bytes(32)
    encoded = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    return f"{prefix}{encoded}"


def hash_api_key(api_key: str) -> str:
    """Hash SHA-256 hex (64 chars) de la key — lo que se persiste."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()
