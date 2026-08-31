
from elasticsearch import AsyncElasticsearch

from app.models.es.value_info_es import ValueInfoES


class ValueEsRepository:
    index_name = 'data_index-value'
    mappings = {
        "properties": {
            "id": {"type": "keyword"},
            "value": {"type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_max_word"},
            "type": {"type": "keyword"},
            "column_id": {"type": "keyword"},
            "column_name": {"type": "keyword"},
            "table_id": {"type": "keyword"},
            "table_name": {"type": "keyword"},
        }
    }
    def __init__(self,client: AsyncElasticsearch):
        self.client = client


    def ensure_index(self):
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(index=self.index_name,mappings=self.mappings)

    async def index(self, value_infos,batch_size:int = 20):
        for i in range(0,len(value_infos),batch_size):
            batch = value_infos[i:i+batch_size]
            operations = []
            for value_info in batch:
                operations.append({"index":{"_index":self.index_name,"_id":value_info["id"]}})
                operations.append(value_info)
            await self.client.bulk(operations=operations)

    async def query(self, query: str, score_threshold: float = 0.6, limit: int = 10) -> list[ValueInfoES]:

        es_query = {
            "match": {
                "value": query
            }
        }

        resp = await self.client.search(
            index=self.index_name,
            query=es_query,
            min_score=score_threshold,
            size=limit
        )

        hits = resp.get("hits", {}).get("hits", [])

        results: list[ValueInfoES] = []
        for hit in hits:
            source = hit["_source"]
            results.append(source)

        return results