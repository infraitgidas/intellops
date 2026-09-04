from fastapi import FastAPI
from src.ml.pipeline.mock_reader import load_mock_data

app = FastAPI(title="IntellOps AI Engine Worker", version="1.0.0")


@app.on_event("startup")
async def startup_event():
    """Al arrancar el worker, intentamos leer los datos mock."""
    try:
        data = load_mock_data()
        print(f"Worker AI iniciado. Se leyeron {len(data)} registros mock.")
    except Exception as e:
        print(f"Error inicializando el worker o leyendo mocks: {e}")


@app.get("/ml/status")
async def get_status():
    """Endpoint de estado del módulo IA requerido por la API."""
    return {
        "status": "online",
        "module": "intellops-ai-engine",
        "models": {
            "isolation_forest": "standby",
            "llama_3_2_1b": "standby"
        },
        "mock_contract_valid": True
    }