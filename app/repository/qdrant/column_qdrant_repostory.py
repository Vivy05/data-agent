from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

from app.conf.meta_config import ColumnConfig
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant


class ColumnQdrantRepostory:
    collection_name:str = "data-agent-column"
    def __init__(self,client: AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):
        if not await self.client.collection_exists(self.collection_name):
            await self.client.create_collection(self.collection_name,
                                                vectors_config=VectorParams(size=384,distance=Distance.COSINE))

    def upsert(self, ids:list,embeddings:list,payload:list[ColumnInfoQdrant],batch_size:int = 20):
        zipped = list(zip(ids,embeddings,payload))
        for i in range(0, len(zipped), batch_size):
            batch = zipped[i:i+batch_size]
            batch_points = [PointStruct(id=id,vector=embedding,payload=payload) for id,embedding,payload in batch]
            self.client.upsert(self.collection_name,batch_points)

    async def search(self, keyword_embedding: list[float],score_threshold:float=0.6):
        result = await self.client.query_points(collection_name=self.collection_name,query=keyword_embedding,score_threshold=score_threshold)
        return [point.payload for point in result.points]
