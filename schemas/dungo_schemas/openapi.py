from pydantic import BaseModel

class UploadOpenapiModel(BaseModel):
    data: dict | str
    integration_id: str