"""IntellOps Comms — placeholder.

Dispatcher de alertas (intellops-comms). Sin lógica de negocio todavía;
el polling de ALERT y el envío a Telegram/Email se agregan en issues
posteriores. Mantiene el contenedor vivo para validar el stack de
docker-compose.
"""

import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("intellops-comms")

if __name__ == "__main__":
    logger.info("intellops-comms iniciado (placeholder)")
    while True:
        time.sleep(3600)
