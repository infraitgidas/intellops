"""Errores de dominio tipificados (ADR-09).

Cada subtipo fija su HTTP status y un código de error estable para el
contrato ErrorResponse {error: {code, message}}.
"""


class DomainError(Exception):
    """Error base de dominio con código estable para el contrato de error.

    `headers` opcional (p. ej. `WWW-Authenticate` para 401) lo propaga el
    handler de main.py a la respuesta HTTP (design §4, IAUTH-1).
    """

    http_code: int = 500
    default_code: str = "domain_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.headers = headers


class AuthenticationError(DomainError):
    """401 — credenciales inválidas (anti-enumeración, SEC-1)."""

    http_code = 401
    default_code = "invalid_credentials"


class AuthorizationError(DomainError):
    """403 — usuario autenticado sin permiso o inactivo (SEC-2, ADR-15)."""

    http_code = 403
    default_code = "forbidden"


class NotFoundError(DomainError):
    """404 — recurso inexistente."""

    http_code = 404
    default_code = "not_found"


class ConflictError(DomainError):
    """409 — violación de unicidad o FK RESTRICT (SEC-3)."""

    http_code = 409
    default_code = "conflict"
