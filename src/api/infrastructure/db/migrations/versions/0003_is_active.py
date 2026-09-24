"""Activación/desactivación de aplicaciones — columna is_active (ISS-S2-02).

Agrega a application la columna `is_active BOOLEAN NOT NULL DEFAULT TRUE`
(ADR-20: NOT NULL + DEFAULT TRUE, aditiva y compatible con filas
existentes). NO modifica 0001/0002 ni el índice único parcial
`idx_application_api_token_hash` (DATA-7). Downgrade: DROP COLUMN (DATA-8).

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-23
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE application "
        "ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE application DROP COLUMN is_active")
