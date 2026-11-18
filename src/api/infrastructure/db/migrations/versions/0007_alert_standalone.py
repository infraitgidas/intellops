"""Alerta independiente de la anomalía e índices del read path (ISS-B-03, ADR-0012).

En la v1 las alertas las crea el motor de reglas de umbral (B.14), sin
detección ML (D1): no hay anomalía ni modelo detrás. El DDL 0001 exigía
`alert.anomaly_id` NOT NULL (y `anomaly.model_id` NOT NULL), no guardaba el
tenant ni la severidad y no tenía cuándo se creó la alerta. Esta migración:

- agrega `application_id` (tenant, FK a `application`, ON DELETE RESTRICT),
  `severity` (TEXT + `ck_alert_severity`: low/medium/high/critical) y
  `created_at` (TIMESTAMPTZ NOT NULL, default `now()`);
- relaja `anomaly_id` (una alerta de umbral no tiene anomalía; una de ML, en
  M3, sí), `recipient` y `channel_id` (el destino lo completa el dispatcher
  de B.10 al despachar, desde su configuración);
- crea los índices del read path newest-first: `idx_alert_app_created` para
  `GET /alerts` e `idx_anomaly_app_timestamp` para `GET /anomalies`.

Las columnas propias de las reglas (umbral, valor observado) las agrega B.14
en su migración, que cuelga de esta (`down_revision = "0007"`).

Como 0004, no hay backfill posible (el tenant y la severidad de una alerta
existente no se pueden derivar): si `alert` tiene filas, upgrade y downgrade
abortan con un mensaje claro en lugar del error crudo del NOT NULL.

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-08
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _assert_alert_empty(direction: str) -> None:
    """Aborta si ALERT tiene filas (no hay backfill/restauración posible)."""
    count = op.get_bind().exec_driver_sql("SELECT count(*) FROM alert").scalar()
    if count:
        raise RuntimeError(
            f"0007 {direction} abortado: alert tiene {count} fila(s) y no "
            "existe forma segura de derivar application_id y severity (ni de "
            "restaurar los NOT NULL de anomaly_id, recipient y channel_id). "
            "Vaciar alert antes de continuar."
        )


def upgrade() -> None:
    _assert_alert_empty("upgrade")
    op.execute(
        """
        ALTER TABLE alert
            ADD COLUMN application_id UUID NOT NULL,
            ADD COLUMN severity TEXT NOT NULL,
            ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            ALTER COLUMN anomaly_id DROP NOT NULL,
            ALTER COLUMN recipient DROP NOT NULL,
            ALTER COLUMN channel_id DROP NOT NULL,
            ADD CONSTRAINT ck_alert_severity
                CHECK (severity IN ('low', 'medium', 'high', 'critical')),
            ADD CONSTRAINT fk_alert_application
                FOREIGN KEY (application_id)
                REFERENCES application(app_id)
                ON DELETE RESTRICT
        """
    )
    op.execute(
        "CREATE INDEX idx_alert_app_created ON alert(application_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX idx_anomaly_app_timestamp "
        "ON anomaly(application_id, timestamp DESC)"
    )


def downgrade() -> None:
    _assert_alert_empty("downgrade")
    op.execute("DROP INDEX idx_anomaly_app_timestamp")
    op.execute("DROP INDEX idx_alert_app_created")
    op.execute(
        """
        ALTER TABLE alert
            DROP CONSTRAINT fk_alert_application,
            DROP CONSTRAINT ck_alert_severity,
            DROP COLUMN created_at,
            DROP COLUMN severity,
            DROP COLUMN application_id,
            ALTER COLUMN anomaly_id SET NOT NULL,
            ALTER COLUMN recipient SET NOT NULL,
            ALTER COLUMN channel_id SET NOT NULL
        """
    )
