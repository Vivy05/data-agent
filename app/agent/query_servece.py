from elasticsearch import AsyncElasticsearch
from fastapi.params import Depends
from langchain_openai import OpenAIEmbeddings
from typing import Annotated

from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.context import DataAgentContext
from app.agent.graph import graph
from app.agent.state import DataAgentState
from app.client.embedding_client_manger import  embedding_client_manger
from app.client.es_client_manger import es_client_manger
from app.client.mysql_client_manger import meta_mysql_client_manger, dw_mysql_client_manger
from app.client.qdrant_client_manger import qdrant_client_manger
from app.repository.es.value_es_reposlitory import ValueEsRepository
from app.repository.mysql.dw_mysql_repository import DwMysqlRepository
from app.repository.mysql.meta_mysql_repository import MetaMySQLRepository
from app.repository.qdrant.column_qdrant_repostory import ColumnQdrantRepostory
from app.repository.qdrant.metric_qdrant_repository import MetricQdrantRepository

async def get_qdrant_client():
    return qdrant_client_manger.init()
async def get_es_client():
    return es_client_manger.init()
async def get_meta_mysql_client():
    return meta_mysql_client_manger.init()
async def get_dw_mysql_client():
    return dw_mysql_client_manger.init()

async def get_embedding_client():
    return embedding_client_manger.client
async def get_metric_qdrant_repository(client: Annotated[AsyncQdrantClient,Depends(get_qdrant_client)]):
    return MetricQdrantRepository(client)
async def get_column_qdrant_repository(client: Annotated[AsyncQdrantClient,Depends(get_qdrant_client)]):
    return ColumnQdrantRepostory(client)
async def value_es_repostory(client: Annotated[AsyncElasticsearch,Depends(get_es_client)]):
    return ValueEsRepository(client)
async def get_meta_mysql_repository(session:Annotated[AsyncSession,Depends(get_meta_mysql_client)]):
    return MetaMySQLRepository(session)
async def get_dw_mysql_repository(session:Annotated[AsyncSession,Depends(get_dw_mysql_client)]):
    return DwMysqlRepository(session)

class QueryServece:
    def __init__(self,
                 embedding_client: Annotated[OpenAIEmbeddings,Depends(get_embedding_client)],
                 metric_qdrant_repostory: Annotated[MetricQdrantRepository,Depends(get_metric_qdrant_repository)],
                 column_qdrant_repostory: Annotated[ColumnQdrantRepostory,Depends(get_column_qdrant_repository)],
                 value_es_repostory: Annotated[ValueEsRepository,Depends(value_es_repostory)],
                 meta_mysql_repository: Annotated[MetaMySQLRepository,Depends(get_meta_mysql_repository)],
                 dw_mysql_repository: Annotated[DwMysqlRepository,Depends(get_dw_mysql_repository)]):
        self.embedding_client = embedding_client
        self.metric_qdrant_repostory = metric_qdrant_repostory
        self.column_qdrant_repostory = column_qdrant_repostory
        self.value_es_repostory = value_es_repostory
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository

    async def query(self,query: str):
        state = DataAgentState(
            query="统计一下华北地区的销售总额"
        )
        context = DataAgentContext(
            embedding_client = self.embedding_client,
            metric_qdrant_repostory = self.metric_qdrant_repostory,
            column_qdrant_repostory = self.column_qdrant_repostory,
            value_es_repostory = self.value_es_repostory,
            meta_mysql_repository = self.meta_mysql_repository,
            dw_mysql_repository = self.dw_mysql_repository)
        async  for chunk in graph.astream(input=state, context=context, stream_mode="custom"):
            yield f"data: {chunk}\n\n"