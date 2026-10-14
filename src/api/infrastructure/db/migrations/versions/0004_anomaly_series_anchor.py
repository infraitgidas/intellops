"""Ancla ANOMALY a la serie/bucket en lugar de metric_id (ISS-S3-04).

M4: el dataset operativo para ML es agregado por (application_id,
metric_type_id, bucket), no por RUM_METRIC individual. Reemplaza
`anomaly.metric_id` (FK a rum_metric) por la clave de serie + bucket y agrega
un índice único (serie, bucket, modelo) para reproceso idempotente.

No hay backfill posible (metric_id -> serie/bucket no es derivable de forma
confiable): si `anomaly` tiene filas, upgrade y downgrade abortan.
`timestamp` se mantiene como instante de detección.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-14
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _assert_anomaly_empty(direction: str) -> None:
    """Aborta si ANOMALY tiene filas (no hay backfill/restauración posible)."""
    count = op.get_bind().exec_driver_sql("SELECT count(*) FROM anomaly").scalar()
    if count:
        raise RuntimeError(
            f"0004 {direction} abortado: anomaly tiene {count} fila(s) y no "
            "existe mapeo seguro metric_id <-> serie/bucket. Vaciar anomaly "
            "(y alert) antes de continuar."
        )


def upgrade() -> None:
    _assert_anomaly_empty("upgrade")
    op.execute("ALTER TABLE anomaly DROP CONSTRAINT fk_anomaly_metric")
    op.execute("ALTER TABLE anomaly DROP COLUMN metric_id")
    op.execute(
        """
        ALTER TABLE anomaly
            ADD COLUMN application_id UUID NOT NULL,
            ADD COLUMN metric_type_id SMALLINT NOT NULL,
            ADD COLUMN bucket_start TIMESTAMPTZ NOT NULL,
            ADD COLUMN bucket_seconds INTEGER NOT NULL,
            ADD CONSTRAINT ck_anomaly_bucket_seconds
                CHECK (bucket_seconds >= 60),
            ADD CONSTRAINT ck_anomaly_bucket_aligned
                CHECK ((EXTRACT(EPOCH FROM bucket_start)::bigint
                        % bucket_seconds) = 0),
            ADD CONSTRAINT fk_anomaly_application
                FOREIGN KEY (application_id)
                REFERENCES application(app_id)
                ON DELETE RESTRICT,
            ADD CONSTRAINT fk_anomaly_metric_type
                FOREIGN KEY (metric_type_id)
                REFERENCES metric_type(metric_type_id)
                ON DELETE RESTRICT
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX idx_anomaly_series_bucket_model ON anomaly("
        "application_id, metric_type_id, bucket_start, bucket_seconds, model_id)"
    )


def downgrade() -> None:
    _assert_anomaly_empty("downgrade")
    op.execute("DROP INDEX idx_anomaly_series_bucket_model")
    op.execute(
        """
        ALTER TABLE anomaly
            DROP CONSTRAINT fk_anomaly_metric_type,
            DROP CONSTRAINT fk_anomaly_application,
            DROP CONSTRAINT ck_anomaly_bucket_aligned,
            DROP CONSTRAINT ck_anomaly_bucket_seconds,
            DROP COLUMN bucket_seconds,
            DROP COLUMN bucket_start,
            DROP COLUMN metric_type_id,
            DROP COLUMN application_id
        """
    )
    op.execute("ALTER TABLE anomaly ADD COLUMN metric_id UUID NOT NULL")
    op.execute(
        "ALTER TABLE anomaly ADD CONSTRAINT fk_anomaly_metric "
        "FOREIGN KEY (metric_id) REFERENCES rum_metric(metric_id) "
        "ON DELETE RESTRICT"
    )
