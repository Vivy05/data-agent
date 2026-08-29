from typing import TypedDict
from langchain_openai import OpenAIEmbeddings

from app.repository.es.value_es_reposlitory import ValueEsRepository
from app.repository.mysql.dw_mysql_repository import DwMysqlRepository
from app.repository.mysql.meta_mysql_repository import MetaMySQLRepository
from app.repository.qdrant.column_qdrant_repostory import ColumnQdrantRepostory
from app.repository.qdrant.metric_qdrant_repository import MetricQdrantRepository


class DataAgentContext(TypedDict):
    embedding_client: OpenAIEmbeddings
    column_qdrant_repostory: ColumnQdrantRepostory
    metric_qdrant_repostory: MetricQdrantRepository
    value_es_repostory: ValueEsRepository
    meta_mysql_repository: MetaMySQLRepository
    dw_mysql_repository: DwMysqlRepository

