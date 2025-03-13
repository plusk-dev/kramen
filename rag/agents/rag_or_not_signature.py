from pydantic import BaseModel, Field
import dspy


class InputModel(BaseModel):
    query: str = Field(
        description=(
            "The user's input query as a plain text string. "
            "This query may represent a question, command, or statement that the system "
            "needs to analyze to decide if external data sources are required to generate an appropriate response."
        )
    )


class OutputModel(BaseModel):
    use_rag_or_not: bool = Field(
        description=(
            "A boolean value indicating whether retrieval-augmented generation (RAG) is required. "
            "Set to True if the query involves topics, data, or context beyond the model's internal knowledge base, "
            "and external sources must be consulted. Set to False if the query can be answered entirely using "
            "pretrained knowledge without requiring external data."
        )
    )


class RAGOrNotSignature(dspy.Signature):
    """
    Determines whether a query should be handled by a general-purpose LLM or a RAG system.

    Decision-making criteria:
    - General or conversational queries (e.g., "Hello", "How are you?") are handled by the LLM.
    - Specific or data-dependent queries (e.g., "What is the total cost of products in my cart?") require RAG.

    Input:
        query: The user's input query as a string.

    Output:
        should_use_rag: A boolean value.
            - True: The query is specific and requires RAG.
            - False: The query is general and can be answered directly by the LLM.

    Example:
        Input: "Hello"
        Output: False

        Input: "What is the delivery status of my last order?"
        Output: True
    """
    input: InputModel = dspy.InputField()
    output: OutputModel = dspy.OutputField()

