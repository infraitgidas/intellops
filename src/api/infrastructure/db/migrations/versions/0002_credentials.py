"""Credenciales de acceso — columnas, índices y seed Admin (ISS-S2-01).

Agrega a lab_user la columna `password_hash` (NULL en DDL, ADR-06) y el
índice único `idx_lab_user_email`; agrega a application la columna
dormida `api_token_hash` (ADR-03) con su índice único parcial; siembra
el Admin dev/CI con UUID fijo (ADR-05, DATA-3). NO modifica 0001.

El hash del seed es argon2id precomputado de la password dev
(ADMIN_BOOTSTRAP_PASSWORD en .env.example; default en config.py):
verify('admin-dev-password', hash) == True (el salt viaja embebido).

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-12
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED_USER_ID = "9f8c5a2e-1b2c-4d5e-8f9a-0b1c2d3e4f5a"
SEED_EMAIL = "admin@intellops.local"
SEED_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$hH0jN7g+iu10ULAQCmU2lA$"
    "IucJ1e2Xsts65qYcSKoL9Zk1Z2zmQO2yDwQbxfQ2+qw"
)


def upgrade() -> None:
    op.execute("ALTER TABLE lab_user ADD COLUMN password_hash VARCHAR(255)")
    op.execute("CREATE UNIQUE INDEX idx_lab_user_email ON lab_user(email)")
    op.execute("ALTER TABLE application ADD COLUMN api_token_hash VARCHAR(64)")
    op.execute(
        "CREATE UNIQUE INDEX idx_application_api_token_hash "
        "ON application(api_token_hash) WHERE api_token_hash IS NOT NULL"
    )
    op.execute(
        f"""
        INSERT INTO lab_user (user_id, name, email, role_id, is_active, password_hash)
        VALUES (
            '{SEED_USER_ID}',
            'Admin',
            '{SEED_EMAIL}',
            (SELECT role_id FROM user_role WHERE name = 'Admin'),
            TRUE,
            '{SEED_PASSWORD_HASH}'
        )
        """
    )


def downgrade() -> None:
    # Orden DATA-4: seed → índice parcial → columna → índice email → columna.
    # Seguro: user_favorite_metric CASCADE, user_session SET NULL.
    op.execute(f"DELETE FROM lab_user WHERE user_id = '{SEED_USER_ID}'")
    op.execute("DROP INDEX idx_application_api_token_hash")
    op.execute("ALTER TABLE application DROP COLUMN api_token_hash")
    op.execute("DROP INDEX idx_lab_user_email")
    op.execute("ALTER TABLE lab_user DROP COLUMN password_hash")
