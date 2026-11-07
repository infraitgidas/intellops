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


def _availability_reference_count() -> int:
    """Filas que referencian el tipo `AVAILABILITY` (FKs ON DELETE RESTRICT)."""
    return op.get_bind().exec_driver_sql(
        "SELECT (SELECT count(*) FROM rum_metric rm "
        "JOIN metric_type mt ON mt.metric_type_id = rm.metric_type_id "
        "WHERE mt.name = 'AVAILABILITY') "
        "+ (SELECT count(*) FROM user_favorite_metric fm "
        "JOIN metric_type mt ON mt.metric_type_id = fm.metric_type_id "
        "WHERE mt.name = 'AVAILABILITY')"
    ).scalar()


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO metric_type (name, description) VALUES
            ('AVAILABILITY',
             'Disponibilidad medida por la sonda HTTP (1 disponible, 0 no disponible)')
        ON CONFLICT (name) DO NOTHING
        """
    )


def downgrade() -> None:
    """Retira la fila de `AVAILABILITY`, salvo que ya haya uso (B.13/D1).

    `fk_rum_metric_type` y `fk_user_favorite_metric_type` son ON DELETE
    RESTRICT: una vez que la sonda ingestó una métrica de disponibilidad, el
    DELETE revienta con `RestrictViolation` a mitad del downgrade. Como en
    `0004`, el guard aborta ANTES con un mensaje accionable y deja la revisión
    en 0006, en lugar de fallar dentro de la sentencia.
    """
    count = _availability_reference_count()
    if count:
        raise RuntimeError(
            f"0006 downgrade abortado: {count} fila(s) de rum_metric (o "
            "user_favorite_metric) referencian AVAILABILITY y "
            "fk_rum_metric_type es ON DELETE RESTRICT. Borrar esas métricas "
            "antes de bajar a 0005."
        )
    op.execute("DELETE FROM metric_type WHERE name = 'AVAILABILITY'")
