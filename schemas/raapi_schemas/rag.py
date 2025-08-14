from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    llm: str = Field(default="gpt-4o-mini", description="Identifier for the LLM")


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
    rephrasal_instructions: str | None = Field(...,
                                        description="System prompt for the LLM")
    request_headers: dict = Field(
        ..., description="Headers to be used to make request on the user's behalf")
    additional_context: Dict[str, Any] = Field(
        description="Additional context for the query", default={})
    llm_config: LLMConfig
    natural_language_response: bool = Field(
        default=False, description="Whether to generate a natural language response from the API response")


class GenerateStepsSchema(BaseModel):
    query: str = Field(..., description="The query to decompose into steps")
    integration_ids: List[str] = Field(..., description="List of integration IDs to consider when generating steps")
    llm_config: LLMConfig


class DeepThinkSchema(BaseModel):
    rephraser: bool = Field(
        ..., description="A flag to indicate whether the integration should rephrase the query before processing.")
    # Fixed this line
    api_base: dict = Field(..., description="API Base URL")
    query: str = Field(..., description="User query")
    rephrasal_instructions: str = Field(...,
                                        description="System prompt for the LLM")
    request_headers: dict = Field(
        ..., description="Headers to be used to make request on the user's behalf")
    additional_context: Dict[str, Any] = Field(
        description="Additional context for the query", default={})
    integrations: List[str] = Field(...,
                                    description="List of integrations to be used")
    llm_config: LLMConfig


class EditVectorSchema(BaseModel):
    integration_id: str = Field(..., description="ID of the integration")
    new_metadata: dict = Field(..., description="new metadata")
