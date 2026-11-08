"""Puerto de lectura de alertas (capa de dominio) — ISS-B-03 (#68).

`AlertRepository` abstrae la consulta app-scoped de `alert`: el tenant es
SIEMPRE parámetro del caller (ADR-0003/OAS-14). Es de solo lectura: las
alertas las crea el motor de reglas (B.14) y las despacha B.10.

`AlertRecord` no incluye `recipient`: es un mail o un chat id de Telegram,
un dato de configuración del dispatcher que la lectura no necesita exponer
(ADR-0012). `status` y `channel` son los nombres del catálogo en minúsculas.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

# pylint: disable=too-many-instance-attributes,too-few-public-methods  # DTO plano

# Dominio cerrado de severidad (`ck_alert_severity`, migración 0007).
ALERT_SEVERITIES = ("low", "medium", "high", "critical")
# Catálogo `alert_status` (DDL 0001) en minúsculas, como lo expone la API.
ALERT_STATUSES = ("pending", "sent", "failed")


@dataclass(frozen=True)
class AlertRecord:
    """Alerta de la aplicación autenticada (ADR-0012)."""

    alert_id: UUID
    application_id: UUID
    severity: str
    message: str
    status: str
    created_at: datetime
    anomaly_id: UUID | None = None  # NULL en alertas de umbral (v1)
    channel: str | None = None  # NULL hasta que B.10 la despacha
    sent_at: datetime | None = None


class AlertRepository(Protocol):
    """Lectura app-scoped de alertas: el tenant es parámetro (OAS-14)."""

    async def list_alerts(
        self,
        app_id: UUID,
        start: datetime,
        end: datetime,
        limit: int,
        status: str | None = None,
    ) -> list[AlertRecord]:
        """Alertas de `app_id` creadas en `[start, end)`, la más nueva
        primero, como máximo `limit`; opcionalmente en un solo estado."""
        ...
