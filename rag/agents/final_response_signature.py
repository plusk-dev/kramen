from typing import Any, Type, Union
import dspy
from pydantic import BaseModel, Field

class InputModel(BaseModel):
    query: str = Field(
        ..., 
        description=(
            "The user's question or request, which requires a response based on the provided data. "
            "Note: The query may include date/time information in brackets at the beginning (e.g., '[Current date and time: 2024-01-15 14:30:00 UTC]'). "
            "Use this temporal context if relevant to the query (e.g., for time-based operations, recent data, etc.), otherwise ignore it."
        )
    )
    structure_of_data: Union[dict, list] = Field(
        ..., 
        description=(
            "A well-defined structure (dictionary or list) representing how the data is organized. "
            "This helps in understanding how to extract relevant information efficiently."
        )
    )
    data: Any = Field(
        ..., 
        description=(
            "The actual dataset (structured as per 'structure_of_data') that will be used to generate "
            "a meaningful response to the user's query."
        )
    )

class OutputModel(BaseModel):
    natural_language_response: str = Field(
        description=(
            "A well-structured, informative, and concise response to the user's query in natural language. "
            "Ensure clarity and completeness in addressing the query."
        )
    )

class FinalResponseGeneratorSchema(dspy.Signature):
    input: InputModel = dspy.InputField(
        description=(
            "The required input fields, including the user's query, data structure, and actual data, "
            "to generate a relevant response."
        )
    )
    output: OutputModel = dspy.OutputField(
        description=(
            "The output field representing the AI-generated natural language response based on the provided data. This should contain all the details given to you, including every single thing. Like unique identifiers if provided, all kinds of attributes, etc."
        )
    )

# Instantiating the response generation agent
FINAL_RESPONSE_GENERATOR_AGENT = dspy.Predict(FinalResponseGeneratorSchema)
