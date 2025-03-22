from typing import Any, Type
import dspy
from pydantic import BaseModel, Field

class InputModel(BaseModel):
    query: str = Field(..., description="User query")
    context: str = Field(description="Context for answering the query")

class OutputModel(BaseModel):
    response: str = Field(
        description="Response to the user's query in natural language.")

class TextResponseGenerator(dspy.Signature):
    input: InputModel = dspy.InputField()
    output: OutputModel = dspy.OutputField()

TEXT_RESPONSE_GENERATOR = dspy.Predict(TextResponseGenerator)
