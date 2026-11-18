"""Puerto de configuración de reglas de umbral (capa de dominio) — ISS-B-14 (#74).

`AlertRuleRepository` abstrae la persistencia de `alert_rule`: umbrales por
aplicación y por métrica (ADR-0013, migración 0008). El tenant
(`application_id`) es SIEMPRE parámetro explícito del caller: la
configuración es CRUD de administración autenticado por rol (JWT), no
lectura de tenant por API key (design §9).

`AlertRuleRecord` es el DTO plano de la tabla. `threshold` es `Decimal`
porque el umbral es un valor de contrato que se compara con el observado:
en punto flotante la comparación inclusiva (ADR-0013 §5) quedaría a merced
del redondeo, igual que en la columna `NUMERIC`.

`upsert_rule` es idempotente por la clave `uq_alert_rule_key`
(`application_id`, `metric_type_id`, `comparison`, `threshold`): repetir la
configuración actualiza la regla existente en vez de duplicarla
(OAS-B14-1). `metric_type_exists` consulta el catálogo porque el servicio
verifica la métrica ANTES de escribir (404 `metric_type_not_found`).
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

# pylint: disable=too-many-instance-attributes,too-few-public-methods  # DTO plano

# Dominios de los CHECK de `alert_rule` (migración 0008).
ALERT_RULE_COMPARISONS = ("gt", "lt")
ALERT_RULE_SEVERITIES = ("low", "medium", "high", "critical")
ALERT_RULE_MIN_WINDOW_MINUTES = 1
ALERT_RULE_MAX_WINDOW_MINUTES = 10080  # 7 días


@dataclass(frozen=True)
class AlertRuleRecord:
    """Umbral de una métrica para una aplicación (ADR-0013)."""

    rule_id: UUID
    application_id: UUID
    metric_type_id: int
    comparison: str
    threshold: Decimal
    window_minutes: int
    min_samples: int
    cooldown_minutes: int
    severity: str
    is_active: bool = True
    # None en el alta: `created_at` lo fija el DEFAULT now() de la tabla.
    created_at: datetime | None = None


class AlertRuleRepository(Protocol):
    """Persistencia de reglas de umbral, idempotente por clave (OAS-B14-1).

    Las implementaciones reciben una AsyncSession; las mutaciones NO
    commitean (ADR-10): el servicio coordina commit/rollback.
    """

    async def list_rules(self, app_id: UUID) -> list[AlertRuleRecord]:
        """Reglas de `app_id` (activas e inactivas) por `created_at`
        ascendente, con desempate determinista por `rule_id` (OAS-B14-2)."""
        ...

    async def upsert_rule(
        self, rule: AlertRuleRecord
    ) -> tuple[AlertRuleRecord, bool]:
        """Crea la regla o actualiza la de la misma clave; devuelve la fila
        resultante y si fue alta (`True`) o actualización (`False`)."""
        ...

    async def metric_type_exists(self, metric_type_id: int) -> bool:
        """`True` si el id está en el catálogo `metric_type` (OAS-B14-1)."""
        ...
