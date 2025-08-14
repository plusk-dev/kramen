"""
FastAPI endpoints for RAG-based query operations.

This module contains the FastAPI router endpoints that handle HTTP requests
for endpoint identification, query execution, and deep thinking operations.
"""

import json
import os
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from rag.services import EndpointService, QueryExecutionService, DeepThinkService
from schemas.raapi_schemas.rag import DeepThinkSchema, IdentifyEndpointsRequest, RunQuerySchema, GenerateStepsSchema
from utils.general import append_datetime_to_query

# Router initialization
run_query_router = APIRouter()


def load_integration_manual(integration_uuid: str) -> str:
    """Load the manual for a given integration UUID."""
    manual_path = Path(__file__).parent.parent / "proxies" / "manuals" / f"{integration_uuid}.md"
    
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


@run_query_router.post("/identify-endpoints")
async def identify_endpoints(request: IdentifyEndpointsRequest):
    """Identify relevant endpoints for a given query."""
    # Append datetime context to query
    query_with_datetime = append_datetime_to_query(request.query)
    
    return await EndpointService.identify_endpoints(
        integration_id=request.integration_id,
        api_base=request.api_base,
        query=query_with_datetime,
        rephraser=request.rephraser,
        rephrasal_instructions=request.rephrasal_instructions
    )


@run_query_router.post("/generate-steps")
async def generate_steps(request: GenerateStepsSchema):
    """Generate steps for a given query based on available integrations."""
    # Setup deep thinking environment
    integrations = DeepThinkService.setup_deep_think(
        request.llm_config, 
        request.integration_ids
    )
    
    # Append datetime context to query
    query_with_datetime = append_datetime_to_query(request.query)
    
    # Decompose the query into single-platform steps
    steps = DeepThinkService.decompose_query(
        query=query_with_datetime,
        integration_uuids=request.integration_ids
    )
    
    # Associate each step with an integration
    steps_with_integrations = []
    for step in steps:
        integration_uuid = DeepThinkService.select_integration_for_step(step, integrations)
        steps_with_integrations.append({
            "step": step,
            "integration_uuid": integration_uuid
        })
    
    return {
        "steps": steps_with_integrations,
        "integrations": integrations,
        "query": request.query
    }


@run_query_router.post("/action")
async def run_endpoint(request: RunQuerySchema, _called_from_deep: bool = False):
    """Execute a query against the identified endpoint."""
    # Setup LM environment if called individually (not from deep)
    if not _called_from_deep:
        DeepThinkService.setup_deep_think(
            request.llm_config, 
            [request.integration_id]
        )
    
    # Append datetime context to query
    query_with_datetime = append_datetime_to_query(request.query)
    
    # First identify endpoints
    retrieved_vectors = await EndpointService.identify_endpoints(
        integration_id=request.integration_id,
        api_base=request.api_base,
        query=query_with_datetime,
        rephraser=request.rephraser,
        rephrasal_instructions=request.rephrasal_instructions
    )
    print(retrieved_vectors)
    
    # Get the identified endpoint
    vector = retrieved_vectors['endpoint']
    
    # Execute the query
    result = await QueryExecutionService.execute_query(
        integration_id=request.integration_id,
        api_base=request.api_base,
        query=query_with_datetime,
        vector=vector,
        request_headers=request.request_headers,
        llm_config=request.llm_config,
        natural_language_response=request.natural_language_response,
        additional_context=request.additional_context
    )
    
    # Add rephrased query to the result
    result['rephrased_query'] = retrieved_vectors['rephrased_query']
    result["request"].pop("endpoint")
    return result


async def deep_stream_generator(request: DeepThinkSchema):
    """Generator function that yields streaming data for deep thinking query."""
    # Setup deep thinking environment
    integrations = DeepThinkService.setup_deep_think(
        request.llm_config, 
        request.integrations
    )

    # Append datetime context to query
    query_with_datetime = append_datetime_to_query(request.query)

    context_data = {}  # Store raw response data as dict
    executed_steps = []
    step_counter = 0
    max_steps = 7  # Safety limit to prevent infinite loops

    # Yield initial metadata
    yield json.dumps({
        "type": "metadata",
        "query": request.query,
        "integrations": integrations,
        "max_steps": max_steps
    }) + "\n"

    # Generate and execute steps dynamically
    while step_counter < max_steps:
        step_counter += 1
        
        # Generate the next step based on current context
        next_step, is_complete, reasoning = DeepThinkService.generate_next_step(
            original_query=query_with_datetime,
            context_data=context_data,
            integration_uuids=request.integrations
        )
        
        # If the agent determines we're complete or no next step is needed
        if is_complete or next_step is None:
            break
        
        # Select integration for this step
        integration_uuid = DeepThinkService.select_integration_for_step(next_step, integrations)
        
        # Find integration name for display
        integration_name = integration_uuid
        for integration in integrations:
            if integration.get('uuid') == integration_uuid:
                integration_name = integration.get('name', integration_uuid)
                break
        
        # Yield step start event
        yield json.dumps({
            "type": "step_start",
            "step_number": step_counter,
            "step": next_step,
            "integration_uuid": integration_uuid,
            "integration_name": integration_name,
            "reasoning": reasoning
        }) + "\n"
        
        print(f"{next_step} [{integration_name}]")
        
        # Load the manual for this integration
        integration_manual = load_integration_manual(integration_uuid)

        # Execute the step via /action endpoint
        result = await run_endpoint(RunQuerySchema(
            rephraser=request.rephraser,
            rephrasal_instructions=request.rephrasal_instructions,
            integration_id=integration_uuid,
            api_base=request.api_base.get(integration_uuid, ""),
            request_headers=request.request_headers.get(integration_uuid, {}),
            additional_context={
                **context_data,  # Pass raw response data from previous steps
                "integration_manual": integration_manual  # Add the manual to context
            },
            llm_config=request.llm_config,
            query=next_step,
            natural_language_response=True  # Get natural language response for streaming
        ), _called_from_deep=True)

        # Store the raw response data for the next step
        context_data[f"step_{step_counter}"] = {
            'step': next_step,
            'step_number': step_counter,
            'response': result.get('request', {}).get('response', result),
            'integration_uuid': integration_uuid,
            'manual_used': bool(integration_manual),
            'reasoning': reasoning
        }
        
        executed_steps.append({
            "step": next_step,
            "integration_uuid": integration_uuid
        })

        # Yield step completion event with natural language response
        yield json.dumps({
            "type": "step_complete",
            "step_number": step_counter,
            "step": next_step,
            "integration_uuid": integration_uuid,
            "integration_name": integration_name,
            "response": result,
            "natural_language_response": result.get('natural_language_response', ''),
            "manual_used": bool(integration_manual),
            "reasoning": reasoning
        }) + "\n"

    # Generate final natural language response using the accumulated context data
    final_response = DeepThinkService.generate_final_response(query_with_datetime, context_data)

    # Yield final response
    yield json.dumps({
        "type": "final_response",
        "final_response": final_response,
        "natural_language_response": final_response,
        "total_steps": len(executed_steps),
        "executed_steps": executed_steps
    }) + "\n"

    # Yield completion event
    yield json.dumps({
        "type": "complete"
    }) + "\n"


@run_query_router.post("/deep")
async def deep(request: DeepThinkSchema):
    """Execute a deep thinking query that may require multiple steps with streaming response."""
    return StreamingResponse(
        deep_stream_generator(request),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    ) 