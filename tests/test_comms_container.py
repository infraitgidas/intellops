"""Ancla el empaquetado, el arranque y el despliegue del despachador (ISS-B-10).

`intellops-comms` pasa de placeholder a worker real: importa `comms.*` como
paquete top-level, abre conexión a `DATABASE_URL` y despacha alertas. La
imagen copiaba solo `entrypoint.py`, así que con el dispatcher real habría
arrancado con `ModuleNotFoundError: No module named 'comms.dispatcher'`.

Además el compose tiene que poder levantar SIN secretos: los destinos y las
credenciales se pasan con default vacío (`${VAR:-}`) y el worker trata la
ausencia como "canal no disponible", nunca como un fallo (OAS-B10-2).
"""

from pathlib import Path

import pytest

DOCKERFILE = Path("src/comms/Dockerfile")
ENTRYPOINT = Path("src/comms/entrypoint.py")
COMPOSE = Path("docker-compose.yml")
ENV_EXAMPLE = Path(".env.example")

# Variables que el worker consume y que el compose le pasa al contenedor.
COMMS_ENV_VARS = (
    "INTELLOPS_COMMS_INTERVAL_SECONDS",
    "INTELLOPS_COMMS_BATCH_SIZE",
    "INTELLOPS_COMMS_CHANNEL_CRITICAL",
    "INTELLOPS_COMMS_CHANNEL_HIGH",
    "INTELLOPS_COMMS_CHANNEL_MEDIUM",
    "INTELLOPS_COMMS_CHANNEL_LOW",
    "INTELLOPS_COMMS_RETRY_ATTEMPTS",
    "INTELLOPS_COMMS_RETRY_BASE_SECONDS",
    "INTELLOPS_COMMS_RETRY_FACTOR",
    "INTELLOPS_COMMS_RETRY_BUDGET_SECONDS",
    "INTELLOPS_COMMS_DELIVERY_TIMEOUT_SECONDS",
    "INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN",
    "INTELLOPS_COMMS_TELEGRAM_CHAT_ID",
    "INTELLOPS_COMMS_SMTP_HOST",
    "INTELLOPS_COMMS_SMTP_PORT",
    "INTELLOPS_COMMS_SMTP_USER",
    "INTELLOPS_COMMS_SMTP_PASSWORD",
    "INTELLOPS_COMMS_SMTP_FROM",
    "INTELLOPS_COMMS_SMTP_TO",
    "INTELLOPS_COMMS_SMTP_STARTTLS",
)


def _comms_service_block() -> str:
    """Bloque YAML del servicio `intellops-comms` dentro del compose."""
    content = COMPOSE.read_text(encoding="utf-8")
    start = content.index("\n  intellops-comms:") + 1
    rest = content[start:]
    end = rest.find("\n  intellops-")
    return rest if end == -1 else rest[:end]


def test_image_packages_the_full_source_tree():
    """La imagen copia `src/` y expone `comms.*` como top-level (PYTHONPATH)."""
    content = DOCKERFILE.read_text(encoding="utf-8")
    assert "COPY src/ src/" in content
    assert "ENV PYTHONPATH=/app/src" in content


def test_image_installs_the_shared_runtime_requirements():
    """Sin dependencias nuevas: las del core ya traen SQLAlchemy, asyncpg,
    httpx y pydantic-settings (D9)."""
    content = DOCKERFILE.read_text(encoding="utf-8")
    assert "COPY src/api/requirements.txt ." in content
    assert "pip install --no-cache-dir -r requirements.txt" in content


def test_image_runs_the_comms_entrypoint_as_a_module():
    """El CMD arranca el worker como módulo y no expone puertos (ADR-0010)."""
    content = DOCKERFILE.read_text(encoding="utf-8")
    assert 'CMD ["python", "-m", "comms.entrypoint"]' in content
    assert "EXPOSE" not in content


def test_entrypoint_imports_the_comms_package_as_top_level():
    """El entrypoint importa `comms.*`, no `src.comms.*` (path del runtime)."""
    source = ENTRYPOINT.read_text(encoding="utf-8")
    assert "from comms." in source
    assert "src.comms" not in source


def test_entrypoint_shuts_down_on_sigterm_and_sigint():
    """El worker se apaga ordenadamente con SIGTERM/SIGINT."""
    source = ENTRYPOINT.read_text(encoding="utf-8")
    assert "SIGTERM" in source
    assert "SIGINT" in source


def test_entrypoint_survives_a_failed_cycle():
    """Un ciclo fallido no mata el proceso: sin bleeder externo el próximo
    ciclo ES el reintento (design §6, D7: nada de crash-loop)."""
    source = ENTRYPOINT.read_text(encoding="utf-8")
    assert "broad-exception-caught" in source


def test_compose_passes_the_comms_variables_with_empty_defaults():
    """El stack levanta sin secretos: cada variable llega con default vacío."""
    block = _comms_service_block()
    for name in COMMS_ENV_VARS:
        assert f"${{{name}:-}}" in block, name
    assert "${POSTGRES_USER:-intellops}" in block


def test_comms_service_has_no_published_ports():
    """`intellops-comms` no es alcanzable desde el host (ADR-0010)."""
    block = _comms_service_block()
    assert "\n    ports:" not in block
    assert "mem_limit: 150m" in block


def test_env_example_lists_the_new_variables_when_present():
    """`.env.example` lista las variables del worker, todas vacías.

    El archivo lo escribe el orquestador en esta entrega (la política de
    seguridad del worker bloquea las rutas `.env*`); si todavía no está
    actualizado, el test se salta y el faltante se reporta en la entrega.
    """
    content = ENV_EXAMPLE.read_text(encoding="utf-8")
    if "INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN" not in content:
        pytest.skip(".env.example pendiente de actualizar por el orquestador")
    for name in COMMS_ENV_VARS:
        assert f"\n{name}=" in content, name
    for name in (
        "INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN",
        "INTELLOPS_COMMS_TELEGRAM_CHAT_ID",
        "INTELLOPS_COMMS_SMTP_HOST",
        "INTELLOPS_COMMS_SMTP_USER",
        "INTELLOPS_COMMS_SMTP_PASSWORD",
        "INTELLOPS_COMMS_SMTP_TO",
    ):
        assert f"\n{name}=\n" in content, name
