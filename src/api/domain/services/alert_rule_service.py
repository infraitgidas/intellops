"""AlertRuleService — evalúa las reglas de umbral de una aplicación (ISS-B-14).

Por cada regla efectiva y habilitada: observa la ventana `[now - window, now)`,
decide con `breaches` y, si no hay cooldown activo, inserta la alerta Pending.
El cooldown se consulta en `alert` (sin estado en memoria: sobrevive a un
reinicio) con `created_at > now - cooldown`: una alerta creada exactamente hace
`cooldown` ya salió del cooldown (DT-2). `created_at = now` lo fija el servicio
(DT-8) para que el reloj inyectado sea el mismo en la ventana y en el cooldown.

Un error al evaluar una regla se registra y no impide evaluar las demás
(AR-8): cada regla corre en `rule_transaction` (savepoint), así un error SQL
no aborta la transacción de la aplicación ni descarta las alertas ya creadas.
El servicio no hace commit: la transacción es del evaluador.
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from api.domain.repositories.alert_rule_repository import (
    AlertRuleRepository,
    NewAlert,
)
from api.domain.services.alert_rules import (
    AlertRule,
    breaches,
    build_message,
    effective_rules,
)

# pylint: disable=too-few-public-methods  # caso de uso con un solo método público

logger = logging.getLogger(__name__)


class AlertRuleService:
    """Crea las alertas Pending de las reglas que disparan."""

    def __init__(self, repository: AlertRuleRepository) -> None:
        self._repository = repository

    async def evaluate_application(self, app_id: UUID, now: datetime) -> list[NewAlert]:
        """Evalúa las reglas de `app_id` en `now`; devuelve las alertas creadas."""
        rules = effective_rules(await self._repository.list_rule_overrides(app_id))
        created: list[NewAlert] = []
        for rule in rules:
            try:
                async with self._repository.rule_transaction():
                    alert = await self._evaluate_rule(app_id, rule, now)
            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception(
                    "Falló la regla %s de la aplicación %s", rule.rule_id, app_id
                )
                continue
            if alert is not None:
                created.append(alert)
        return created

    async def _evaluate_rule(
        self, app_id: UUID, rule: AlertRule, now: datetime
    ) -> NewAlert | None:
        start = now - timedelta(seconds=rule.window_seconds)
        observation = await self._repository.observe(app_id, rule.rule_id, start, now)
        if not breaches(rule, observation.value, observation.samples):
            return None
        since = now - timedelta(seconds=rule.cooldown_seconds)
        if await self._repository.has_recent_alert(app_id, rule.rule_id, since):
            return None
        alert = NewAlert(
            application_id=app_id,
            rule_id=rule.rule_id,
            severity=rule.severity,
            threshold=rule.threshold,
            observed_value=observation.value,
            message=build_message(rule, observation.value),
            created_at=now,
        )
        await self._repository.create_alert(alert)
        return alert
