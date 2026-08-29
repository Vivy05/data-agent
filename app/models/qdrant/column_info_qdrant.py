from typing import TypedDict


class ColumnInfoQdrant(TypedDict):
    id: str
    name: str
    role: str
    type: str
    examples: list
    description: str
    alias: list
    table: str