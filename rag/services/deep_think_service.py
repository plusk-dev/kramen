"""
Deep thinking service for handling multi-step query execution.

This service manages complex queries that require decomposition into multiple steps,
where each step calls a single platform's API via the /action endpoint.
"""

import json
from typing import Dict, List, Any, Optional, Tuple

import dspy

from rag.agents.decomposer_agent import DECOMPOSER_AGENT, InputModel as DecomposerInputModel, DYNAMIC_STEP_AGENT, DynamicStepInputModel
from rag.agents.integration_picker import INTEGRATION_PICKER, InputModel as IntegrationPickerInputModel
from rag.agents.text_response_generator import TEXT_RESPONSE_GENERATOR, InputModel as TextInputModel
from models import session, Integration
from utils.general import sqlalchemy_object_to_dict
from config import LLM_API_KEYS


class DeepThinkService:
    """Service class for deep thinking operations."""

    @staticmethod
    def _configure_dspy(llm_config: Any) -> None:
        """Configure DSPy with the provided LLM configuration."""
        api_key = LLM_API_KEYS.get(llm_config.llm, "")
        if not api_key:
            raise ValueError(f"No API key found for LLM: {llm_config.llm}")

        lm = dspy.LM(
            model=llm_config.llm,
            api_key=api_key
        )
        dspy.configure(lm=lm)

    @staticmethod
    def _get_integrations(integration_uuids: List[str]) -> List[Dict]:
        """Retrieve integrations from the database."""
        return [
            sqlalchemy_object_to_dict(i)
            for i in session.query(Integration).filter(
                Integration.uuid.in_(integration_uuids)
            ).all()
        ]

    @staticmethod
    def _load_integration_manual(integration_uuid: str) -> str:
        """Load the manual for a given integration UUID."""
        from pathlib import Path
        manual_path = Path(__file__).parent.parent.parent / \
            "proxies" / "manuals" / f"{integration_uuid}.md"

        if manual_path.exists():
            try:
                with open(manual_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Error loading manual for {integration_uuid}: {e}")
                return ""
        else:
            print(f"No manual found for integration {integration_uuid}")
            return ""

    @staticmethod
    def decompose_query(query: str, integration_uuids: List[str] = None) -> List[str]:
        """Decompose the query into single-platform steps."""
        # Fetch workflow instructions from integration manuals
        workflow_instructions = ""
        if integration_uuids:
            for integration_uuid in integration_uuids:
                manual = DeepThinkService._load_integration_manual(
                    integration_uuid)
                if manual:
                    workflow_instructions += f"\nIntegration {integration_uuid} manual:\n{manual}\n"

        decomposed = DECOMPOSER_AGENT(input=DecomposerInputModel(
            query=query,
            workflow_instructions=workflow_instructions if workflow_instructions else None
        ))
        return decomposed.output.steps

    @staticmethod
    def generate_next_step(original_query: str, context_data: Dict, integration_uuids: List[str] = None) -> Tuple[Optional[str], bool, str]:
        """
        Generate the next step dynamically based on context from previous steps.

        Args:
            original_query: The original user query
            context_data: Dictionary containing context from previous steps
            integration_uuids: List of available integration UUIDs

        Returns:
            Tuple of (next_step, is_complete, reasoning)
        """
        # Build context string from previous steps
        context_str = ""
        if context_data:
            for _, step_data in context_data.items():
                context_str += f"{step_data['step']}\n"
                context_str += f"Integration: {step_data['integration_uuid']}\n"
                context_str += f"Result: {str(step_data['response'])}\n\n"

        # Fetch workflow instructions from integration manuals
        workflow_instructions = ""
        if integration_uuids:
            for integration_uuid in integration_uuids:
                manual = DeepThinkService._load_integration_manual(
                    integration_uuid)
                if manual:
                    workflow_instructions += f"\nIntegration {integration_uuid} manual:\n{manual}\n"

        # Generate the next step
        result = DYNAMIC_STEP_AGENT(input=DynamicStepInputModel(
            original_query=original_query,
            context_from_previous_steps=context_str if context_str else None,
            workflow_instructions=workflow_instructions if workflow_instructions else None
        ))

        return result.output.next_step, result.output.is_complete, result.output.reasoning

    @staticmethod
    def select_integration_for_step(step: str, integrations: List[Dict]) -> str:
        """Select the appropriate integration for a step."""
        id_agent = INTEGRATION_PICKER(input=IntegrationPickerInputModel(
            query=step,
            integrations=integrations
        ))
        return id_agent.output.uuid

    @staticmethod
    def build_context_from_response(step: str, response: Dict) -> str:
        """Build context string from step and response."""
        return f"Step: {step}\nResult: {str(response.get('request', {}).get('response', response))}\n\n"

    @staticmethod
    def generate_final_response(query: str, context_data: Dict) -> str:
        """Generate the final text response from dict-based context data."""
        # Convert context data to a readable format for the text generator
        context_str = ""
        for step_key, step_data in context_data.items():
            context_str += f"Step: {step_data['step']}\nResult: {str(step_data['response'])}\n\n"

        res = TEXT_RESPONSE_GENERATOR(input=TextInputModel(
            query=query,
            context=context_str
        ))
        return res.output.response

    @classmethod
    def setup_deep_think(cls, llm_config: Any, integration_uuids: List[str]) -> List[Dict]:
        """Setup the deep thinking environment."""
        cls._configure_dspy(llm_config)
        return cls._get_integrations(integration_uuids)
