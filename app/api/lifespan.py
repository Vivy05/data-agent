from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.client.embedding_client_manger import embedding_client_manger
from app.client.es_client_manger import es_client_manger
from app.client.mysql_client_manger import meta_mysql_client_manger, dw_mysql_client_manger
from app.client.qdrant_client_manger import qdrant_client_manger

@asynccontextmanager
async def lifespan(app: FastAPI):
    embedding_client_manger.init()
    es_client_manger.init()
    qdrant_client_manger.init()
    meta_mysql_client_manger.init()
    dw_mysql_client_manger.init()
    yield
    await es_client_manger.close()
    await qdrant_client_manger.close()
    await meta_mysql_client_manger.close()
    await dw_mysql_client_manger.close()