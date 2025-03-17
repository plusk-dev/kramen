from typing import List
from pydantic import BaseModel

class UploadOpenapiModel(BaseModel):
    data: dict | str
    integration_id: str
    selected_endpoints: List[str]