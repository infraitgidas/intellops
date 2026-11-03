"""Siembra la métrica AVAILABILITY en el catálogo (ISS-B-13, B.13/D1).

La sonda HTTP mínima de disponibilidad reporta una métrica por ejecución por el
mismo camino de ingesta RUM: `AVAILABILITY` con unidad `count` y valor 1
(disponible) o 0 (no disponible), de modo que `AVG(value)` por bucket en
`GET /metrics/query` sea directamente la razón de uptime.

El catálogo `metric_type` se siembra en la migración `0001` y el repositorio de
ingesta resuelve el tipo por nombre, así que el tipo nuevo solo necesita su
fila. Los cinco tipos originales no se tocan.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-03
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO metric_type (name, description) VALUES
            ('AVAILABILITY', 'Disponibilidad medida por la sonda HTTP (1 disponible, 0 no disponible)')
        ON CONFLICT (name) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM metric_type WHERE name = 'AVAILABILITY'")
