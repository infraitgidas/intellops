"""Puerto de lectura de sesiones RUM (capa de dominio) — ISS-S3-03 (#42).

`SessionRepository` abstrae la consulta app-scoped de `user_session`: el
tenant es SIEMPRE parámetro del caller (ADR-0003/OAS-14), nunca un dato del
request. La sesión la crea la ingesta en el primer evento (ADR-0002); este
puerto es de solo lectura (ADR-0011).

`SessionSummary` expone solo datos que el servidor realmente registra:
`user_id`, `ip_address`, `os_version`, `end_timestamp` y `duration_ms`
existen en el DDL pero siempre son NULL en v1 (ADR-0011), así que no forman
parte del DTO. `last_activity_at` es una observación derivada (timestamp más
reciente entre las métricas y excepciones de la sesión), no un cierre.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

# pylint: disable=too-few-public-methods  # DTO plano


@dataclass(frozen=True)
class SessionSummary:
    """Sesión RUM del tenant con su actividad agregada (ADR-0011)."""

    session_id: UUID
    application_id: UUID
    start_timestamp: datetime
    metric_count: int
    exception_count: int
    last_activity_at: datetime | None = None  # None si la sesión no tiene filas
    user_agent: str | None = None


class SessionRepository(Protocol):
    """Lectura app-scoped de sesiones RUM: el tenant es parámetro (OAS-14)."""

    async def list_sessions(
        self,
        app_id: UUID,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> list[SessionSummary]:
        """Sesiones de `app_id` iniciadas en `[start, end)`, la más nueva
        primero, como máximo `limit`."""
        ...

    async def get_session(
        self, app_id: UUID, session_id: UUID
    ) -> SessionSummary | None:
        """La sesión `session_id` SOLO si pertenece a `app_id` (filtro por
        `session_id` AND `app_id`, ADR-0003); si no, None."""
        ...
