"""Entrypoint de la sonda: `python -m probe` (S1, S3, D5).

Un solo proceso, un solo origen: carga `ProbeSettings`, corre un ciclo
(probe -> build_batch -> send_batch) con un `httpx.AsyncClient` compartido y
repite cada `PROBE_INTERVAL_SECONDS` hasta que lo detengan.
"""

import asyncio
import logging

import httpx

from probe.config import ProbeSettings
from probe.ingest import build_batch, sanitize_target_url, send_batch
from probe.runner import ProbeResult, run_probe
from probe.scheduler import ProbeScheduler

logger = logging.getLogger(__name__)


def _log_result(result: ProbeResult, ingest_status: int | None) -> None:
    """Registra la corrida: outcome, status medido, latencia e ingesta (S1).

    `ingest_status=None` significa que la ingesta nunca respondió: la medición
    se registra igual, porque ya ocurrió y es la evidencia de la corrida.
    """
    logger.info(
        "probe outcome=%s target=%s http_status=%s latency_ms=%s ingest_status=%s",
        result.outcome.value,
        sanitize_target_url(result.target_url),
        result.status_code,
        result.latency_ms,
        "unknown" if ingest_status is None else ingest_status,
    )


def _log_startup(settings: ProbeSettings) -> None:
    """Registra la configuración de arranque con las URLs saneadas.

    `ingest_base_url` es tan configurable como el target y puede traer
    credenciales en el userinfo o un token en el query string: se loguea con el
    mismo saneo, no cruda.
    """
    logger.info(
        "probe starting target=%s interval=%ss ingest=%s",
        sanitize_target_url(settings.probe_target_url),
        settings.probe_interval_seconds,
        sanitize_target_url(settings.ingest_base_url),
    )


async def run_cycle(settings: ProbeSettings, client: httpx.AsyncClient) -> ProbeResult:
    """Una corrida completa: medir, armar el batch y enviarlo por ingesta.

    Si el envío falla, la medición YA ocurrió: se registra con
    `ingest_status=unknown` antes de propagar el error, para que un fallo de
    ingesta no borre la evidencia de la corrida.
    """
    result = await run_probe(
        settings.probe_target_url,
        timeout_seconds=settings.probe_timeout_seconds,
        client=client,
    )
    payload = build_batch(
        result,
        api_key=settings.probe_api_key,
        session_id=None,  # D4: sesión sintética por tenant y target.
        application_id=settings.probe_application_id,
    )
    try:
        ingest_status = await send_batch(
            base_url=settings.ingest_base_url,
            api_key=settings.probe_api_key,
            payload=payload,
            client=client,
            timeout_seconds=settings.probe_timeout_seconds,
        )
    except httpx.HTTPError:
        _log_result(result, None)
        raise
    _log_result(result, ingest_status)
    return result


async def _serve(settings: ProbeSettings) -> None:
    """Crea el cliente compartido y corre el scheduler indefinidamente (S1)."""
    async with httpx.AsyncClient(timeout=settings.probe_timeout_seconds) as client:

        async def cycle() -> None:
            try:
                await run_cycle(settings, client)
            except httpx.HTTPError as exc:
                # La corrida nunca pierde el ritmo por un fallo de ingesta: se
                # registra y el próximo intervalo vuelve a intentar.
                logger.warning("probe ingest failed: %s", exc)
            except Exception:  # pylint: disable=broad-exception-caught
                # Un error inesperado (p. ej. en build_batch) tampoco puede
                # matar el proceso: no hay política de reinicio externa, el
                # próximo ciclo ES el reintento. Es deliberadamente amplio y no
                # se re-lanza; CancelledError no entra acá (deriva de
                # BaseException): la cancelación sí frena la sonda.
                logger.exception("probe cycle failed unexpectedly")

        await ProbeScheduler(
            interval_seconds=settings.probe_interval_seconds,
            cycle=cycle,
        ).run()


def main() -> None:
    """Punto de entrada del módulo ejecutable."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    settings = ProbeSettings()
    _log_startup(settings)
    try:
        asyncio.run(_serve(settings))
    except KeyboardInterrupt:
        logger.info("probe stopped")


if __name__ == "__main__":
    main()
