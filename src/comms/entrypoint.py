"""Entrypoint del despachador de alertas (`intellops-comms`, ISS-B-10).

Worker sin puertos (ADR-0010): abre el engine async contra `DATABASE_URL`,
construye los proveedores de los canales que tienen destino configurado, corre
un ciclo de despacho cada `INTELLOPS_COMMS_INTERVAL_SECONDS` y se apaga
ordenadamente con SIGTERM/SIGINT (lo ya enviado quedó commiteado; la
transacción en curso se descarta y el próximo arranque la reintenta, porque la
alerta sigue Pending).

Sin secretos configurados el worker igual arranca: los canales sin destino se
avisan una vez y las alertas quedan Pending (OAS-B10-2). Un ciclo que falla
—base caída, proveedor caído— se loguea y NO mata el proceso: sin política de
reinicio externa, el próximo ciclo ES el reintento (D7, design §6).

Los imports usan el paquete `comms`: la imagen pone `src/` en `PYTHONPATH`.
"""

import asyncio
import logging
import signal
from contextlib import suppress

import httpx
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from comms.config import EMAIL, TELEGRAM, CommsSettings, get_comms_settings
from comms.dispatcher import AlertProvider, CycleSummary, Dispatcher
from comms.providers import EmailProvider, TelegramProvider
from comms.repository import SqlAlchemyCommsRepository
from comms.scheduler import CommsScheduler

logger = logging.getLogger("intellops-comms")


def build_providers(
    settings: CommsSettings, client: httpx.AsyncClient
) -> dict[str, AlertProvider]:
    """Proveedores de los canales con destino configurado (design §6).

    Un canal sin credenciales simplemente no está en el mapa: el dispatcher lo
    trata como "no disponible" y deja sus alertas en Pending (OAS-B10-2).
    """
    providers: dict[str, AlertProvider] = {}
    if settings.telegram_configured:
        providers[TELEGRAM] = TelegramProvider(
            token=settings.telegram_bot_token or "",
            destination=settings.telegram_chat_id or "",
            client=client,
            timeout=settings.delivery_timeout_seconds,
            api_base=settings.telegram_api_base,
        )
    if settings.email_configured:
        providers[EMAIL] = EmailProvider(
            host=settings.smtp_host or "",
            port=settings.smtp_port,
            destination=settings.smtp_to or "",
            sender=settings.smtp_sender,
            username=settings.smtp_user,
            password=settings.smtp_password,
            starttls=settings.smtp_starttls,
            timeout=settings.delivery_timeout_seconds,
        )
    return providers


async def run_cycle(
    sessions: async_sessionmaker,
    settings: CommsSettings,
    providers: dict[str, AlertProvider],
    notified_channels: set[str] | None = None,
) -> CycleSummary:
    """Un ciclo completo con su propia sesión y su log de resumen (design §8).

    `notified_channels` se comparte entre ciclos: un canal sin credenciales se
    avisa UNA vez por proceso, no una vez por ciclo (design §6).
    """
    async with sessions() as session:
        dispatcher = Dispatcher(
            SqlAlchemyCommsRepository(session),
            providers,
            settings.routing,
            settings.retry_policy,
            batch_size=settings.batch_size,
            notified_channels=notified_channels,
        )
        summary = await dispatcher.run_cycle()
    logger.info(
        "comms cycle claimed=%d sent=%d failed=%d",
        summary.claimed,
        summary.sent,
        summary.failed,
    )
    return summary


async def _serve(settings: CommsSettings) -> None:
    """Corre el scheduler hasta que llegue SIGTERM/SIGINT."""
    engine: AsyncEngine = create_async_engine(
        settings.async_database_url, pool_pre_ping=True
    )
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for stop_signal in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(stop_signal, stop.set)

    async with httpx.AsyncClient() as client:
        providers = build_providers(settings, client)
        notified_channels: set[str] = set()

        async def cycle() -> None:
            try:
                await run_cycle(sessions, settings, providers, notified_channels)
            except Exception:  # pylint: disable=broad-exception-caught
                # Sin política de reinicio externa, el próximo ciclo ES el
                # reintento: un error de base o de un proveedor no puede
                # matar el worker. CancelledError no entra acá (deriva de
                # BaseException): el apagado sí frena el ciclo.
                logger.exception("comms cycle failed unexpectedly")

        scheduler = asyncio.create_task(
            CommsScheduler(
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
    settings = get_comms_settings()
    logger.info(
        "comms dispatcher starting interval=%ss batch=%d channels=%s "
        "database_url=%s",
        settings.interval_seconds,
        settings.batch_size,
        ",".join(settings.configured_channels) or "none",
        # Nunca se loguea la URL cruda: puede traer credenciales.
        settings.async_database_url.split("@")[-1],
    )
    try:
        asyncio.run(_serve(settings))
    except KeyboardInterrupt:
        pass
    logger.info("comms dispatcher stopped")


if __name__ == "__main__":
    main()
