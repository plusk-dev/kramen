from typing import List
from pydantic import BaseModel

class UploadOpenapiModel(BaseModel):
    integration_id: str
    selected_endpoints: List[str]