"""Catálogos sin entidad ORM compartidos por los repositorios (ISS-B-14, DT-9).

`metric_type`, `alert_status` y `alert_channel` no tienen mirror ORM: se
referencian como `TableClause` livianos para los JOIN y subconsultas por
nombre o id. Viven aquí para no redefinirlos en cada repositorio.
"""

from sqlalchemy import Column, SmallInteger, Text, table

METRIC_TYPE = table(
    "metric_type",
    Column("metric_type_id", SmallInteger),
    Column("name", Text),
)
ALERT_STATUS = table(
    "alert_status",
    Column("status_id", SmallInteger),
    Column("name", Text),
)
ALERT_CHANNEL = table(
    "alert_channel",
    Column("channel_id", SmallInteger),
    Column("name", Text),
)
