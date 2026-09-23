"""Tests unitarios del PR-A (core-auth-infra): config, exceptions y security.

Cubre A2 (config JWT), A3 (exceptions), A4 (password argon2),
A5 (jwt claims) y A6 (api keys dormidas) — escenarios AUTH-6, SEC-5.
"""

import logging
import re
import sys
from uuid import uuid4

import jwt as pyjwt
import pytest
from pydantic import ValidationError

from api.config import Settings
from api.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
)
from api.infrastructure.security.api_keys import (
    ApiKeyRedactionFilter,
    generate_api_key,
    hash_api_key,
    redact_api_key,
)
from api.infrastructure.security.jwt import create_access_token, decode_token
from api.infrastructure.security.password import (
    DUMMY_HASH,
    DUMMY_PASSWORD,
    PasswordHasher,
)


# -- A2: config (AUTH-6) ----------------------------------------------------

def test_jwt_secret_shorter_than_32_rejected():
    """jwt_secret < 32 chars DEBE fallar la validación de settings."""
    with pytest.raises(ValidationError):
        Settings(jwt_secret="too-short")


def test_jwt_secret_exactly_32_chars_accepted():
    settings = Settings(jwt_secret="a" * 32)
    assert settings.jwt_secret == "a" * 32


def test_settings_jwt_defaults():
    settings = Settings(jwt_secret="s" * 32)
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_access_token_expire_minutes == 30
    assert settings.api_key_prefix == "ilp_"


def test_settings_default_jwt_secret_meets_minimum():
    assert len(Settings().jwt_secret) >= 32


# -- A3: exceptions tipificadas (ADR-09) ------------------------------------

def test_domain_error_subtypes_and_http_codes():
    assert issubclass(AuthenticationError, DomainError)
    assert issubclass(AuthorizationError, DomainError)
    assert issubclass(NotFoundError, DomainError)
    assert issubclass(ConflictError, DomainError)
    assert AuthenticationError.http_code == 401
    assert AuthorizationError.http_code == 403
    assert NotFoundError.http_code == 404
    assert ConflictError.http_code == 409


def test_domain_error_default_codes_and_override():
    err = AuthenticationError("invalid credentials")
    assert err.message == "invalid credentials"
    assert err.code == "invalid_credentials"
    assert str(err) == "invalid credentials"

    err2 = AuthorizationError("user inactive", code="user_inactive")
    assert err2.code == "user_inactive"

    assert NotFoundError("missing").code == "not_found"
    assert ConflictError("duplicate").code == "conflict"


def test_domain_error_supports_headers_for_www_authenticate():
    """DomainError DEBE aceptar headers (p. ej. WWW-Authenticate) y el
    handler de main.py los propaga a la respuesta (design §4, IAUTH-1)."""
    err = AuthenticationError(
        "missing api key", code="invalid_api_key", headers={"WWW-Authenticate": "ApiKey"}
    )
    assert err.headers == {"WWW-Authenticate": "ApiKey"}
    assert err.code == "invalid_api_key"

    plain = NotFoundError("missing")
    assert plain.headers is None


# -- A4: password argon2 (pwdlib) -------------------------------------------

def test_password_hash_roundtrip():
    hasher = PasswordHasher()
    hashed = hasher.hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert hashed.startswith("$argon2")
    assert hasher.verify_password("correct horse battery staple", hashed) is True


def test_password_verify_rejects_wrong_password():
    hasher = PasswordHasher()
    hashed = hasher.hash_password("right-password")
    assert hasher.verify_password("wrong-password", hashed) is False


def test_dummy_hash_is_valid_argon2_and_verifies_dummy():
    assert DUMMY_HASH.startswith("$argon2id$")
    hasher = PasswordHasher()
    assert hasher.verify_password(DUMMY_PASSWORD, DUMMY_HASH) is True
    assert hasher.verify_password("not-the-dummy-password", DUMMY_HASH) is False


# -- A5: jwt claims (AUTH-1) ------------------------------------------------

SECRET = "test-secret-key-0123456789abcdef"


def test_create_access_token_claims():
    user_id = uuid4()
    token = create_access_token(user_id, "Admin", secret=SECRET)
    payload = decode_token(token, SECRET)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "Admin"
    assert payload["iss"] == "intellops-api"
    assert payload["exp"] - payload["iat"] == 1800


