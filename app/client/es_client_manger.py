
from elasticsearch import AsyncElasticsearch

from app.conf.app_config import app_config,ESConfig

class EsClientManger:
    def __init__(self,es_config:ESConfig):
        self.es_config = es_config
        self.client: AsyncElasticsearch | None = None
    def _get_url(self):
        return f"http://{self.es_config.host}:{self.es_config.port}"

    def init(self):
        self.client = AsyncElasticsearch(self._get_url())

    async def close(self):
        await self.client.close()

es_client_manger = EsClientManger(app_config.es)