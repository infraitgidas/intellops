"""Hashing de passwords con argon2 (pwdlib) — ADR-02, SEC-5."""

from pwdlib import PasswordHash

# Password fija cuyo hash se usa para igualar timing en login fallido
# (ADR-13, anti-enumeración). Hash precomputado: el salt viaja embebido
# en la cadena argon2, por lo que verify() funciona en cualquier entorno.
DUMMY_PASSWORD = "intellops-dummy-password-for-timing"
DUMMY_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$KNweEo0XJVqrVF+JYmUqFw$"
    "xV3doHrpD0cM0U+e0jFS5Abwdonneo0P6zJwjJ9owaQ"
)


class PasswordHasher:
    """Envoltorio de pwdlib con parámetros recomendados (argon2id)."""

    def __init__(self) -> None:
        self._password_hash = PasswordHash.recommended()

    def hash_password(self, plain: str) -> str:
        """Devuelve el hash argon2id de `plain` (salt aleatorio)."""
        return self._password_hash.hash(plain)

    def verify_password(self, plain: str, hashed: str) -> bool:
        """Verifica `plain` contra un hash argon2; False si no matchea."""
        return self._password_hash.verify(plain, hashed)
