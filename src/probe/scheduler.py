"""Scheduler de la sonda: corrida periódica a intervalo configurable (S1).

El ciclo se inyecta como callable async sin argumentos, así el scheduler solo
se ocupa del ritmo: nunca duerme después de la última corrida, porque un
`max_cycles` finito debe terminar exactamente con esa cantidad de corridas.

El ritmo se ancla a `time.monotonic()`: la espera es el intervalo MENOS lo que
duró el ciclo, así el período real es `interval_seconds` y no intervalo +
duración del ciclo. Sin esa compensación, con un intervalo de 60 s y buckets de
agregación de 60 s, algunos buckets quedarían con 0 muestras y otros con 2.
"""

import asyncio
import time
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
        """Ejecuta `cycle` y espera lo que falta del intervalo entre corridas.

        `max_cycles=None` corre indefinidamente (`python -m probe`); con un
        entero corre exactamente esa cantidad de ciclos y no duerme al final.

        Si un ciclo dura más que el intervalo, la espera se recorta a cero
        (nunca negativa) y el próximo ciclo arranca de inmediato.
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
                # vez de arrastrar el atraso. Sin esto `next_tick` queda cada
                # vez más atrás y la espera se queda en 0 para siempre: un
                # bucle sin pausa en vez de recuperar el ritmo.
                next_tick = time.monotonic()
                wait = 0.0
            await asyncio.sleep(wait)
