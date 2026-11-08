"""Unit: guards de autenticación y autorización y handlers de error
(ISS-S3-06, #45).

`get_current_user`, `require_role` y `require_api_key` deciden quién entra a
la API. Hasta ahora solo los ejercitaban los tests de integración por HTTP;
este módulo los llama directamente, con los repositorios SQLAlchemy
reemplazados por dobles en memoria (monkeypatch), así que corren sin
Postgres:

- AUTH-5: sin bearer, token inválido/expirado/mal formado o usuario
  inexistente → 401 `invalid_token`; usuario inactivo → 403 (ADR-15).
- ADR-04: `require_role` deja pasar solo los roles indicados.
- IAUTH-1..3 / ADR-22: X-API-Key ausente, inválida o revocada → el MISMO 401
  con `WWW-Authenticate: ApiKey`; app inactiva → 403 `app_inactive`.
- ADR-09 / D5: el contrato ErrorResponse y el 422→400 solo en /telemetry/*.
"""

import json
from uuid import uuid4

import jwt as pyjwt
import pytest
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from api.config import get_settings
from api.domain.entities.application import Application
from api.domain.entities.lab_user import LabUser
from api.domain.entities.user_role import UserRole
from api.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
)
from api.infrastructure.security.api_keys import hash_api_key
from api.infrastructure.security.jwt import DEFAULT_ISSUER, create_access_token
from api.presentation import dependencies
from api.presentation.errors import domain_error_handler, validation_error_handler

VALID_KEY = "ilp_" + "k" * 43


def _user(*, is_active=True, role="Admin") -> LabUser:
    user = LabUser(
        user_id=uuid4(),
        name="Ana",
        email="ana@intellops.local",
        role_id=1,
        is_active=is_active,
    )
    user.role = UserRole(role_id=1, name=role)
    return user


