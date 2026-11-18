"""Reglas de umbral y sus columnas en la alerta (ISS-B-14, ADR-0013).

D1 movió la detección ML a M3, así que en la v1 las alertas las crea el motor
determinístico de reglas de umbral (B.14). La `0007` dejó anotado que el
umbral, el valor observado y el id de la regla los agrega esta migración,
colgando de ella (`down_revision = "0007"`) para no dejar dos heads.

Esta migración:

- crea `alert_rule`: umbral por aplicación y por métrica, con comparación
  (`gt`/`lt`), ventana, muestras mínimas, cooldown y severidad;
- agrega a `alert` las columnas `rule_id` (FK nullable), `threshold` y
  `observed_value`, y el índice del cooldown.

`threshold` y `observed_value` son NUMERIC y no punto flotante: la comparación
inclusiva del umbral (S4) no puede quedar a merced del redondeo. Son nullable
porque las alertas de ML de M3 no tienen regla detrás.

El downgrade aborta si hay alertas de umbral: `rule_id`, `threshold` y
`observed_value` no se pueden derivar, igual que en la `0007`.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-18
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _assert_no_threshold_alerts(direction: str) -> None:
    """Aborta si ALERT tiene alertas de umbral (no hay backfill posible)."""
    count = op.get_bind().exec_driver_sql(
        "SELECT count(*) FROM alert WHERE rule_id IS NOT NULL"
    ).scalar()
    if count:
        raise RuntimeError(
            f"0008 {direction} abortado: alert tiene {count} alerta(s) de "
            "umbral (rule_id no nulo) y no existe forma segura de derivar "
            "rule_id, threshold ni observed_value. Vaciar alert antes de "
            "continuar."
        )


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE alert_rule (
            rule_id UUID PRIMARY KEY,
            application_id UUID NOT NULL,
            metric_type_id SMALLINT NOT NULL,
            comparison TEXT NOT NULL,
            threshold NUMERIC NOT NULL,
            window_minutes INTEGER NOT NULL,
            min_samples INTEGER NOT NULL,
            cooldown_minutes INTEGER NOT NULL,
            severity TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_alert_rule_comparison
                CHECK (comparison IN ('gt', 'lt')),
            CONSTRAINT ck_alert_rule_window
                CHECK (window_minutes BETWEEN 1 AND 10080),
            CONSTRAINT ck_alert_rule_min_samples
                CHECK (min_samples >= 1),
            CONSTRAINT ck_alert_rule_cooldown
                CHECK (cooldown_minutes >= 1),
            CONSTRAINT ck_alert_rule_severity
                CHECK (severity IN ('low', 'medium', 'high', 'critical')),
            CONSTRAINT fk_alert_rule_application
                FOREIGN KEY (application_id)
                REFERENCES application(app_id)
                ON DELETE RESTRICT,
            CONSTRAINT fk_alert_rule_metric_type
                FOREIGN KEY (metric_type_id)
                REFERENCES metric_type(metric_type_id)
                ON DELETE RESTRICT
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_alert_rule_key ON alert_rule"
        "(application_id, metric_type_id, comparison, threshold)"
    )
    op.execute(
        "CREATE INDEX idx_alert_rule_app_active ON alert_rule"
        "(application_id, is_active)"
    )
    op.execute(
        """
        ALTER TABLE alert
            ADD COLUMN rule_id UUID,
            ADD COLUMN threshold NUMERIC,
            ADD COLUMN observed_value NUMERIC,
            ADD CONSTRAINT fk_alert_rule
                FOREIGN KEY (rule_id)
                REFERENCES alert_rule(rule_id)
                ON DELETE RESTRICT
        """
    )
    op.execute(
        "CREATE INDEX idx_alert_rule_created ON alert(rule_id, created_at DESC)"
    )


def downgrade() -> None:
    _assert_no_threshold_alerts("downgrade")
    op.execute("DROP INDEX idx_alert_rule_created")
    op.execute(
        """
        ALTER TABLE alert
            DROP CONSTRAINT fk_alert_rule,
            DROP COLUMN rule_id,
            DROP COLUMN threshold,
            DROP COLUMN observed_value
        """
    )
    op.execute("DROP INDEX idx_alert_rule_app_active")
    op.execute("DROP INDEX uq_alert_rule_key")
    op.execute("DROP TABLE alert_rule")
