import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker

from app.conf.app_config import app_config, DBConfig


class MysqlClientManger:
    def __init__(self, db_config: DBConfig):
        self.engine: AsyncEngine | None = None
        self.session_factory = None
        self.db_config = db_config

    def _get_url(self):
        return f"mysql+asyncmy://{self.db_config.user}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}?charset=utf8mb4"

    def init(self):
        self.engine = create_async_engine(self._get_url(), pool_pre_ping=True,pool_size=10)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False, autoflush=True)

    async def close(self):
        await self.engine.dispose()

dw_mysql_client_manger = MysqlClientManger(db_config=app_config.db_dw)
meta_mysql_client_manger = MysqlClientManger(db_config=app_config.db_meta)

if __name__ == '__main__':
    async def ets():
        dw_mysql_client_manger.init()
        async with dw_mysql_client_manger.session_factory() as session:
            result = await session.execute(text("select * from fact_order limit 10"))
            rows = result.mappings().fetchall()
            print(rows)


    asyncio.run(ets())