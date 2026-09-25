"""Handlers HTTP — contrato ErrorResponse (ADR-09) y 422→400 scoped (D5).

Extraído de main.py para que cualquier app FastAPI (producción y apps de
test como /_probe) traduzca DomainError al mismo contrato. Propaga
`exc.headers` (p. ej. WWW-Authenticate en 401 de API key, IAUTH-1).
`validation_error_handler` traduce los 422 de validación Pydantic a 400
`schema_validation_error` SOLO en paths /telemetry/* (D5): el resto de los
paths conserva el 422 del contrato vigente (p. ej. /applications).
"""

from fastapi import Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
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


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """422→400 `schema_validation_error` SOLO en /telemetry/* (RUM-2, DD-5).

    El envelope de ingesta falla la validación Pydantic (schema_version,
    1..500 events, estructura) y el contrato OAS-11 exige 400 en esos paths;
    el resto de la API conserva el 422 estándar.
    """
    if request.url.path.startswith("/telemetry/"):
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="schema_validation_error",
                    message="invalid ingest envelope",
                )
            ).model_dump(),
        )
    return await request_validation_exception_handler(request, exc)
