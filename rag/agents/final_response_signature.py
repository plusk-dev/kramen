from typing import Any, Type
import dspy
from pydantic import BaseModel, Field

class InputModel(BaseModel):
    query: str = Field(..., description="User query")
    structure_of_data: Any = Field(..., description="Structure of the data that you will use to answer the user query")
    data: Any = Field(..., description="Data that you will use to answer the user's query")


class OutputModel(BaseModel):
    natural_language_response: str = Field(
        description="Response to the user's query in natural language.")


# def generate_custom_final_response_agent(input_model: Type[BaseModel]):

class FinalResponseGeneratorSchema(dspy.Signature):
    input: InputModel = dspy.InputField()
    output: OutputModel = dspy.OutputField()

FINAL_RESPONSE_GENERATOR_AGENT = dspy.Predict(FinalResponseGeneratorSchema)
