"""IntellOps API — FastAPI Backend.

Sistema de Observabilidad Predictiva UX-Céntrica + AI/LLM Open-Source.
PI+D+i | Grupo GIDAS | UTN FrLP | Equipo InfraIT
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import get_settings
from api.domain.exceptions import DomainError
from api.infrastructure.db.repositories.sqlalchemy_ingest_repository import (
    SQLAlchemyIngestRepository,
)
from api.infrastructure.db.session import check_connection, dispose_engine
from api.infrastructure.ingest.counters import IngestCounters
from api.infrastructure.ingest.queue import AsyncioIngestQueue
from api.infrastructure.security.api_keys import ApiKeyRedactionFilter
from api.presentation.errors import (
    domain_error_handler,
    validation_error_handler,
)
from api.presentation.routers import applications, auth, telemetry, users

# ADR-23: redacción global de API keys (IAUTH-4) — el plaintext de una key
# de ingesta nunca aparece en access logs ni tracebacks.
logging.getLogger().addFilter(ApiKeyRedactionFilter())


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Crea la cola de ingesta + workers al startup; al shutdown drena con
    timeout acotado y libera el pool (RUM-7, DD-6).

    La cola es por proceso: el runtime DEBE quedar en un único worker uvicorn
    (CMD actual) para no fragmentarla (RUM-5, R6).
    """
    settings = get_settings()
    counters = IngestCounters()
    queue = AsyncioIngestQueue(
        maxsize=settings.ingest_queue_maxsize,
        worker_count=settings.ingest_workers,
        repository_factory=SQLAlchemyIngestRepository,
        counters=counters,
    )
    await queue.start()
    _app.state.ingest_queue = queue
    _app.state.ingest_counters = counters
    yield
    # RUM-7/D6: close() deja de aceptar (503) → join(timeout) drena →
    # lo no persistido se loguea → dispose_engine() al final.
    await queue.close()
    await queue.join(timeout=settings.ingest_shutdown_timeout)
    await dispose_engine()


app = FastAPI(
    title="IntellOps API",
    description="Observabilidad predictiva con ML y GenIA para infra IT",
    version="0.1.0",
    contact={
        "name": "Equipo InfraIT — GIDAS UTN FrLP",
        "url": "https://github.com/infraitgidas/intellops",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    },
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(DomainError, domain_error_handler)
# D5: 422→400 scoped a /telemetry/* (envelope de ingesta); resto conserva 422.
app.add_exception_handler(RequestValidationError, validation_error_handler)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(applications.router)
app.include_router(telemetry.router)


@app.get("/health")
async def health():
    """Health check endpoint — verifica conexión a la base de datos."""
    db_connected = await check_connection()
    payload = {
        "status": "ok" if db_connected else "error",
        "version": "0.1.0",
        "service": "intellops-api",
        "database": "connected" if db_connected else "disconnected",
    }
    if not db_connected:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)
    return payload


@app.get("/ready")
async def readiness():
    """Readiness check — verifica que las dependencias estén listas."""
    return {"status": "ready"}
