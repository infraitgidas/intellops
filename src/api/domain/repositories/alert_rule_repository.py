"""Puerto del motor de reglas de umbral (capa de dominio) — ISS-B-14 (#74).

`AlertRuleRepository` abstrae lo que el servicio necesita de la base: las
aplicaciones activas, los overrides de reglas, un agregado por regla y ventana,
el chequeo de cooldown por consulta a `alert` y la inserción de la alerta
Pending. No hace commit: la transacción es del caller (el evaluador);
`rule_transaction` aísla cada regla (savepoint) dentro de ella. El
tenant es SIEMPRE parámetro (ADR-0003).
"""

from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from api.domain.services.alert_rules import AlertRule

# pylint: disable=too-many-instance-attributes,too-few-public-methods  # DTOs planos


@dataclass(frozen=True)
class Observation:
    """Agregado de una regla en la ventana: `value` es None sin muestra."""

    value: float | None
    samples: int


@dataclass(frozen=True)
class NewAlert:
    """Alerta Pending a insertar. `recipient`, `channel_id`, `sent_at` y
    `anomaly_id` quedan NULL: el destino lo resuelve B.10 (ADR-0012)."""

    application_id: UUID
    rule_id: str
    severity: str
    threshold: float
    observed_value: float
    message: str
    created_at: datetime


class AlertRuleRepository(Protocol):
    """Lecturas acotadas por tenant e inserción de alertas de regla."""

    def rule_transaction(self) -> AbstractAsyncContextManager[None]:
        """Aísla la evaluación de UNA regla: si el bloque lanza, se deshace solo
        lo hecho dentro y la transacción del caller sigue utilizable."""
        ...

    async def list_active_application_ids(self) -> list[UUID]:
        """Aplicaciones con `is_active = TRUE`."""
        ...

    async def list_rule_overrides(self, app_id: UUID) -> list[AlertRule]:
        """Filas de `alert_rule` de `app_id` (incluidas las deshabilitadas)."""
        ...

    async def observe(
        self, app_id: UUID, rule_id: str, start: datetime, end: datetime
    ) -> Observation:
        """Valor y muestras de la regla en la ventana `[start, end)`."""
        ...

    async def has_recent_alert(self, app_id: UUID, rule_id: str, since: datetime) -> bool:
        """True si hay una alerta de la regla con `created_at > since`,
        sin importar su estado."""
        ...

    async def create_alert(self, alert: NewAlert) -> None:
        """Inserta la alerta en estado Pending (sin commit)."""
        ...
