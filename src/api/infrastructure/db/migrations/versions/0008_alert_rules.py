"""Reglas de umbral para alertas de la v1 (ISS-B-14, #74).

En la v1 un evaluador periódico del core crea las alertas Pending a partir de
tres reglas de umbral por aplicación (latencia, errores, disponibilidad), sin
detección ML. Esta migración:

- crea `alert_rule`: una fila por (aplicación, regla) que reemplaza por
  completo al default del código (`rule_id` es una clave estable en TEXT, con
  CHECK a las tres reglas conocidas); `ON DELETE CASCADE` con la aplicación;
- agrega a `alert` las columnas nullable `rule_id`, `threshold` y
  `observed_value` (qué regla la creó, con qué umbral y qué valor observó),
  más `ck_alert_rule_id`. `rule_id` no es FK: con defaults en código no hay
  fila de `alert_rule` a la que apuntar y el cooldown se consulta por
  (`application_id`, `rule_id`) en `alert`.

Sin guarda en upgrade: la tabla es nueva y las columnas son nullable, así que
las alertas existentes quedan válidas.

Downgrade sin guarda: elimina la tabla y las columnas. Las alertas quedan
válidas para la forma de 0007 y su mensaje conserva umbral y valor observado.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-15
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE alert_rule (
            application_id UUID NOT NULL,
            rule_id TEXT NOT NULL,
            threshold DOUBLE PRECISION NOT NULL,
            severity TEXT NOT NULL,
            window_seconds INTEGER NOT NULL,
            min_samples INTEGER NOT NULL,
            cooldown_seconds INTEGER NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            CONSTRAINT pk_alert_rule PRIMARY KEY (application_id, rule_id),
            CONSTRAINT ck_alert_rule_rule_id
                CHECK (rule_id IN ('latency', 'error_rate', 'availability')),
            CONSTRAINT ck_alert_rule_severity
                CHECK (severity IN ('low', 'medium', 'high', 'critical')),
            CONSTRAINT ck_alert_rule_window CHECK (window_seconds >= 60),
            CONSTRAINT ck_alert_rule_min_samples CHECK (min_samples >= 1),
            CONSTRAINT ck_alert_rule_cooldown CHECK (cooldown_seconds >= 0),
            CONSTRAINT fk_alert_rule_application
                FOREIGN KEY (application_id)
                REFERENCES application(app_id)
                ON DELETE CASCADE
        )
        """
    )
    op.execute(
        """
        ALTER TABLE alert
            ADD COLUMN rule_id TEXT,
            ADD COLUMN threshold DOUBLE PRECISION,
            ADD COLUMN observed_value DOUBLE PRECISION,
            ADD CONSTRAINT ck_alert_rule_id
                CHECK (rule_id IN ('latency', 'error_rate', 'availability'))
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE alert
            DROP CONSTRAINT ck_alert_rule_id,
            DROP COLUMN observed_value,
            DROP COLUMN threshold,
            DROP COLUMN rule_id
        """
    )
    op.execute("DROP TABLE alert_rule")
