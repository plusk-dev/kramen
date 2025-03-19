from typing import List
from pydantic import BaseModel, Field
import dspy


class InputModel(BaseModel):
    query: str = Field(
        description=(
            "A user-defined query string that represents the information being searched for. "
            "This query could be a keyword, a phrase describing desired functionality, a method type, or any specific aspect "
            "of an endpoint's behavior. The query is used to filter the most suitable endpoint(s) from the provided list. "
            "For instance, a query like 'show cart details' would filter endpoints related to cart retrieval."
        )
    )
    integrations: List[dict] = Field(
        description="List of integrations available")


class OutputModel(BaseModel):
    uuid: str = Field(
        description="uuid of the integration that can be used to answer this query.")


class IntegrationPickerSignature(dspy.Signature):

    input: InputModel = dspy.InputField()
    output: OutputModel = dspy.OutputField()


INTEGRATION_PICKER = dspy.Predict(IntegrationPickerSignature)
