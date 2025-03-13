from pydantic import BaseModel, Field


class Query(BaseModel):
    integration_id: str = Field(..., description="ID of the integration")
    query: str = Field(...,
                       description="Query to be queried against the vector database")