def test_decode_token_rejects_expired_token():
    token = create_access_token(uuid4(), "Admin", secret=SECRET, expire_minutes=-1)
    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_token(token, SECRET)


def test_decode_token_rejects_invalid_signature():
    token = create_access_token(uuid4(), "Admin", secret=SECRET)
    with pytest.raises(pyjwt.InvalidSignatureError):
        decode_token(token, "y" * 32)


def test_decode_token_rejects_tampered_sub():
    token = create_access_token(uuid4(), "Admin", secret=SECRET)
    # Firma válida pero claims alterados: la firma deja de corresponder.
    with pytest.raises(pyjwt.InvalidTokenError):
        decode_token(token + "x", SECRET)


# -- A6: api keys dormidas (SEC-5) ------------------------------------------

def test_generate_api_key_format():
    key = generate_api_key()
    assert key.startswith("ilp_")
    assert len(key) == 47
    payload = key[len("ilp_"):]
    assert len(payload) == 43
    assert re.fullmatch(r"[A-Za-z0-9_-]{43}", payload)


def test_generate_api_key_is_unique():
    assert generate_api_key() != generate_api_key()


def test_generate_api_key_custom_prefix():
    key = generate_api_key(prefix="custom_")
    assert key.startswith("custom_")
    assert len(key) == len("custom_") + 43


def test_hash_api_key_sha256_hex_deterministic():
    key = generate_api_key()
    digest = hash_api_key(key)
    assert len(digest) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", digest)
    assert hash_api_key(key) == digest
    assert hash_api_key(key) != hash_api_key(generate_api_key())


# -- IAUTH-4 / SEC-7: redacción de API keys en logs -------------------------

REDACTED = "ilp_***REDACTED***"


def _sample_key() -> str:
    return generate_api_key()  # ilp_ + 43 chars base64url


def test_redact_api_key_hides_full_key_value():
    """redact_api_key DEBE reemplazar el valor completo de la key
    (prefijo + 43 chars) por un marcador (IAUTH-4)."""
    key = _sample_key()
    text = f"request with X-API-Key {key} processed"
    redacted = redact_api_key(text)
    assert key not in redacted
    assert REDACTED in redacted
    assert redacted.startswith("request with X-API-Key ")


def test_redact_api_key_leaves_unrelated_text_untouched():
    """Redacción NO DEBE tocar texto sin formato de key (evita falsos
    positivos en logs normales)."""
    msg = "GET /health 200 1.2ms session=abc123"
    assert redact_api_key(msg) == msg


def test_redact_api_key_requires_full_43_char_payload():
    """Prefijo suelto o payload corto NO es una key válida: no se redacta
    (el patrón exige los 43 chars base64url completos)."""
    assert redact_api_key("ilp_short") == "ilp_short"


def test_redaction_filter_redacts_record_message():
    """ApiKeyRedactionFilter DEBE redactar el mensaje del LogRecord."""
    key = _sample_key()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg=f"auth failed with key {key}", args=(), exc_info=None,
    )
    assert ApiKeyRedactionFilter().filter(record) is True
    assert key not in record.getMessage()
    assert REDACTED in record.getMessage()


def test_redaction_filter_redacts_record_args():
    """ApiKeyRedactionFilter DEBE redactar args interpolables (msg con %s)."""
    key = _sample_key()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="ingest rejected api_key=%s", args=(key,), exc_info=None,
    )
    assert ApiKeyRedactionFilter().filter(record) is True
    assert key not in record.getMessage()
    assert "ingest rejected api_key=ilp_***REDACTED***" == record.getMessage()


def test_redaction_filter_redacts_traceback_text():
    """IAUTH-4: el traceback formateado (exc_info) NO DEBE contener la key."""
    key = _sample_key()
    try:
        raise ValueError(f"boom with key {key}")
    except ValueError:
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname=__file__, lineno=1,
            msg="request failed", args=(), exc_info=sys.exc_info(),
        )
    assert ApiKeyRedactionFilter().filter(record) is True
    assert key not in (record.exc_text or "")
    assert REDACTED in (record.exc_text or "")
