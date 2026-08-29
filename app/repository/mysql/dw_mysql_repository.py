from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DwMysqlRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # async def
    async def get_column_types(self, table_name:str):
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        return {row.Field:row.Type for row in result.fetchall()}

    async def get_column_values(self, table_name:str, column_name:str, limit:int):
        sql = f"select {column_name} from {table_name} limit {limit}"
        result = await self.session.execute(text(sql))
        return result.scalars().fetchall()
