import asyncio


from argparse import ArgumentParser
from pathlib import Path

from app.client.embedding_client_manger import embedding_client_manger
from app.client.es_client_manger import es_client_manger
from app.client.qdrant_client_manger import qdrant_client_manger
from app.repository.qdrant.column_qdrant_repostory import ColumnQdrantRepostory
from app.repository.mysql.dw_mysql_repository import DwMysqlRepository
from app.repository.mysql.meta_mysql_repository import MetaMySQLRepository
from app.repository.es.value_es_reposlitory import ValueEsRepository
from app.repository.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.service.meta_knowledge_service import MetaKnowledgeService
from app.client.mysql_client_manger import meta_mysql_client_manger, dw_mysql_client_manger


async def build(config_path: Path):
    meta_mysql_client_manger.init()
    dw_mysql_client_manger.init()
    qdrant_client_manger.init()
    embedding_client_manger.init()
    es_client_manger.init()
    async with meta_mysql_client_manger.session_factory() as meta_session, dw_mysql_client_manger.session_factory() as dw_session:
        meta_mysql_repository = MetaMySQLRepository(meta_session)
        dw_mysql_repository = DwMysqlRepository(dw_session)
        column_qdrant_repository = ColumnQdrantRepostory(qdrant_client_manger.client)
        embedding_client = embedding_client_manger.client
        value_es_repository = ValueEsRepository(es_client_manger.client)
        metric_qdrant_repository = MetricQdrantRepository(qdrant_client_manger.client)

        meta_knowledge_service = MetaKnowledgeService(meta_mysql_repository,
                                                      dw_mysql_repository,
                                                      column_qdrant_repository,
                                                      embedding_client,
                                                      value_es_repository,
                                                      metric_qdrant_repository)
        await meta_knowledge_service.build(config_path)

    await dw_mysql_client_manger.close()
    await qdrant_client_manger.close()
    await meta_mysql_client_manger.close()
    await es_client_manger.close()

if __name__ == '__main__':
    argument_parser = ArgumentParser()
    argument_parser.add_argument('-c','--conf')
    args = argument_parser.parse_args()
    config_path = Path(args.conf)
    asyncio.run(build(config_path))
