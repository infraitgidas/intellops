"""Unit: lógica de negocio de ApplicationService (ISS-S3-06, #45).

Los endpoints de aplicaciones y API keys ya tienen tests de integración
(`test_applications.py`, `test_api_keys_endpoints.py`), pero sin Postgres
estas reglas quedaban sin ninguna verificación. Este módulo las fija con un
repositorio en memoria y `FakeSession` (conftest):

- 404 en get/update/delete de inexistente, sin commit (APP-1..APP-4).
- ADR-10: el caso feliz commitea; un DomainError hace rollback.
- CRED-1..CRED-4: la key se devuelve una sola vez, se persiste solo su hash,
  409 `key_exists` con key activa, revocación idempotente.
- IAUTH-1..3 / ADR-19: autenticación con gate de prefijo, 401 indistinguible
  y 403 `app_inactive`.
"""

from uuid import uuid4

import pytest

from api.domain.entities.application import Application
from api.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
)
from api.domain.services.application_service import ApplicationService
from api.infrastructure.security.api_keys import hash_api_key
from api.presentation.schemas.application import ApplicationCreate, ApplicationUpdate


class _InMemoryApplications:
    """ApplicationRepository en memoria; registra lookups y updates."""

    def __init__(self, *applications: Application) -> None:
        self.items = {app.app_id: app for app in applications}
        self.updated: list[Application] = []
        self.hash_lookups: list[str] = []
        self.delete_error: Exception | None = None
        self.lookup_override: Application | None = None

    async def get_by_id(self, app_id):
        return self.items.get(app_id)

    async def list(self):
        return list(self.items.values())

    async def create(self, application):
        if application.app_id is None:
            application.app_id = uuid4()
        self.items[application.app_id] = application
        return application

    async def update(self, application):
        self.updated.append(application)

    async def delete(self, app_id):
        if self.delete_error is not None:
            raise self.delete_error
        del self.items[app_id]

    async def get_by_api_token_hash(self, api_token_hash):
        self.hash_lookups.append(api_token_hash)
        if self.lookup_override is not None:
            return self.lookup_override
        return next(
            (a for a in self.items.values() if a.api_token_hash == api_token_hash),
            None,
        )


def _app(**overrides) -> Application:
    fields = {
        "app_id": uuid4(),
        "name": "piloto",
        "description": None,
        "is_active": True,
        "api_token_hash": None,
    }
    fields.update(overrides)
    return Application(**fields)


def _service(fake_session, *applications):
    repo = _InMemoryApplications(*applications)
    return ApplicationService(fake_session, repo), repo


# -- CRUD ---------------------------------------------------------------------

async def test_list_applications_returns_repository_items(fake_session):
    """`list_applications` devuelve lo que tiene el repositorio, sin commit."""
    first, second = _app(name="a"), _app(name="b")
    service, _ = _service(fake_session, first, second)

    assert await service.list_applications() == [first, second]
    assert fake_session.calls == []


async def test_get_missing_application_is_404_without_side_effects(fake_session):
    """Una aplicación inexistente → NotFoundError (404) sin tocar la sesión."""
    service, _ = _service(fake_session)

    with pytest.raises(NotFoundError) as excinfo:
        await service.get_application(uuid4())
    assert excinfo.value.http_code == 404
    assert fake_session.calls == []


async def test_create_application_starts_without_api_key_and_commits(fake_session):
    """Crear guarda nombre y descripción, nace sin key (ADR-16) y commitea."""
    service, repo = _service(fake_session)

    created = await service.create_application(
        ApplicationCreate(name="piloto", description="sitio medido")
    )

    assert repo.items[created.app_id] is created
    assert created.name == "piloto"
    assert created.description == "sitio medido"
    assert created.api_token_hash is None
    assert fake_session.calls == ["commit", "refresh"]


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Bug detectado en ISS-S3-06: create_application ignora "
        "ApplicationCreate.is_active, que el contrato declara (APP-7, default "
        "true). Una app creada con is_active=false queda activa. Se corrige en "
        "un cambio aparte; al corregirlo este test pasa y hay que quitar el xfail."
    ),
)
async def test_create_application_honours_is_active_false(fake_session):
    """POST /applications con is_active=false DEBE crear la app inactiva."""
    service, _ = _service(fake_session)

    created = await service.create_application(
        ApplicationCreate(name="apagada", is_active=False)
    )

    assert created.is_active is False


