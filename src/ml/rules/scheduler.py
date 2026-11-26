"""Scheduler del motor de reglas: ciclo periódico a intervalo configurable.

Réplica deliberada de `src/probe/scheduler.py` (design §10): ADR-0010 prohíbe
cross-imports entre contenedores, así que son las mismas ~25 líneas con sus
propios tests en lugar de acoplar `ai-engine` a `probe`.

Semántica (idéntica a la sonda):

- el ciclo se inyecta como callable async sin argumentos;
- nunca duerme después de la última corrida, así `max_cycles` finito termina
  exactamente con esa cantidad de corridas;
- la espera es el intervalo MENOS la duración del ciclo, anclada a
  `time.monotonic()`;
- si un ciclo se pasa del intervalo, la espera se recorta a cero y el reloj
  se resincroniza en vez de arrastrar el atraso (un bucle sin pausa).
"""

import asyncio
import time
from collections.abc import Awaitable, Callable


# pylint: disable=too-few-public-methods  # el scheduler expone solo `run`
class RuleScheduler:
    """Repite `RulesEngine.run_cycle()` cada `interval_seconds` (design §10)."""

    def __init__(
        self,
        interval_seconds: float,
        cycle: Callable[[], Awaitable[None]],
    ) -> None:
        self.interval_seconds = interval_seconds
        self._cycle = cycle

    async def run(self, max_cycles: int | None = None) -> None:
        """Ejecuta `cycle` y espera lo que falta del intervalo entre corridas.

        `max_cycles=None` corre indefinidamente (worker); con un entero corre
        exactamente esa cantidad de ciclos y no duerme al final (tests).
        """
        cycles = 0
        next_tick = time.monotonic()
        while max_cycles is None or cycles < max_cycles:
            await self._cycle()
            cycles += 1
            if max_cycles is not None and cycles >= max_cycles:
                return
            next_tick += self.interval_seconds
            wait = next_tick - time.monotonic()
            if wait < 0.0:
                # El ciclo se pasó del intervalo: se resincroniza el reloj en
                # vez de arrastrar el atraso (ver docstring del módulo).
                next_tick = time.monotonic()
                wait = 0.0
            await asyncio.sleep(wait)
