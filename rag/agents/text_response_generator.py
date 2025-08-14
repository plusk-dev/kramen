from typing import Any, Type
import dspy
from pydantic import BaseModel, Field

class InputModel(BaseModel):
    query: str = Field(
        ..., 
        description=(
            "User query. "
            "Note: The query may include date/time information in brackets at the beginning (e.g., '[Current date and time: 2024-01-15 14:30:00 UTC]'). "
            "Use this temporal context if relevant to the query (e.g., for time-based operations, recent data, etc.), otherwise ignore it."
        )
    )
    context: str = Field(description="Context for answering the query")

class OutputModel(BaseModel):
    response: str = Field(
        description="Response to the user's query in natural language.")

class TextResponseGenerator(dspy.Signature):
    input: InputModel = dspy.InputField()
    output: OutputModel = dspy.OutputField()

TEXT_RESPONSE_GENERATOR = dspy.Predict(TextResponseGenerator)