def _bearer(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _token(user_id, **overrides) -> str:
    settings = get_settings()
    kwargs = {"secret": settings.jwt_secret, "expire_minutes": 30}
    kwargs.update(overrides)
    return create_access_token(user_id, "Admin", **kwargs)


@pytest.fixture
def users(monkeypatch):
    """Reemplaza el repo SQLAlchemy de usuarios por un dict en memoria."""
    store: dict = {}

    class _Repo:
        def __init__(self, _session) -> None:
            pass

        async def get_by_id(self, user_id):
            return store.get(user_id)

    monkeypatch.setattr(dependencies, "SQLAlchemyUserRepository", _Repo)
    return store


@pytest.fixture
def applications(monkeypatch):
    """Reemplaza el repo SQLAlchemy de aplicaciones por una lista en memoria."""
    store: list[Application] = []

    class _Repo:
        def __init__(self, _session) -> None:
            pass

        async def get_by_api_token_hash(self, api_token_hash):
            return next((a for a in store if a.api_token_hash == api_token_hash), None)

    monkeypatch.setattr(dependencies, "SQLAlchemyApplicationRepository", _Repo)
    return store


# -- get_current_user (AUTH-5, ADR-15) ----------------------------------------

async def test_current_user_with_valid_token_is_resolved(users):
    """Un bearer válido de un usuario activo devuelve ese usuario."""
    user = _user()
    users[user.user_id] = user

    resolved = await dependencies.get_current_user(_bearer(_token(user.user_id)), None)

    assert resolved is user


async def test_current_user_without_bearer_is_401(users):
    """Sin header Authorization → 401 `invalid_token`."""
    with pytest.raises(AuthenticationError) as excinfo:
        await dependencies.get_current_user(None, None)
    assert excinfo.value.code == "invalid_token"


def _bad_tokens(user_id) -> dict[str, str]:
    settings = get_settings()
    claims_without_sub = {"role": "Admin", "iss": DEFAULT_ISSUER}
    return {
        "expirado": _token(user_id, expire_minutes=-1),
        "firma ajena": _token(user_id, secret="otro-secreto-" + "x" * 32),
        "issuer ajeno": _token(user_id, issuer="otro-emisor"),
        "sin sub": pyjwt.encode(claims_without_sub, settings.jwt_secret, algorithm="HS256"),
        "sub no uuid": _token("no-es-un-uuid"),
        "basura": "esto.no.es-un-jwt",
    }


@pytest.mark.parametrize(
    "case",
    ["expirado", "firma ajena", "issuer ajeno", "sin sub", "sub no uuid", "basura"],
)
async def test_current_user_with_bad_token_is_401_invalid_token(users, case):
    """Token expirado, con firma o issuer ajenos, sin `sub`, con `sub` que no
    es UUID o directamente basura → 401 `invalid_token`, nunca un 500."""
    user = _user()
    users[user.user_id] = user

    with pytest.raises(AuthenticationError) as excinfo:
        await dependencies.get_current_user(_bearer(_bad_tokens(user.user_id)[case]), None)
    assert excinfo.value.code == "invalid_token"


async def test_current_user_deleted_after_token_issued_is_401(users):
    """Token válido de un usuario que ya no existe → 401 `invalid_token`."""
    with pytest.raises(AuthenticationError) as excinfo:
        await dependencies.get_current_user(_bearer(_token(uuid4())), None)
    assert excinfo.value.code == "invalid_token"


async def test_current_user_inactive_is_403(users):
    """Token válido de un usuario desactivado → 403 `user_inactive`: la
    desactivación corta el acceso aunque el token no haya expirado."""
    user = _user(is_active=False)
    users[user.user_id] = user

    with pytest.raises(AuthorizationError) as excinfo:
        await dependencies.get_current_user(_bearer(_token(user.user_id)), None)
    assert excinfo.value.code == "user_inactive"


# -- require_role (ADR-04) ----------------------------------------------------

async def test_require_role_allows_listed_roles():
    """Un rol incluido en la lista pasa y devuelve el mismo usuario."""
    checker = dependencies.require_role("Admin", "Researcher")
    for role in ("Admin", "Researcher"):
        user = _user(role=role)
        assert await checker(user) is user


async def test_require_role_rejects_other_roles_with_403():
    """Un rol fuera de la lista → 403 `forbidden` (Researcher no muta)."""
    checker = dependencies.require_role("Admin")

    with pytest.raises(AuthorizationError) as excinfo:
        await checker(_user(role="Researcher"))
    assert excinfo.value.code == "forbidden"


# -- require_api_key (IAUTH-1..3, ADR-22) -------------------------------------

async def test_api_key_valid_returns_application(applications):
    """Una key válida de una app activa devuelve esa aplicación."""
    application = Application(
        app_id=uuid4(), name="piloto", is_active=True, api_token_hash=hash_api_key(VALID_KEY)
    )
    applications.append(application)

    assert await dependencies.require_api_key(VALID_KEY, None) is application


async def test_api_key_missing_invalid_and_revoked_are_the_same_401(applications):
    """Key ausente, con formato inválido o desconocida/revocada DEBEN dar el
    mismo 401 (código, mensaje y `WWW-Authenticate`): no se revela la causa."""
    errors = []
    for raw_key in (None, "no-tiene-prefijo", VALID_KEY):
        with pytest.raises(AuthenticationError) as excinfo:
            await dependencies.require_api_key(raw_key, None)
        exc = excinfo.value
        errors.append((exc.http_code, exc.code, exc.message, exc.headers))

    assert len(set(map(repr, errors))) == 1
    assert errors[0][:2] == (401, "invalid_api_key")
    assert errors[0][3] == {"WWW-Authenticate": "ApiKey"}


async def test_api_key_of_inactive_application_is_403(applications):
    """Key válida de una app inactiva → 403 `app_inactive` (no 401)."""
    applications.append(
        Application(
            app_id=uuid4(),
            name="apagada",
            is_active=False,
            api_token_hash=hash_api_key(VALID_KEY),
        )
    )

    with pytest.raises(AuthorizationError) as excinfo:
        await dependencies.require_api_key(VALID_KEY, None)
    assert excinfo.value.code == "app_inactive"


# -- Handlers de error (ADR-09, D5) -------------------------------------------

def _request(path: str) -> Request:
    return Request(
        {"type": "http", "method": "GET", "path": path, "headers": [], "query_string": b""}
    )


async def test_domain_error_handler_renders_error_response_with_headers():
    """Un DomainError se traduce a su HTTP status, al contrato
    `{error: {code, message}}` y propaga los headers (ADR-09)."""
    exc = NotFoundError("session not found", code="session_not_found",
                        headers={"X-Trace": "1"})

    response = await domain_error_handler(_request("/sessions/x"), exc)

    assert response.status_code == 404
    assert json.loads(response.body) == {
        "error": {"code": "session_not_found", "message": "session not found"}
    }
    assert response.headers["x-trace"] == "1"


async def test_validation_error_becomes_400_only_under_telemetry():
    """Bajo /telemetry/* un error de validación del envelope DEBE ser 400
    `schema_validation_error`; fuera de ese prefijo se conserva el 422
    estándar de FastAPI (D5)."""
    exc = RequestValidationError(
        [{"loc": ("body", "events"), "msg": "Field required", "type": "missing"}]
    )

    telemetry = await validation_error_handler(_request("/telemetry/metrics"), exc)
    other = await validation_error_handler(_request("/applications"), exc)

    assert telemetry.status_code == 400
    assert json.loads(telemetry.body)["error"]["code"] == "schema_validation_error"
    assert other.status_code == 422
    assert "detail" in json.loads(other.body)
