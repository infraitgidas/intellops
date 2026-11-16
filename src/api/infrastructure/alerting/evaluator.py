"""AlertEvaluator — tarea periódica que evalúa las reglas de umbral (ISS-B-14).

Corre dentro del lifespan de la API. El loop duerme `interval_seconds` y recién
después evalúa (DT-10): no toca la base durante el startup. Cada ciclo lista las
aplicaciones activas en una sesión y evalúa cada una con sesión y transacción
propias (DT-5): commit si todo salió bien; ante una excepción, rollback + log y
se sigue con la próxima aplicación. Tras un error SQL Postgres deja la
transacción abortada, así que no se asume que el servicio propaga los errores.

Worker único (ya vigente para la cola de ingesta): sin carrera entre el chequeo
de cooldown y el insert.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from api.domain.services.alert_rule_service import AlertRuleService

logger = logging.getLogger(__name__)


class AlertEvaluator:
    """Evalúa periódicamente las reglas de todas las aplicaciones activas."""

    def __init__(
        self,
        session_factory: Callable[[], Any],
        repository_factory: Callable[[Any], Any],
        interval_seconds: float,
    ) -> None:
        self._session_factory = session_factory
        self._repository_factory = repository_factory
        self._interval_seconds = interval_seconds
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        """Lanza el loop como tarea asyncio (idempotente)."""
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Cancela el loop y espera a que termine (sin propagar la cancelación)."""
        if self._task is None:
            return
        self._task.cancel()
        await asyncio.gather(self._task, return_exceptions=True)

    async def evaluate_once(self, now: datetime) -> None:
        """Un ciclo: evalúa cada aplicación activa con su propia transacción."""
        async with self._session_factory() as session:
            app_ids = await self._repository_factory(
                session
            ).list_active_application_ids()
        for app_id in app_ids:
            async with self._session_factory() as session:
                try:
                    service = AlertRuleService(self._repository_factory(session))
                    await service.evaluate_application(app_id, now)
                    await session.commit()
                except Exception:  # pylint: disable=broad-exception-caught
                    await session.rollback()
                    logger.exception("Falló la evaluación de la aplicación %s", app_id)

    async def _run(self) -> None:
        while True:
            await asyncio.sleep(self._interval_seconds)
            try:
                await self.evaluate_once(datetime.now(timezone.utc))
            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception("Falló el ciclo de evaluación de reglas")
