from langgraph.runtime import Runtime
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.prompt.load_prompt import load_prompt


async def recall_column(state: DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer("召回字段")

    query = state["query"]
    keywords = state["keywords"]
    embedding_client = runtime.context["embedding_client"]
    column_qdrant_repostory = runtime.context["column_qdrant_repostory"]

    prompt = PromptTemplate.from_template(load_prompt("extend_keywords_for_column_recall"))

    output_parser = JsonOutputParser()

    chain = prompt | llm | output_parser

    result = await chain.ainvoke({"query":query})

    keywords = list(set(keywords + result))

    retrieved_columns_map: dict[str,ColumnInfoQdrant] = {}
    for keyword in keywords:
        keyword_embedding =await embedding_client.aembed_query(keyword)
        payloads:ColumnInfoQdrant = await column_qdrant_repostory.search(keyword_embedding)
        for payload in payloads:
            if payload.id not in retrieved_columns_map:
                retrieved_columns_map[payload.id] = payload

    retrieved_columns = list(retrieved_columns_map.values())
    logger.info(f"召回的字段信息：{list(retrieved_columns_map.keys())}")
    return {"retrieved_columns":retrieved_columns}
