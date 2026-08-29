from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.core.log import logger
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant


async def recall_metric(state: DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer("召回指标信息")
    query = state["query"]
    keywords = state["keywords"]

    embedding_client = runtime.context["embedding_client"]
    metric_qdrant_repostory = runtime.context["metric_qdrant_repostory"]

    from app.prompt.load_prompt import load_prompt
    prompt = PromptTemplate.from_template(load_prompt("extend_keywords_for_metric_recall"))

    output_parser = JsonOutputParser()

    from app.agent.llm import llm
    chain = prompt | llm | output_parser

    result = await chain.ainvoke({"query": query})
    keywords = list(set(result+keywords))

    retrieved_metric_map: dict[str, MetricInfoQdrant] = {}
    for keyword in keywords:
        keyword_embedding = await embedding_client.aembed_query(keyword)
        payloads: MetricInfoQdrant = await metric_qdrant_repostory.search(keyword_embedding)
        for payload in payloads:
            if payload.id not in retrieved_metric_map:
                retrieved_metric_map[payload.id] = payload

    retrieved_metrics = list(retrieved_metric_map.values())

    logger.info(f"召回的指标信息：{list(retrieved_metric_map.keys())}")
    return {"retrieved_metrics": retrieved_metrics}
