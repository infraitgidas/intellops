"""Unit: lógica de negocio de UserService (ISS-S3-06, #45).

Fija sin Postgres las reglas de usuarios que hasta ahora solo cubrían los
tests de integración (`test_users.py`), con un repositorio en memoria y
`FakeSession` (conftest):

- 404 en get/update de inexistente (USR-2, USR-5).
- Rol inexistente → 409 con rollback (ADR-14).
- La password se guarda hasheada con argon2 y solo se re-hashea si viene en
  el update (USR-3, USR-5); el plaintext nunca queda en la entidad (SEC-4).
- ADR-10: caso feliz con commit; DomainError con rollback y sin commit.
"""

from uuid import uuid4

import pytest

from api.domain.entities.lab_user import LabUser
from api.domain.entities.user_role import UserRole
from api.domain.exceptions import ConflictError, NotFoundError
from api.domain.services.user_service import UserService
from api.infrastructure.security.password import PasswordHasher
from api.presentation.schemas.user import UserCreate, UserUpdate

ADMIN = UserRole(role_id=1, name="Admin")
RESEARCHER = UserRole(role_id=2, name="Researcher")


class _InMemoryUsers:
    """UserRepository en memoria con catálogo de roles fijo."""

    def __init__(self, *users: LabUser) -> None:
        self.items = {user.user_id: user for user in users}
        self.roles = {ADMIN.role_id: ADMIN, RESEARCHER.role_id: RESEARCHER}
        self.updated: list[LabUser] = []
        self.create_error: Exception | None = None

    async def get_by_id(self, user_id):
        return self.items.get(user_id)

    async def get_by_email(self, email):
        return next((u for u in self.items.values() if u.email == email), None)

    async def list(self):
        return list(self.items.values())

    async def create(self, user):
        if self.create_error is not None:
            raise self.create_error
        if user.user_id is None:
            user.user_id = uuid4()
        self.items[user.user_id] = user
        return user

    async def update(self, user):
        self.updated.append(user)

    async def get_role_by_id(self, role_id):
        return self.roles.get(role_id)


def _user(**overrides) -> LabUser:
    fields = {
        "user_id": uuid4(),
        "name": "Ana",
        "email": "ana@intellops.local",
        "role_id": RESEARCHER.role_id,
        "is_active": True,
        "password_hash": "hash-original",
    }
    fields.update(overrides)
    return LabUser(**fields)


def _service(fake_session, *users):
    repo = _InMemoryUsers(*users)
    return UserService(fake_session, repo), repo


# -- Lectura ------------------------------------------------------------------

async def test_list_and_get_user(fake_session):
    """`list_users` y `get_user` devuelven lo del repositorio sin commit."""
    user = _user()
    service, _ = _service(fake_session, user)

    assert await service.list_users() == [user]
    assert await service.get_user(user.user_id) is user
    assert fake_session.calls == []


async def test_get_missing_user_is_404(fake_session):
    """Un usuario inexistente → NotFoundError (404)."""
    service, _ = _service(fake_session)

    with pytest.raises(NotFoundError) as excinfo:
        await service.get_user(uuid4())
    assert excinfo.value.http_code == 404


# -- Alta (USR-3/USR-4, ADR-14) -----------------------------------------------

async def test_create_user_hashes_password_and_commits(fake_session):
    """Crear guarda el hash argon2 (nunca el plaintext) con el rol pedido y
    commitea."""
    service, repo = _service(fake_session)

    created = await service.create_user(
        UserCreate(
            name="Beto",
            email="beto@intellops.local",
            password="password-segura",
            role_id=ADMIN.role_id,
        )
    )

    assert repo.items[created.user_id] is created
    assert created.role_id == ADMIN.role_id
    assert created.password_hash != "password-segura"
    assert created.password_hash.startswith("$argon2")
    assert PasswordHasher().verify_password("password-segura", created.password_hash)
    assert fake_session.calls == ["commit", "refresh"]


async def test_create_user_with_unknown_role_is_409_with_rollback(fake_session):
    """Un `role_id` inexistente → 409 con rollback y sin crear nada (ADR-14)."""
    service, repo = _service(fake_session)

    with pytest.raises(ConflictError) as excinfo:
        await service.create_user(
            UserCreate(
                name="Beto",
                email="beto@intellops.local",
                password="password-segura",
                role_id=99,
            )
        )

    assert excinfo.value.http_code == 409
    assert repo.items == {}
    assert fake_session.calls == ["rollback"]


async def test_create_user_duplicate_email_rolls_back(fake_session):
    """Si el repositorio rechaza el email duplicado (409), el servicio hace
    rollback y propaga el error sin commitear (USR-4, ADR-10)."""
    service, repo = _service(fake_session)
    repo.create_error = ConflictError("email already registered")

    with pytest.raises(ConflictError):
        await service.create_user(
            UserCreate(
                name="Beto",
                email="ana@intellops.local",
                password="password-segura",
                role_id=ADMIN.role_id,
            )
        )
    assert fake_session.calls == ["rollback"]


# -- Actualización (USR-5) ----------------------------------------------------

async def test_update_without_password_keeps_existing_hash(fake_session):
    """Un update sin `password` NO DEBE re-hashear: el hash queda igual."""
    user = _user(password_hash="hash-original")
    service, repo = _service(fake_session, user)

    updated = await service.update_user(user.user_id, UserUpdate(name="Ana María"))

    assert updated.name == "Ana María"
    assert updated.password_hash == "hash-original"
    assert repo.updated == [user]
    assert fake_session.calls == ["commit", "refresh"]


async def test_update_with_password_rehashes(fake_session):
    """Un update con `password` DEBE guardar el hash nuevo de esa password."""
    user = _user(password_hash="hash-original")
    service, _ = _service(fake_session, user)

    updated = await service.update_user(
        user.user_id, UserUpdate(password="otra-password-segura")
    )

    assert updated.password_hash != "hash-original"
    assert PasswordHasher().verify_password("otra-password-segura", updated.password_hash)


async def test_update_changes_every_sent_field(fake_session):
    """Nombre, email, estado y rol se actualizan juntos cuando vienen."""
    user = _user(role_id=RESEARCHER.role_id, is_active=True)
    service, _ = _service(fake_session, user)

    updated = await service.update_user(
        user.user_id,
        UserUpdate(
            name="Nuevo",
            email="nuevo@intellops.local",
            is_active=False,
            role_id=ADMIN.role_id,
        ),
    )

    assert (updated.name, updated.email, updated.is_active, updated.role_id) == (
        "Nuevo",
        "nuevo@intellops.local",
        False,
        ADMIN.role_id,
    )


async def test_update_with_unknown_role_is_409_and_keeps_user_intact(fake_session):
    """Cambiar a un rol inexistente → 409 con rollback; el rol no cambia."""
    user = _user(role_id=RESEARCHER.role_id)
    service, repo = _service(fake_session, user)

    with pytest.raises(ConflictError):
        await service.update_user(user.user_id, UserUpdate(role_id=99))

    assert user.role_id == RESEARCHER.role_id
    assert repo.updated == []
    assert fake_session.calls == ["rollback"]


async def test_update_missing_user_is_404_with_rollback(fake_session):
    """Actualizar un usuario inexistente → 404; la sesión queda limpia
    (rollback) y no se commitea nada."""
    service, repo = _service(fake_session)

    with pytest.raises(NotFoundError):
        await service.update_user(uuid4(), UserUpdate(name="x"))

    assert repo.updated == []
    assert fake_session.calls == ["rollback"]
