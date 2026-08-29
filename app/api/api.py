from typing import Annotated

from fastapi import FastAPI
from fastapi.params import Depends
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.api.lifespan import lifespan
from app.agent.query_servece import QueryServece

app = FastAPI(lifespan=lifespan)

class Query(BaseModel):
    query: str

def get_query_servece() -> QueryServece:
    return QueryServece()

@app.post("/query")
async def query(query: Query,query_servece: Annotated[QueryServece,Depends(get_query_servece)]):
    return StreamingResponse(query_servece.query(query.query),media_type="text/event-stream")