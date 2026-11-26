"""Entrypoint del motor de reglas (`intellops-ai-engine`, ISS-B-14).

Worker sin puertos (ADR-0010): abre el engine async contra `DATABASE_URL`,
corre `RulesEngine.run_cycle()` cada `INTELLOPS_RULES_INTERVAL_SECONDS` y se
apaga ordenadamente con SIGTERM/SIGINT (una alerta ya creada queda
commiteada; la transacción en curso se descarta y el próximo arranque la
reintenta).

Los imports usan el paquete `ml.rules`: el contenedor de test y el runtime de
`intellops-core` ponen `src/` en `PYTHONPATH`. El Dockerfile del worker aún
copia solo este archivo (pendiente de B.14 en infraestructura), así que el
empaquetado de la imagen se reporta como riesgo del cambio.
"""

import asyncio
import logging
import signal
from contextlib import suppress

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from ml.rules.config import RulesSettings, get_rules_settings
from ml.rules.engine import CycleSummary, RulesEngine
from ml.rules.repository import SqlAlchemyRulesRepository
from ml.rules.scheduler import RuleScheduler

logger = logging.getLogger("intellops-rules")


async def run_cycle(
    sessions: async_sessionmaker,
) -> CycleSummary:
    """Un ciclo completo con su propia sesión y su log de resumen (§10)."""
    async with sessions() as session:
        summary = await RulesEngine(SqlAlchemyRulesRepository(session)).run_cycle()
    logger.info(
        "rules cycle evaluated=%d fired=%d cooled=%d insufficient=%d ok=%d",
        summary.evaluated,
        summary.fired,
        summary.cooled,
        summary.insufficient,
        summary.ok,
    )
    return summary


async def _serve(settings: RulesSettings) -> None:
    """Corre el scheduler hasta que llegue SIGTERM/SIGINT."""
    engine: AsyncEngine = create_async_engine(
        settings.async_database_url, pool_pre_ping=True
    )
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for stop_signal in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(stop_signal, stop.set)

    async def cycle() -> None:
        try:
            await run_cycle(sessions)
        except Exception:  # pylint: disable=broad-exception-caught
            # Sin política de reinicio externa, el próximo ciclo ES el
            # reintento: un error de base no puede matar el worker.
            # CancelledError no entra acá (deriva de BaseException).
            logger.exception("rules cycle failed unexpectedly")

    scheduler = asyncio.create_task(
        RuleScheduler(
            interval_seconds=settings.interval_seconds,
            cycle=cycle,
        ).run()
    )
    stopper = asyncio.create_task(stop.wait())
    try:
        await asyncio.wait(
            {scheduler, stopper}, return_when=asyncio.FIRST_COMPLETED
        )
    finally:
        stopper.cancel()
        scheduler.cancel()
        with suppress(asyncio.CancelledError):
            await scheduler
        with suppress(asyncio.CancelledError):
            await stopper
        await engine.dispose()


def main() -> None:
    """Punto de entrada del worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    settings = get_rules_settings()
    logger.info(
        "rules engine starting interval=%ss database_url=%s",
        settings.interval_seconds,
        # Nunca se loguea la URL cruda: puede traer credenciales.
        settings.async_database_url.split("@")[-1],
    )
    try:
        asyncio.run(_serve(settings))
    except KeyboardInterrupt:
        pass
    logger.info("rules engine stopped")


if __name__ == "__main__":
    main()
