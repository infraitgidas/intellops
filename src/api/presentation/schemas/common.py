"""Schemas compartidos — contrato ErrorResponse (ADR-09) y email de laboratorio.

`LabEmail`: el seed de la migración 0002 y las fixtures usan dominios
special-use/reserved (RFC 6761) como `.local` (`admin@intellops.local`), que
email-validator 2.3.0 rechaza de forma incondicional. Este campo valida con
email-validator y, si el rechazo es por dominio reserved, exige estructura
mínima estricta antes de aceptar (dev/CI; ver deviation ADR-12 en apply).
"""

import re
from typing import Annotated

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BaseModel

# Estructura mínima (RFC 5322 local-part + DNS labels) exigida cuando
# email-validator rechaza por dominio special-use/reserved (p. ej. .local).
_LOCAL_PART_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}$")
_DOMAIN_RE = re.compile(
    r"^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$"
)


def _validate_email(value: str) -> str:
    """Valida el email; acepta dominios reserved solo si la estructura es válida."""
    try:
        result = validate_email(value, check_deliverability=False)
        return result.normalized
    except EmailNotValidError:
        local, sep, domain = value.rpartition("@")
        if not sep or not _LOCAL_PART_RE.fullmatch(local) or not _DOMAIN_RE.fullmatch(
            domain
        ):
            raise
        return value


LabEmail = Annotated[str, AfterValidator(_validate_email)]


class ErrorDetail(BaseModel):
    """Detalle de un error de dominio: código estable + mensaje legible."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Envoltorio único de errores de dominio (401/403/404/409)."""

    error: ErrorDetail
