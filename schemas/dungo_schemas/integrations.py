from pydantic import BaseModel
from typing import Optional, Dict, Any


class CreateIntegrationModel(BaseModel):
    name: str
    description: str
    icon: str
    auth_structure: Optional[Dict[str, Any]] = None


class DeleteIntegrationModel(BaseModel):
    id: int


class DeleteIntegrationEndpointModel(BaseModel):
    url: str
    integration_id: str


class UpdateIntegrationDescriptionModel(BaseModel):
    id: int
    description: str