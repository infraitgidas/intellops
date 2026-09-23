"""Handler HTTP de DomainError — contrato ErrorResponse (ADR-09).

Extraído de main.py para que cualquier app FastAPI (producción y apps de
test como /_probe) traduzca DomainError al mismo contrato. Propaga
`exc.headers` (p. ej. WWW-Authenticate en 401 de API key, IAUTH-1).
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from api.domain.exceptions import DomainError
from api.presentation.schemas.common import ErrorDetail, ErrorResponse


async def domain_error_handler(
    request: Request,  # pylint: disable=unused-argument  # firma exigida por FastAPI
    exc: DomainError,
) -> JSONResponse:
    """Traduce DomainError tipificadas al contrato ErrorResponse (ADR-09)."""
    return JSONResponse(
        status_code=exc.http_code,
        content=ErrorResponse(
            error=ErrorDetail(code=exc.code, message=exc.message)
        ).model_dump(),
        headers=exc.headers,
    )
