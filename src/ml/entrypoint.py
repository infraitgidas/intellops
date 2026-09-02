"""IntellOps AI Engine — placeholder.

Worker aislado (intellops-ai-engine). Sin lógica de negocio todavía;
detección de anomalías (Isolation Forest) e inferencia LLM se agregan
en issues posteriores. Mantiene el contenedor vivo para validar el
stack de docker-compose.
"""

import logging
import time

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger("intellops-ai-engine")

if __name__ == "__main__":
    logger.info("intellops-ai-engine iniciado (placeholder, sin tráfico web)")
    while True:
        time.sleep(3600)
