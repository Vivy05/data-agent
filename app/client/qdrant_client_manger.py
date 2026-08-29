

from qdrant_client import AsyncQdrantClient

from app.conf.app_config import app_config,QdrantConfig

class QdrantClientManger:
    def __init__(self,qdrant_config:QdrantConfig):
        self.qdrant_config = qdrant_config
        self.client = None

    def _get_url(self):
        return f"http://{self.qdrant_config.host}:{self.qdrant_config.port}"

    def init(self):
        self.client = AsyncQdrantClient(url=self._get_url())

    async def close(self):
        await self.client.close()

qdrant_client_manger = QdrantClientManger(app_config.qdrant)