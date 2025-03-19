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


class OutputModel(BaseModel):
    steps: List[str] = Field(
        description=(
            "A sequence of steps in which the user's query is divided. Each step must involve accessing a platform. "
            "Reading,Filtering, processing, or analyzing data should happen within the step that retrieves it, not in separate steps. "
            "Every step should require interaction with a platform, and no step should perform only local computation. "
            "Examples:\n\n"
            "Query: 'Generate a report on all cancelled subscriptions and log them in Jira.'\n"
            "Steps:\n"
            "- 'Retrieve a list of all cancelled subscriptions along with their respective cancellation reasons from the subscription management system.'\n"
            "- 'Create a Jira ticket for each cancelled subscription, including the cancellation reason in the ticket description.'\n\n"
            "Query: 'Identify high-priority customer support tickets and notify the relevant team.'\n"
            "Steps:\n"
            "- 'Fetch the latest customer support tickets from Zendesk and filter those marked as high priority.'\n"
            "- 'Post a summary of high-priority tickets in the team’s Slack channel.'\n\n"
            "Query: 'Summarize pending pull requests and notify developers.'\n"
            "Steps:\n"
            "- 'Retrieve all pending pull requests from GitHub, including their status and assigned reviewers.'\n"
            "- 'Send a summary of pending pull requests to the development team via Slack.'\n\n"
            "Query: 'Detect failed payment transactions and notify customers via email.'\n"
            "Steps:\n"
            "- 'Fetch failed payment transactions from Stripe within the last 24 hours.'\n"
            "- 'Send an email notification to affected customers using SendGrid.'"
        )
    )


class DecomposerSignature(dspy.Signature):

    input: InputModel = dspy.InputField()
    output: OutputModel = dspy.OutputField()


DECOMPOSER_AGENT = dspy.Predict(DecomposerSignature)
