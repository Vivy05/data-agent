import asyncio

from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agent.context import DataAgentContext
from app.agent.node.add_extra_context import add_extra_context
from app.agent.node.correct_sql import correct_sql
from app.agent.node.execute_sql import execute_sql
from app.agent.node.extract_keywords import extract_keywords
from app.agent.node.filter_metric import filter_metric
from app.agent.node.filter_table import filter_table
from app.agent.node.generate_sql import generate_sql
from app.agent.node.merge_retrieved_info import merge_retrieved_info
from app.agent.node.recall_colume import recall_column
from app.agent.node.recall_metric import recall_metric
from app.agent.node.recall_value import recall_value
from app.agent.node.validate_sql import validate_sql
from app.agent.state import DataAgentState
from app.client.embedding_client_manger import embedding_client_manger
from app.client.es_client_manger import es_client_manger
from app.client.mysql_client_manger import meta_mysql_client_manger, dw_mysql_client_manger
from app.client.qdrant_client_manger import qdrant_client_manger
from app.repository.es.value_es_reposlitory import ValueEsRepository
from app.repository.mysql.dw_mysql_repository import DwMysqlRepository
from app.repository.mysql.meta_mysql_repository import MetaMySQLRepository
from app.repository.qdrant.column_qdrant_repostory import ColumnQdrantRepostory
from app.repository.qdrant.metric_qdrant_repository import MetricQdrantRepository

graph_builder = StateGraph(state_schema=DataAgentState,context_schema=DataAgentContext)

graph_builder.add_node("add_extra_context",add_extra_context)
graph_builder.add_node("correct_sql",correct_sql)
graph_builder.add_node("execute_sql",execute_sql)
graph_builder.add_node("extract_keywords",extract_keywords)
graph_builder.add_node("filter_metric",filter_metric)
graph_builder.add_node("filter_table",filter_table)
graph_builder.add_node("generate_sql",generate_sql)
graph_builder.add_node("merge_retrieved_info",merge_retrieved_info)
graph_builder.add_node("recall_column",recall_column)
graph_builder.add_node("recall_metric",recall_metric)
graph_builder.add_node("recall_value",recall_value)
graph_builder.add_node("validate_sql",validate_sql)

graph_builder.add_edge(START,"extract_keywords")

graph_builder.add_edge("extract_keywords","recall_column")
graph_builder.add_edge("extract_keywords","recall_metric")
graph_builder.add_edge("extract_keywords","recall_value")
graph_builder.add_edge("recall_column","merge_retrieved_info")
graph_builder.add_edge("recall_metric","merge_retrieved_info")
graph_builder.add_edge("recall_value","merge_retrieved_info")
graph_builder.add_edge("merge_retrieved_info","filter_metric")
graph_builder.add_edge("merge_retrieved_info","filter_table")
graph_builder.add_edge("filter_metric","add_extra_context")
graph_builder.add_edge("filter_table","add_extra_context")
graph_builder.add_edge("add_extra_context","generate_sql")
graph_builder.add_edge("generate_sql","validate_sql")
graph_builder.add_conditional_edges("validate_sql",lambda state:"execute_sql" if state['error'] is None else "correct_sql",{"execute_sql":"execute_sql","correct_sql":"correct_sql"})
graph_builder.add_edge("correct_sql","execute_sql")

graph_builder.add_edge("execute_sql",END)



graph = graph_builder.compile()

if __name__ == "__main__":
    embedding_client_manger.init()
    es_client_manger.init()
    qdrant_client_manger.init()
    meta_mysql_client_manger.init()
    dw_mysql_client_manger.init()

    async def test():
        state = DataAgentState(
            query="统计一下华北地区的销售总额"
        )
        context = DataAgentContext(
            embedding_client=embedding_client_manger.client,
            metric_qdrant_repostory=MetricQdrantRepository(qdrant_client_manger.client),
            column_qdrant_repostory=ColumnQdrantRepostory(qdrant_client_manger.client),
            value_es_repostory=ValueEsRepository(es_client_manger.client),
            meta_mysql_repository=MetaMySQLRepository(meta_mysql_client_manger),
            dw_mysql_repository=DwMysqlRepository(dw_mysql_client_manger)
        )
        async  for chunk in graph.astream(input=state,context=context,stream_mode="custom"):
            print(chunk)

    asyncio.run(test())