import uuid

from pathlib import Path
from langchain_openai import OpenAIEmbeddings

from app.conf.meta_config import MetaConfig
from app.conf.config_loader import load_config
from app.core.log import logger
from app.models.es.value_info_es import ValueInfoES
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.repository.qdrant.column_qdrant_repostory import ColumnQdrantRepostory
from app.repository.mysql.dw_mysql_repository import DwMysqlRepository
from app.repository.mysql.meta_mysql_repository import MetaMySQLRepository
from app.repository.es.value_es_reposlitory import ValueEsRepository
from app.repository.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:
    def __init__(self,meta_mysql_repository: MetaMySQLRepository,
                 dw_mysql_repository: DwMysqlRepository,
                 column_qdrant_repository: ColumnQdrantRepostory,
                 embedding_client: OpenAIEmbeddings,
                 value_es_repository: ValueEsRepository,
                 metric_qdrant_repository: MetricQdrantRepository):
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.embedding_client = embedding_client
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository

    def _convert_column_info_from_mysql_to_qdrant(self, column_info: ColumnInfoMySQL) -> ColumnInfoQdrant:
        return ColumnInfoQdrant(
            id = column_info.id,
            name = column_info.name,
            role = column_info.role,
            type= column_info.type,
            examples = column_info.examples,
            description = column_info.description,
            alias = column_info.alias,
            table = column_info.table_id,
        )

    async def _save_table_to_meta_db(self,meta_config: MetaConfig):

        table_infos: list[TableInfoMySQL] = []
        column_infos: list[ColumnInfoMySQL] = []
        for table in meta_config.tables:
            table_info = TableInfoMySQL(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description,
            )
            table_infos.append(table_info)

            column_types: dict[str, str] = await self.dw_mysql_repository.get_column_types(table.name)

            for column in table.columns:
                column_values_list = await self.dw_mysql_repository.get_column_values(table.name, column.name, 10)
                column_info = ColumnInfoMySQL(
                    id=f"{table.name}.{column.name}",
                    name=column.name,
                    type=column_types[column.name],
                    role=column.role,
                    examples=column_values_list,
                    description=column.description,
                    alias=column.alias,
                    table_id=table.name,
                )
                column_infos.append(column_info)

        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.save_table_infos(table_infos)
            await self.meta_mysql_repository.save_column_infos(column_infos)

        return table_infos, column_infos

    async def _save_column_info_to_qdrant(self, column_infos: list[ColumnInfoMySQL]):
        points = []
        for column_info in column_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.name,
                "payload": self._convert_column_info_from_mysql_to_qdrant(column_info),
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.description,
                "payload": self._convert_column_info_from_mysql_to_qdrant(column_info),
            })
            for alia in column_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alia,
                    "payload": self._convert_column_info_from_mysql_to_qdrant(column_info),
                })

        embedding_texts = [point['embedding_text'] for point in points]
        batch_size = 4
        embeddings = []
        for i in range(0, len(embedding_texts), batch_size):
            batch_embeddings = await self.embedding_client.aembed_documents(embedding_texts[i:i + batch_size])
            embeddings.extend(batch_embeddings)
        ids = [point['id'] for point in points]
        payloads = [point['payload'] for point in points]

        self.column_qdrant_repository.upsert(ids,embeddings,payloads)

    async def _save_value_info_to_es(self,meta_config: MetaConfig,column_infos: list[ColumnInfoMySQL]):
        column2sync: dict[str, bool] = {}
        for table in meta_config.tables:
            for column in table.columns:
                if column.sync:
                    column2sync[f"{table.name}.{column.name}"] = column.sync
        value_infos = []
        for column_info in column_infos:
            sync = column2sync.get(column_info.id, False)
            if sync:
                current_values_infos = await self.dw_mysql_repository.get_column_values(column_info.table_id,
                                                                                        column_info.name, 100000)
                value_info_es_list = [
                    ValueInfoES(
                        id=f"{column_info.id}.{value}",
                        value=value,
                        type=column_info.type,
                        column_id=column_info.id,
                        column_name=column_info.name,
                        table_id=column_info.table_id,
                        table_name=column_info.table_id,
                    )
                    for value in current_values_infos
                ]
                value_infos.extend(value_info_es_list)
        await self.value_es_repository.index(value_infos, batch_size=20)

    async def _save_metrics_to_meta_db(self, meta_config: MetaConfig):
        metric_infos: list[MetricInfoMySQL] = []
        column_metrics: list[ColumnMetricMySQL] = []
        for metric in meta_config.metrics:
            metric_info = MetricInfoMySQL(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias,
            )
            metric_infos.append(metric_info)

            for relevant_column in metric.relevant_columns:
                column_metric = ColumnMetricMySQL(
                    column_id=relevant_column,
                    metric_id=metric.name
                )
                column_metrics.append(column_metric)
        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.save_metric_infos(metric_infos)
            await self.meta_mysql_repository.save_column_metric(column_metrics)

        return metric_infos

    def _convert_metric_info_from_mysql_to_qdrant(self, metrics_info: MetricInfoMySQL) -> MetricInfoQdrant:
        return MetricInfoQdrant(
            id=metrics_info.id,
            name=metrics_info.name,
            description=metrics_info.description,
            relevant_columns=metrics_info.relevant_columns,
            alias=metrics_info.alias,
        )

    async def _save_metric_info_to_qdrant(self, metrics_infos:list[MetricInfoMySQL]):
        points: list[dict] = []
        for metrics_info in metrics_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metrics_info.name,
                "payload": self._convert_metric_info_from_mysql_to_qdrant(metrics_info)
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metrics_info.description,
                "payload": self._convert_metric_info_from_mysql_to_qdrant(metrics_info)
            })
            for alia in metrics_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alia,
                    "payload": self._convert_metric_info_from_mysql_to_qdrant(metrics_info)
                })
        ids = [point['id'] for point in points]
        embedding = []
        embedding_texts = [point['embedding_text'] for point in points]
        embedding_batch_size = 10
        for i in range(0, len(embedding_texts), embedding_batch_size):
            batch_embedding_text = embedding_texts[i:i + embedding_batch_size]
            batch_embedding = await self.embedding_client.aembed_documents(batch_embedding_text)
            embedding.extend(batch_embedding)
        payloads = [point['payload'] for point in points]

        await self.metric_qdrant_repository.ensure_collection()

        await self.metric_qdrant_repository.upsert(ids, embedding, payloads)

    async def build(self,config_path: Path):
        meta_config:MetaConfig = load_config(config_path,MetaConfig)
        logger.info("加载配置文件成功")
        if meta_config.tables:
            # 存储到数据库
            table_infos,column_infos = await self._save_table_to_meta_db(meta_config)
            logger.info("保存表信息到meta数据库")

            await self.column_qdrant_repository.ensure_collection()
            # 进行向量化并存储到向量数据库
            await self._save_column_info_to_qdrant(column_infos)
            logger.info("为字段信息建立向量索引")
            #将需要的值存储到es中
            await self._save_value_info_to_es(meta_config, column_infos)
            logger.info("为字段信息建立全文索引")

        if meta_config.metrics:
            metrics_infos = await self._save_metrics_to_meta_db(meta_config)
            logger.info("保存指标信息到meta数据库")

            await self._save_metric_info_to_qdrant(metrics_infos)
            logger.info("为指标信息建立索引")

        logger.info("元数据知识库构建完成")


