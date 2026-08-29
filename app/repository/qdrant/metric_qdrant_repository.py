from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams,Distance,PointStruct


class MetricQdrantRepository:
    collection_name = 'data_agent-metric'
    def __init__(self,client:AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):
        if not await self.client.collection_exists(self.collection_name):
            await self.client.create_collection(self.collection_name,
                                                vectors_config=VectorParams(size=384,distance=Distance.COSINE))

    async def upsert(self, ids:list, embedding:list, payloads:list,batch_size=20):
        zipped = list(zip(ids,embedding,payloads))
        for i in range(0,len(zipped),batch_size):
            batch = zipped[i:i+batch_size]
            batch_point = [PointStruct(id=id,vector=embedding,payload=payload) for id,embedding,payload in batch]
            await self.client.upsert(collection_name=self.collection_name,points=batch_point)

    async def search(self, keyword_embedding: list[float], score_threshold: float = 0.6):
        result = await self.client.query_points(collection_name=self.collection_name, query=keyword_embedding,
                                                score_threshold=score_threshold)
        return [point.payload for point in result.points]