"""Scheduler de la sonda: corrida periódica a intervalo configurable (S1).

El ciclo se inyecta como callable async sin argumentos, así el scheduler solo
se ocupa del ritmo: nunca duerme después de la última corrida, porque un
`max_cycles` finito debe terminar exactamente con esa cantidad de corridas.
"""

import asyncio
from collections.abc import Awaitable, Callable


# pylint: disable=too-few-public-methods  # el scheduler expone solo `run`
class ProbeScheduler:
    """Repite un ciclo de sonda cada `interval_seconds` (S1)."""

    def __init__(
        self,
        interval_seconds: float,
        cycle: Callable[[], Awaitable[None]],
    ) -> None:
        self.interval_seconds = interval_seconds
        self._cycle = cycle

    async def run(self, max_cycles: int | None = None) -> None:
        """Ejecuta `cycle` y espera el intervalo entre corridas.

        `max_cycles=None` corre indefinidamente (`python -m probe`); con un
        entero corre exactamente esa cantidad de ciclos y no duerme al final.
        """
        cycles = 0
        while max_cycles is None or cycles < max_cycles:
            await self._cycle()
            cycles += 1
            if max_cycles is not None and cycles >= max_cycles:
                return
            await asyncio.sleep(self.interval_seconds)
