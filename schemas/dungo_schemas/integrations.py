from pydantic import BaseModel


class CreateIntegrationModel(BaseModel):
    name: str


class DeleteIntegrationModel(BaseModel):
    id: int


class DeleteIntegrationEndpointModel(BaseModel):
    url: str
    integration_id: str