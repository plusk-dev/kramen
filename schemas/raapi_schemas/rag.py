from typing import List, Optional
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    llm: str = Field(..., description="Identifier for the LLM")
    llm_api_key: str = Field(..., description="API key for the LLM provider")


class IdentifyEndpointsRequest(BaseModel):
    api_base: str = Field(...,
                          description="The base URL of the API to which the integration will connect.")
    integration_id: str = Field(
        ..., description="A unique identifier for the integration making the request.")
    query: str = Field(..., description="The query or prompt that the integration will use to identify available endpoints.")
    rephrasal_instructions: Optional[str] = Field(
        None, description="An optional system prompt used to guide or customize the integration's behavior.")
    rephraser: bool = Field(
        ..., description="A flag to indicate whether the integration should rephrase the query before processing.")
    llm_config: LLMConfig


class RunQuerySchema(BaseModel):
    rephraser: bool = Field(
        ..., description="A flag to indicate whether the integration should rephrase the query before processing.")
    integration_id: str = Field(..., description="ID of the integration")
    # Fixed this line
    api_base: str = Field(..., description="API Base URL")
    query: str = Field(..., description="User query")
    rephrasal_instructions: str = Field(...,
                                        description="System prompt for the LLM")
    request_headers: dict = Field(
        ..., description="Headers to be used to make request on the user's behalf")
    llm_config: LLMConfig
