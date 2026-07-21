"""IntellOps API — FastAPI Backend.

Sistema de Observabilidad Predictiva UX-Céntrica + AI/LLM Open-Source.
PI+D+i | Grupo GIDAS | UTN FrLP | Equipo InfraIT
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="IntellOps API",
    description="Observabilidad predictiva con ML y GenIA para infraestructura IT",
    version="0.1.0",
    contact={
        "name": "Equipo InfraIT — GIDAS UTN FrLP",
        "url": "https://github.com/infraitgidas/intellops",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    },
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
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0", "service": "intellops-api"}


@app.get("/ready")
async def readiness():
    """Readiness check — verifica que las dependencias estén listas."""
    return {"status": "ready"}
