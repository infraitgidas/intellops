# SPEC — ISS-S3-06: Pruebas unitarias de módulos críticos

**Tipo**: Delta spec. **Cambio**: ISS-S3-06 (GitHub #45). **Base**: `proposal.md`, ISS-S2-04 (capas de test), ADR-10, ADR-13, ADR-04, ADR-19, ADR-22.
**Alcance**: capa unitaria (sin Postgres) de los módulos críticos de normalización, validación, lógica de negocio y transformación. Sin cambios de producción.

## Capabilities

- **Modificadas**: `qa`

---

## 1. qa (Modificada)

## ADDED Requirements

### Requirement: QA-U1 (cobertura unitaria por módulo crítico)

Con `pytest -m unit` solo, cada módulo de la tabla MUST alcanzar la cobertura de líneas indicada:

| Criterio de #45 | Módulos | Mínimo |
|---|---|---|
| Normalización | `api/domain/services/ingest_normalizer.py` | 100 % |
| Validaciones | `ingest_policy.py`, `query_service.py`, `presentation/dependencies.py`, `presentation/errors.py` | 100 % |
| Lógica de negocio | `application_service.py`, `user_service.py`, `auth_service.py`, `ingest_service.py` | 90 % |
| Transformaciones | `infrastructure/ingest/queue.py`, `ml/pipeline/api_reader.py` | 90 % |

Los tests MUST NOT pedir fixtures de base de datos, para que corran en el job "Unit Tests" del CI.

### Requirement: QA-U2 (invariante transaccional de los servicios, ADR-10)

Los tests de servicios MUST verificar que un caso feliz commitea, que un `DomainError` hace rollback y que nunca queda un commit antes del error.

#### Scenario: Error de dominio a mitad de operación

- GIVEN un servicio con `FakeSession`
- WHEN la operación levanta `ConflictError` o `NotFoundError` dentro del bloque transaccional
- THEN la sesión registra `rollback` y ningún `commit`

### Requirement: QA-U3 (seguridad del login)

Los tests de `AuthService` MUST fijar que:

- email inexistente, usuario sin password y password incorrecta dan el mismo error (código, mensaje y status);
- con usuario inexistente o sin hash se verifica contra `DUMMY_HASH` (ADR-13);
- un usuario inactivo con password correcta recibe 403 sin actualizar `last_login`, y con password incorrecta recibe 401.

#### Scenario: Anti-enumeración

- GIVEN un usuario con password, uno sin password y un email que no existe
- WHEN se intenta el login con credenciales incorrectas para cada uno
- THEN los tres errores son idénticos: 401 `invalid_credentials` con el mismo mensaje

### Requirement: QA-U4 (guards de acceso)

Los tests de `dependencies.py` MUST cubrir:

- `get_current_user`: sin bearer, token expirado, con firma o issuer ajenos, sin `sub`, con `sub` que no es UUID, basura y usuario inexistente → 401 `invalid_token`; usuario inactivo → 403 `user_inactive`.
- `require_role`: roles permitidos pasan; otro rol → 403 `forbidden`.
- `require_api_key`: key ausente, con formato inválido y desconocida o revocada → el mismo 401 con `WWW-Authenticate: ApiKey`; app inactiva → 403 `app_inactive`.

### Requirement: QA-U5 (bugs encontrados)

Un bug que destapen los tests MUST quedar documentado con un test `xfail(strict=True)` que describa el comportamiento esperado y MUST corregirse en un cambio aparte. Al corregirlo, el test pasa, `strict=True` lo convierte en falla y obliga a quitar la marca.

---

## Límites de recursos

Suite unitaria completa < 60 s, CPU-only, sin Postgres ni red.

## Criterios ML

No aplica: no se entrenan ni evalúan modelos.
