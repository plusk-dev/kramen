from typing import List, Optional
from pydantic import BaseModel, Field
import dspy


class InputModel(BaseModel):
    query: str = Field(
        description=(
            "A user-defined query string that represents the information being searched for. "
            "This query could be a keyword, a phrase describing desired functionality, a method type, or any specific aspect "
            "of an endpoint's behavior. The query is used to filter the most suitable endpoint(s) from the provided list. "
            "For instance, a query like 'show cart details' would filter endpoints related to cart retrieval. "
            "Note: The query may include date/time information in brackets at the beginning (e.g., '[Current date and time: 2024-01-15 14:30:00 UTC]'). "
            "Use this temporal context if relevant to the query (e.g., for time-based operations, recent data, etc.), otherwise ignore it."
        )
    )
    workflow_instructions: Optional[str] = Field(
        description=(
            "Instructions to design the workflow of the steps."
        ),
        default=None
    )


class OutputModel(BaseModel):
    steps: List[str] = Field(
        description=(
            "A sequence of steps in which the user's query is divided. Each step must involve accessing exactly ONE platform/API. "
            "Each step should be a single, atomic action that can be executed via the /action endpoint. "
            "Steps should be ordered logically so that later steps can use the results from earlier steps as context. "
            "Every step should require interaction with a platform, and no step should perform only local computation. "
            "Examples:\n\n"
            "Query: 'Generate a report on all cancelled subscriptions and log them in Jira.'\n"
            "Steps:\n"
            "- 'Retrieve a list of all cancelled subscriptions along with their respective cancellation reasons from the subscription management system.'\n"
            "- 'Create a Jira ticket for each cancelled subscription, including the cancellation reason in the ticket description.'\n\n"
            "Query: 'Identify high-priority customer support tickets and notify the relevant team.'\n"
            "Steps:\n"
            "- 'Fetch the latest customer support tickets from Zendesk and filter those marked as high priority.'\n"
            "- 'Post a summary of high-priority tickets in the team's Slack channel.'\n\n"
            "Query: 'Summarize pending pull requests and notify developers.'\n"
            "Steps:\n"
            "- 'Retrieve all pending pull requests from GitHub, including their status and assigned reviewers.'\n"
            "- 'Send a summary of pending pull requests to the development team via Slack.'\n\n"
            "Query: 'Detect failed payment transactions and notify customers via email.'\n"
            "Steps:\n"
            "- 'Fetch failed payment transactions from Stripe within the last 24 hours.'\n"
            "- 'Send an email notification to affected customers using SendGrid.'\n\n"
            "Query: 'find my customers from stripe and list my repositories and tell me the count of each'\n"
            "Steps:\n"
            "- 'Fetch the list of customers from Stripe including their details'\n"
            "- 'Retrieve the list of repositories from the version control platform (e.g., GitHub) associated with the user's account.'\n\n"
            "IMPORTANT: Each step must be a single action on a single platform. Do not combine multiple platform actions in one step. "
            "The counting/analysis of results should be done within the step that retrieves the data, not as a separate step."
        )
    )


# New models for dynamic step generation
class DynamicStepInputModel(BaseModel):
    original_query: str = Field(
        description=(
            "The original user query that needs to be fulfilled. "
            "Note: The query may include date/time information in brackets at the beginning (e.g., '[Current date and time: 2024-01-15 14:30:00 UTC]'). "
            "Use this temporal context if relevant to the query (e.g., for time-based operations, recent data, etc.), otherwise ignore it."
        )
    )
    context_from_previous_steps: Optional[str] = Field(
        description="Context and results from previous steps that have been executed.",
        default=None
    )
    workflow_instructions: Optional[str] = Field(
        description="Instructions to design the workflow of the steps.",
        default=None
    )


class DynamicStepOutputModel(BaseModel):
    next_step: Optional[str] = Field(
        description=(
            "The next single step that should be executed to progress towards fulfilling the original query. "
            "This should be a single, atomic action that can be executed via the /action endpoint. "
            "\n\nSTOP IMMEDIATELY: If the original query has been fully addressed or satisfied, return null/None. "
            "Do NOT generate additional steps once the core request has been fulfilled. Evaluate carefully if "
            "the original query's requirements have been met based on the context from previous steps. "
            "\n\nThe step should take into account the context from previous steps and build upon their results. "
            "\n\nIMPORTANT: The step MUST be a concise, clear sentence with 10-15 words maximum. "
            "Make it short and sweet while still being descriptive and actionable. "
            "\n\nPLATFORM NAME REQUIREMENT: Always include the name of the platform on which the step is being performed in the step description. This is required to clearly identify which service will be used. COMPULSORY STEP."
            "\n\nCRITICAL RULE FOR MULTIPLE RESOURCES: When the query requires operating on multiple resources "
            "(create, update, delete, etc.) and the available API can only handle ONE resource at a time, "
            "you MUST generate separate steps for each individual resource. Do NOT try to process multiple "
            "resources in a single step if the API doesn't support bulk operations. "
            "\n\nKeep it concise but informative - short sentences that clearly explain the action."
        )
    )
    is_complete: bool = Field(
        description=(
            "Whether the original query has been fully addressed and no more steps are needed. "
            "Return true IMMEDIATELY when the query is complete - do not continue generating steps. "
            "Carefully evaluate if the original query's requirements have been satisfied based on "
            "the context from previous steps. Return false only if more steps are genuinely required."
        )
    )
    reasoning: str = Field(
        description=(
            "Brief explanation of why this step is needed or why the query is complete. "
            "This helps with debugging and understanding the decision-making process."
        )
    )


class DecomposerSignature(dspy.Signature):
    input: InputModel = dspy.InputField()
    output: OutputModel = dspy.OutputField()


class DynamicStepSignature(dspy.Signature):
    input: DynamicStepInputModel = dspy.InputField()
    output: DynamicStepOutputModel = dspy.OutputField()


DECOMPOSER_AGENT = dspy.Predict(DecomposerSignature)
DYNAMIC_STEP_AGENT = dspy.Predict(DynamicStepSignature)
