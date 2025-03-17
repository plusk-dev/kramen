from typing import List
from pydantic import BaseModel, Field
import dspy


# lm = dspy.LM('groq/gemma2-9b-it',
#              api_key='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')
# dspy.configure(lm=lm)


class Endpoint(BaseModel):
    url: str = Field(
        description="The URL of the API endpoint, representing the path where the endpoint can be accessed. "
                    "It should follow standard URL conventions and be unique to identify specific functionality."
    )
    description: str = Field(
        description="A detailed and comprehensive explanation of what the endpoint does. "
                    "This should clearly state the endpoint's purpose, expected behavior, "
                    "and any additional context to help in deciding its relevance."
    )
    method: str = Field(
        description="The HTTP method used for this endpoint, such as GET, POST, PUT, or DELETE. "
                    "The method defines the type of operation performed by the endpoint, e.g., "
                    "fetching data (GET), creating new entries (POST), updating existing entries (PUT), or deleting entries (DELETE)."
    )


# Input model with an array of API endpoints and a query
class InputModel(BaseModel):
    endpoints: List[Endpoint] = Field(
        description=(
            "Answer with a non-empty python array of endpoint URLs only that can possibly answer the query even if its vague. "
        )
    )
    query: str = Field(
        description=(
            "A user-defined query string that represents the information being searched for. "
            "This query could be a keyword, a phrase describing desired functionality, a method type, or any specific aspect "
            "of an endpoint's behavior. The query is used to filter the most suitable endpoint(s) from the provided list. "
            "For instance, a query like 'show cart details' would filter endpoints related to cart retrieval."
        )
    )


# Output model returning the filtered array of API endpoints
class OutputModel(BaseModel):
    filtered_endpoints: List[Endpoint] = Field(
        description=(
            "A list of endpoint objects selected by analyzing the descriptions of all available endpoints. "
            "The filtering process focuses primarily on the endpoint descriptions to determine potential matches to the user's query. "
            "Absolute matches are not required; endpoints that can potentially address the query based on their descriptions are included. "
            "The list ensures that relevant or even loosely related endpoints are returned to maximize the chances of fulfilling the user's request."
            "RETURN ONLY 1 ENDPOINT USING THE ABOVE INSTRUCTIONS"
        )
    )


class ArrayAnswerSignature(dspy.Signature):

    input: InputModel = dspy.InputField()
    output: OutputModel = dspy.OutputField()


ENDPOINT_FILTERER_AGENT = dspy.Predict(ArrayAnswerSignature)

# # Example query to match an endpoint
# query_example = "Retrieve orders for the user"

# # Creating input data for the agent
# input_data = InputModel(
#     endpoints=[
#         Endpoint(
#             url="http://127.0.0.1:5000/orders/my",
#             description="Retrieves all orders placed by the current logged-in user.",
#             method="GET"
#         ),
#         Endpoint(
#             url="http://127.0.0.1:5000/orders",
#             description="Places a new order using the user's cart details.",
#             method="POST"
#         ),
#         Endpoint(
#             url="http://127.0.0.1:5000/products",
#             description="Retrieves the list of all available products.",
#             method="GET"
#         )
#     ],
#     query=query_example
# )

# # Invoking the AI agent
# result = ENDPOINT_FILTERER_AGENT(input=input_data)

# # Printing the filtered endpoints
# print(result)
