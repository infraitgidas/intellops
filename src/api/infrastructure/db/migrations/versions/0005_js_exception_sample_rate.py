"""Agrega sample_rate a js_exception (ISS-B-15, OD-03).

La tasa de muestreo de excepciones viaja opcional desde el agente
(`JsExceptionEvent.sample_rate`) y se persiste para poder ponderar el análisis
por `1 / sample_rate` (§5 del contrato del agente). Columna nullable: las filas
existentes y los clientes que no reportan la tasa quedan en NULL, sin backfill.
No cambia `required` ni el envelope.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-30
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE js_exception ADD COLUMN sample_rate DOUBLE PRECISION"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE js_exception DROP COLUMN sample_rate")
