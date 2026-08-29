from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_openai import OpenAIEmbeddings
from huggingface_hub import InferenceClient

from app.conf.app_config import EmbeddingConfig, app_config


class EmbeddingClientManger:
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.client: OpenAIEmbeddings | None = None

    def init(self):
        self.client = OpenAIEmbeddings(model="BAAI/bge-small-zh-v1.5",
                                       base_url=f"http://{self.config.host}:{self.config.port}",
                                       # 本地服务可以填写任意占位符
                                       api_key="unused",
                                       check_embedding_ctx_length=False,)





# import httpx
# from typing import List
# from app.conf.app_config import EmbeddingConfig, app_config
#
#
# class EmbeddingClientManger:
#     def __init__(self, config: EmbeddingConfig):
#         self.config = config
#         self.base_url = f"http://{config.host}:{config.port}"
#         # 添加 client 属性，指向自身或者一个简单对象
#         self.client = self  # 或者设置为 None，但调用方期望有 aembed_documents 方法
#
#     def init(self):
#         """兼容旧代码"""
#         # 确保 client 属性存在
#         if not hasattr(self, 'client') or self.client is None:
#             self.client = self
#
#     async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
#         url = f"{self.base_url}/embed"
#         async with httpx.AsyncClient(timeout=60.0) as http_client:
#             response = await http_client.post(
#                 url,
#                 json={"inputs": texts},
#                 headers={"Content-Type": "application/json"}
#             )
#             response.raise_for_status()
#             return response.json()
#
#     async def aembed_query(self, text: str) -> List[float]:
#         result = await self.aembed_documents([text])
#         return result[0]
#
#     def embed_documents(self, texts: List[str]) -> List[List[float]]:
#         import asyncio
#         return asyncio.run(self.aembed_documents(texts))
#
#     def embed_query(self, text: str) -> List[float]:
#         import asyncio
#         return asyncio.run(self.aembed_query(text))


embedding_client_manger = EmbeddingClientManger(config=app_config.embedding)