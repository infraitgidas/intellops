"""Unit: lógica de negocio de AuthService (ISS-S3-06, #45).

El login es la superficie más sensible de la API. Este módulo fija sin
Postgres sus reglas de seguridad, con un repositorio en memoria y
`FakeSession` (conftest):

- SEC-1: usuario inexistente, sin password y password incorrecta dan el
  MISMO 401, sin revelar cuál es el caso.
- ADR-13: con usuario inexistente o sin hash se verifica igual contra
  `DUMMY_HASH`, para que el tiempo de respuesta no delate si el email existe.
- SEC-2: usuario inactivo con password correcta → 403 sin tocar
  `last_login`; con password incorrecta sigue siendo 401 (el estado de la
  cuenta solo se revela a quien conoce la password).
- AUTH-1: login OK actualiza `last_login`, commitea y emite un JWT con `sub`
  y el rol denormalizado.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from api.config import get_settings
from api.domain.entities.lab_user import LabUser
from api.domain.entities.user_role import UserRole
from api.domain.exceptions import AuthenticationError, AuthorizationError
from api.domain.services.auth_service import AuthService
from api.infrastructure.security.jwt import decode_token
from api.infrastructure.security.password import DUMMY_HASH, PasswordHasher

PASSWORD = "password-correcta"
# argon2 es caro a propósito: se hashea una sola vez para todo el módulo.
PASSWORD_HASH = PasswordHasher().hash_password(PASSWORD)


class _InMemoryUsers:
    """UserRepository en memoria (solo lo que usa el login)."""

    def __init__(self, *users: LabUser) -> None:
        self.by_email = {user.email: user for user in users}

    async def get_by_email(self, email):
        return self.by_email.get(email)


class _SpyHasher:
    """PasswordHasher real que registra contra qué hash se verificó."""

    def __init__(self) -> None:
        self._real = PasswordHasher()
        self.verified_against: list[str] = []

    def verify_password(self, plain, hashed):
        self.verified_against.append(hashed)
        return self._real.verify_password(plain, hashed)


def _user(**overrides) -> LabUser:
    fields = {
        "user_id": uuid4(),
        "name": "Ana",
        "email": "ana@intellops.local",
        "role_id": 1,
        "is_active": True,
        "password_hash": PASSWORD_HASH,
        "last_login": None,
    }
    fields.update(overrides)
    user = LabUser(**fields)
    user.role = UserRole(role_id=1, name="Admin")
    return user


def _service(fake_session, *users):
    service = AuthService(fake_session, _InMemoryUsers(*users))
    spy = _SpyHasher()
    service._hasher = spy  # pylint: disable=protected-access
    return service, spy


async def test_login_ok_updates_last_login_commits_and_issues_token(fake_session):
    """Login correcto: `last_login` ≈ ahora, commit y JWT con sub, rol y la
    expiración configurada (AUTH-1)."""
    user = _user()
    service, _ = _service(fake_session, user)
    before = datetime.now(timezone.utc)

    response = await service.login(user.email, PASSWORD)

    settings = get_settings()
    claims = decode_token(response.access_token, settings.jwt_secret)
    assert claims["sub"] == str(user.user_id)
    assert claims["role"] == "Admin"
    assert response.token_type == "bearer"
    assert response.expires_in == settings.jwt_access_token_expire_minutes * 60
    assert before <= user.last_login <= datetime.now(timezone.utc) + timedelta(seconds=1)
    assert fake_session.calls == ["commit"]


async def test_unknown_email_verifies_against_dummy_hash_and_returns_401(fake_session):
    """Email inexistente → verificación contra DUMMY_HASH (igualar tiempos,
    ADR-13) y 401 `invalid_credentials` con rollback."""
    service, spy = _service(fake_session)

    with pytest.raises(AuthenticationError) as excinfo:
        await service.login("nadie@intellops.local", PASSWORD)

    assert excinfo.value.code == "invalid_credentials"
    assert spy.verified_against == [DUMMY_HASH]
    assert fake_session.calls == ["rollback"]


async def test_user_without_password_hash_also_uses_dummy_hash(fake_session):
    """Un usuario sin password (hash NULL, ADR-06) se trata igual que uno
    inexistente: DUMMY_HASH y el mismo 401."""
    user = _user(password_hash=None)
    service, spy = _service(fake_session, user)

    with pytest.raises(AuthenticationError):
        await service.login(user.email, PASSWORD)
    assert spy.verified_against == [DUMMY_HASH]


async def test_failed_logins_are_indistinguishable(fake_session):
    """Email inexistente, usuario sin password y password incorrecta DEBEN
    dar exactamente el mismo error (SEC-1, anti-enumeración)."""
    with_password = _user(email="con@intellops.local")
    without_password = _user(email="sin@intellops.local", password_hash=None)
    service, _ = _service(fake_session, with_password, without_password)

    errors = []
    for email, password in (
        ("nadie@intellops.local", PASSWORD),
        ("sin@intellops.local", PASSWORD),
        ("con@intellops.local", "password-incorrecta"),
    ):
        with pytest.raises(AuthenticationError) as excinfo:
            await service.login(email, password)
        errors.append(
            (excinfo.value.http_code, excinfo.value.code, excinfo.value.message)
        )

    assert len(set(errors)) == 1
    assert errors[0] == (401, "invalid_credentials", "invalid email or password")


async def test_inactive_user_with_correct_password_is_403_without_last_login(fake_session):
    """Usuario inactivo + password correcta → 403 `user_inactive`, sin
    actualizar `last_login` ni commitear (SEC-2)."""
    user = _user(is_active=False)
    service, _ = _service(fake_session, user)

    with pytest.raises(AuthorizationError) as excinfo:
        await service.login(user.email, PASSWORD)

    assert excinfo.value.http_code == 403
    assert excinfo.value.code == "user_inactive"
    assert user.last_login is None
    assert fake_session.calls == ["rollback"]


async def test_inactive_user_with_wrong_password_is_401_not_403(fake_session):
    """Con password incorrecta, un usuario inactivo DEBE dar 401: el 403
    solo se muestra a quien conoce la password (no filtra el estado)."""
    user = _user(is_active=False)
    service, _ = _service(fake_session, user)

    with pytest.raises(AuthenticationError) as excinfo:
        await service.login(user.email, "password-incorrecta")
    assert excinfo.value.http_code == 401


async def test_logout_is_stateless(fake_session):
    """Logout no persiste nada (AUTH-4)."""
    service, _ = _service(fake_session)

    assert await service.logout() is None
    assert fake_session.calls == []