async def test_update_application_changes_only_sent_fields(fake_session):
    """Un update parcial cambia solo los campos enviados y commitea (APP-3)."""
    application = _app(name="viejo", description="desc", is_active=True)
    service, repo = _service(fake_session, application)

    updated = await service.update_application(
        application.app_id, ApplicationUpdate(is_active=False)
    )

    assert updated.is_active is False
    assert updated.name == "viejo"
    assert updated.description == "desc"
    assert repo.updated == [application]
    assert fake_session.calls == ["commit", "refresh"]


async def test_update_application_can_change_every_field(fake_session):
    """Nombre, descripción y estado se actualizan juntos cuando vienen."""
    application = _app(name="viejo", description=None, is_active=False)
    service, _ = _service(fake_session, application)

    updated = await service.update_application(
        application.app_id,
        ApplicationUpdate(name="nuevo", description="otra", is_active=True),
    )

    assert (updated.name, updated.description, updated.is_active) == (
        "nuevo",
        "otra",
        True,
    )


async def test_update_missing_application_is_404_without_update(fake_session):
    """Actualizar una app inexistente → 404 sin llamar al repo ni commitear."""
    service, repo = _service(fake_session)

    with pytest.raises(NotFoundError):
        await service.update_application(uuid4(), ApplicationUpdate(name="x"))
    assert repo.updated == []
    assert fake_session.calls == []


async def test_delete_application_removes_and_commits(fake_session):
    """Borrar una app existente la elimina y commitea (APP-4)."""
    application = _app()
    service, repo = _service(fake_session, application)

    await service.delete_application(application.app_id)

    assert application.app_id not in repo.items
    assert fake_session.calls == ["commit"]


async def test_delete_missing_application_is_404(fake_session):
    """Borrar una app inexistente → 404 sin tocar la sesión."""
    service, _ = _service(fake_session)

    with pytest.raises(NotFoundError):
        await service.delete_application(uuid4())
    assert fake_session.calls == []


async def test_delete_with_sessions_rolls_back_and_propagates_409(fake_session):
    """FK RESTRICT de user_session → ConflictError 409 con rollback y sin
    commit (ADR-07, ADR-10)."""
    application = _app()
    service, repo = _service(fake_session, application)
    repo.delete_error = ConflictError("application has associated sessions")

    with pytest.raises(ConflictError) as excinfo:
        await service.delete_application(application.app_id)

    assert excinfo.value.http_code == 409
    assert fake_session.calls == ["rollback"]
    assert application.app_id in repo.items


# -- Emisión y revocación de API key (CRED-1..CRED-4) -------------------------

async def test_issue_api_key_returns_plaintext_once_and_stores_only_hash(fake_session):
    """La key se devuelve en claro una sola vez; se persiste solo su SHA-256
    y el hint son los últimos 4 caracteres (CRED-1, SEC-7)."""
    application = _app()
    service, repo = _service(fake_session, application)

    issued = await service.issue_api_key(application.app_id)

    assert issued.api_key.startswith("ilp_")
    assert issued.hint == issued.api_key[-4:]
    assert application.api_token_hash == hash_api_key(issued.api_key)
    assert issued.api_key not in application.api_token_hash
    assert repo.updated == [application]
    assert fake_session.calls == ["commit", "refresh"]


async def test_issue_api_key_generates_a_different_key_each_time(fake_session):
    """Dos emisiones (con revocación en el medio) dan keys distintas."""
    application = _app()
    service, _ = _service(fake_session, application)

    first = await service.issue_api_key(application.app_id)
    await service.revoke_api_key(application.app_id)
    second = await service.issue_api_key(application.app_id)

    assert first.api_key != second.api_key


