from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, TableInfoState, ColumnInfoState, MetricInfoState
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.repository.mysql.meta_mysql_repository import MetaMySQLRepository


async def merge_retrieved_info(state: DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer("app/agent/node/merge_retrieved_info.py")

    retrieved_columns: list[ColumnInfoQdrant] = state["retrieved_columns"]
    retrieved_metrics: list[MetricInfoQdrant] = state["retrieved_metrics"]

    meta_mysql_repository: MetaMySQLRepository = runtime.context['meta_mysql_repository']

    #构建table
    table_info_map:dict[str,TableInfoState] = {}
    for retrieved_column in retrieved_columns:
        table_info_p:TableInfoMySQL = await meta_mysql_repository.serch(retrieved_column["table"])
        column_info = ColumnInfoState(
            name=retrieved_column["name"],
            description=retrieved_column["description"],
            examples=retrieved_column["examples"],
            role=retrieved_column["role"],
            type=retrieved_column["type"],
            alias=retrieved_column["alias"],
        )
        if table_info_p.id not in table_info_map:
            table_info = TableInfoState(
                name=table_info_p.name,
                role=table_info_p.role,
                description=table_info_p.description,
                columns=[column_info]
            )
            table_info_map[table_info_p.id] = table_info
        else:
            table_info_map[table_info_p.id]["columns"].append(column_info)

    #构建metric
    metric_info_state: list[MetricInfoState] = [MetricInfoState(name=retrieved_metric["name"],
                                                                description=retrieved_metric["description"],
                                                                relevant_columns=retrieved_metric["relevant_columns"],
                                                                alias=retrieved_metric["alias"],)
                                            for retrieved_metric in retrieved_metrics]
    return {"table_info_state":list(table_info_map.values()),"metric_info_state":metric_info_state}