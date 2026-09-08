"""IntellOps API — FastAPI Backend.

Sistema de Observabilidad Predictiva UX-Céntrica + AI/LLM Open-Source.
PI+D+i | Grupo GIDAS | UTN FrLP | Equipo InfraIT
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .infrastructure.db.session import check_connection, dispose_engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Libera el pool de conexiones a la DB al apagar la app."""
    yield
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