async def test_issue_api_key_with_active_key_is_409_key_exists(fake_session):
    """Con una key activa, emitir otra → 409 `key_exists` sin pisar el hash
    (CRED-3: la rotación es revocar y emitir)."""
    application = _app(api_token_hash="a" * 64)
    service, repo = _service(fake_session, application)

    with pytest.raises(ConflictError) as excinfo:
        await service.issue_api_key(application.app_id)

    assert excinfo.value.code == "key_exists"
    assert application.api_token_hash == "a" * 64
    assert repo.updated == []
    assert fake_session.calls == []


async def test_issue_api_key_for_missing_application_is_404(fake_session):
    """Emitir key para una app inexistente → 404."""
    service, _ = _service(fake_session)

    with pytest.raises(NotFoundError):
        await service.issue_api_key(uuid4())


async def test_revoke_api_key_clears_hash_and_commits(fake_session):
    """Revocar borra el hash y commitea (CRED-4, fail-closed)."""
    application = _app(api_token_hash="b" * 64)
    service, repo = _service(fake_session, application)

    await service.revoke_api_key(application.app_id)

    assert application.api_token_hash is None
    assert repo.updated == [application]
    assert fake_session.calls == ["commit"]


async def test_revoke_without_active_key_is_idempotent_noop(fake_session):
    """Revocar sin key activa no actualiza ni commitea (idempotente)."""
    application = _app(api_token_hash=None)
    service, repo = _service(fake_session, application)

    await service.revoke_api_key(application.app_id)

    assert repo.updated == []
    assert fake_session.calls == []


# -- Autenticación de API key (IAUTH-1..3, ADR-19) ----------------------------

async def test_authenticate_valid_key_returns_application(fake_session):
    """Una key emitida autentica y devuelve su aplicación."""
    application = _app()
    service, _ = _service(fake_session, application)
    issued = await service.issue_api_key(application.app_id)

    assert await service.authenticate_api_key(issued.api_key) is application


@pytest.mark.parametrize("raw_key", ["", "sk_live_abc", "ILP_abc", "xilp_abc"])
async def test_authenticate_rejects_wrong_prefix_without_lookup(fake_session, raw_key):
    """Sin el prefijo `ilp_` → 401 `invalid_api_key` SIN consultar el repo
    (gate barato antes del hash)."""
    service, repo = _service(fake_session, _app())

    with pytest.raises(AuthenticationError) as excinfo:
        await service.authenticate_api_key(raw_key)

    assert excinfo.value.code == "invalid_api_key"
    assert repo.hash_lookups == []


async def test_authenticate_unknown_or_revoked_key_is_indistinguishable_401(fake_session):
    """Una key desconocida y una revocada DEBEN dar el mismo 401 (mismo
    código y mensaje): no se revela cuál de las dos es (IAUTH-3)."""
    application = _app()
    service, _ = _service(fake_session, application)
    issued = await service.issue_api_key(application.app_id)
    await service.revoke_api_key(application.app_id)

    errors = []
    for raw_key in (issued.api_key, "ilp_" + "x" * 43):
        with pytest.raises(AuthenticationError) as excinfo:
            await service.authenticate_api_key(raw_key)
        errors.append((excinfo.value.code, excinfo.value.message))

    assert errors[0] == errors[1] == ("invalid_api_key", "invalid api key")


async def test_authenticate_rejects_lookup_whose_hash_does_not_match(fake_session):
    """Si el lookup devolviera una app cuyo hash no coincide, la comparación
    timing-safe DEBE rechazarla con 401 (defensa en profundidad)."""
    service, repo = _service(fake_session)
    repo.lookup_override = _app(api_token_hash="c" * 64)

    with pytest.raises(AuthenticationError) as excinfo:
        await service.authenticate_api_key("ilp_" + "y" * 43)
    assert excinfo.value.code == "invalid_api_key"


async def test_authenticate_key_of_inactive_application_is_403(fake_session):
    """Key válida de una app inactiva → 403 `app_inactive` (APP-8)."""
    application = _app()
    service, _ = _service(fake_session, application)
    issued = await service.issue_api_key(application.app_id)
    application.is_active = False

    with pytest.raises(AuthorizationError) as excinfo:
        await service.authenticate_api_key(issued.api_key)

    assert excinfo.value.http_code == 403
    assert excinfo.value.code == "app_inactive"
