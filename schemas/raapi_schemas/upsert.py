from pydantic import BaseModel, Field

class UpsertSchema(BaseModel):
    integration_id: str = Field(..., description="ID of the integration")
    text: str = Field(..., description="Text to be vectorized")
    metadata: dict = Field(..., description="Metadata of the vector")