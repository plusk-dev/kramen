from pydantic import BaseModel

class CreateAPIKeyModel(BaseModel):
    name: str

class DeleteAPIKeyModel(BaseModel):
    id: int