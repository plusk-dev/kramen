from pydantic import BaseModel, Field
import dspy


class InputModel(BaseModel):
    """
    Represents the structure of the input data for the query rephrasing process.
    """
    rephrasal_instructions: str = Field(
        ...,
        description=(
            "Instructions to keep in mind"
        )
    )
    query: str = Field(
        ...,
        description=(
            "Query to be rephrased"
        )
    )


class OutputModel(BaseModel):
    rephrased_query: str = Field(
        ...,
        description=(
            "Rephrase the query into a slightly more formal and technical way."
        )
    )


class QueryRephraseSignature(dspy.Signature):
    """
    Defines the input-output schema for a system that rephrases user queries to make them suitable for API documentation.

    The input specifies the query that needs rephrasing, while the output includes both the rephrased query 
    and the system prompt, which provides guidance for generating the rephrased query. This schema helps ensure 
    consistency and quality in how user queries are transformed into documentation-ready statements.

    - **Input**: A model containing the user's query as a raw text string. The input is analyzed and transformed 
      to align with the specific needs of API documentation, emphasizing clarity and conciseness.
    - **Output**: A model containing:
        - **System Prompt**: Instructions or guidelines for rephrasing the query.
        - **Rephrased Query**: The concise and polished version of the query, designed to fit seamlessly 
          into API documentation.

    This schema is useful in scenarios where user input needs to be reformatted or optimized for technical contexts, 
    ensuring that the final output adheres to predefined standards and usability goals.
    """
    input: InputModel = dspy.InputField()
    output: OutputModel = dspy.OutputField()


REPHRASER_AGENT = dspy.Predict(QueryRephraseSignature)
