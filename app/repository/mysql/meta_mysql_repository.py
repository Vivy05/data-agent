from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL


class MetaMySQLRepository:
    def __init__(self,session: AsyncSession):
        self.session = session

    async def save_table_infos(self, table_infos):
        self.session.add_all(table_infos)

    async def save_column_infos(self, column_infos):
        self.session.add_all(column_infos)

    async def save_metric_infos(self, metric_infos:list[MetricInfoMySQL]):
        self.session.add_all(metric_infos)

    async def save_column_metric(self, column_metrics: list[ColumnMetricMySQL]):
        self.session.add_all(column_metrics)

    async def serch(self, table_id:str) -> TableInfoMySQL | None:
        result:TableInfoMySQL | None = await self.session.get(TableInfoMySQL,table_id)
        return result