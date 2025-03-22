from typing import Any, Type, Union
import dspy
from pydantic import BaseModel, Field

class InputModel(BaseModel):
    query: str = Field(
        ..., 
        description="The user's question or request, which requires a response based on the provided data."
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
    """
    A schema that defines how a final response is generated based on structured data input.
    """
    input: InputModel = dspy.InputField(
        description=(
            "The required input fields, including the user's query, data structure, and actual data, "
            "to generate a relevant response."
        )
    )
    output: OutputModel = dspy.OutputField(
        description=(
            "The output field representing the AI-generated natural language response based on the provided data."
        )
    )

# Instantiating the response generation agent
FINAL_RESPONSE_GENERATOR_AGENT = dspy.Predict(FinalResponseGeneratorSchema)
