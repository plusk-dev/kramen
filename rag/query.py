from fastapi import HTTPException
from fastembed import LateInteractionTextEmbedding, SparseTextEmbedding, TextEmbedding
from qdrant_client import models
import requests
from typing import List, Callable
from qdrant_client.models import ScoredPoint
from schemas.raapi_schemas.query import Query
from utils.upsert import qdrant_client
import json

from config import DENSE_EMBEDDING_MODEL, LATE_EMBEDDING_MODEL, SPARSE_EMBEDDING_MODEL


dense_embedding_model = TextEmbedding(
    f"sentence-transformers/{DENSE_EMBEDDING_MODEL}")
bm25_embedding_model = SparseTextEmbedding(
    f"Qdrant/{SPARSE_EMBEDDING_MODEL}")
late_interaction_embedding_model = LateInteractionTextEmbedding(
    f"colbert-ir/{LATE_EMBEDDING_MODEL}")


async def query_db(request: Query):
    """
    Run a query against the vector database using multiple embedding models.
    """
    try:
        dense_query_vector = next(
            dense_embedding_model.query_embed(request.query))
        sparse_query_vector = next(
            bm25_embedding_model.query_embed(request.query))
        late_query_vector = next(
            late_interaction_embedding_model.query_embed(request.query))

        prefetch = [
            models.Prefetch(
                query=dense_query_vector,
                using=DENSE_EMBEDDING_MODEL,
                limit=20,
            ),
            models.Prefetch(
                query=models.SparseVector(**sparse_query_vector.as_object()),
                using=SPARSE_EMBEDDING_MODEL,
                limit=20,
            ),
            models.Prefetch(
                query=late_query_vector,
                using=LATE_EMBEDDING_MODEL,
                limit=20,
            ),
        ]

        points = qdrant_client.query_points(
            request.integration_id,
            prefetch=prefetch,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            with_payload=True,
            limit=5,
        )

        return points.points

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_all_endpoints(integration_id: str):
    points = qdrant_client.query_points(
        collection_name=integration_id, with_payload=True)
    return points.points


def tool_factory(api_base: str, endpoints: List[ScoredPoint]) -> List[Callable]:
    """
    Creates a list of callable functions for GET endpoints that are marked as tools.
    Each function makes an HTTP request to the corresponding endpoint.

    Args:
        endpoints: A list of ScoredPoint objects representing the endpoints.

    Returns:
        A list of callable functions, each corresponding to a GET tool endpoint.
    """
    tools = []

    for endpoint in endpoints:
        # Check if the endpoint is a tool and uses the GET method
        if endpoint.payload.get('tool', False) and endpoint.payload['method'] == 'GET':
            # Extract relevant information from the payload
            url = endpoint.payload['url']
            description = endpoint.payload['description']
            parameters_str = endpoint.payload.get(
                'parameters', '[]')  # Default to '[]' if not present

            # Parse the parameters field from a JSON string to a Python object
            try:
                parameters = json.loads(parameters_str)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Failed to parse 'parameters' field for endpoint {url}: {e}")

            # Extract parameter names and their required status
            param_definitions = []
            for param in parameters:
                param_name = param['name']
                # Default to False if 'required' is not specified
                is_required = param.get('required', False)
                if is_required:
                    # Required parameters have no default value
                    param_definitions.append(param_name)
                else:
                    # Optional parameters default to None
                    param_definitions.append(f"{param_name}=None")

            # Dynamically create the function with explicit arguments
            def create_tool_function(url, description, param_definitions):
                # Define the function signature dynamically
                arg_list = ", ".join(param_definitions)
                param_names = [param.split('=')[0]
                               for param in param_definitions]
                print(arg_list)
                function_code = f"""
def tool_function({arg_list}):
    \"\"\"
    {description}
    \"\"\"
    params = {{}}
    # Explicitly add arguments to the params dictionary
    for param in {param_names}:
        if locals().get(param) is not None:
            params[param] = locals()[param]
    try:
        print("Making request to:", url)
        print("Request parameters:", params)
        response = requests.get(api_base + url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except Exception as e:
        print(f"Error making request: {{e}}")
        return {{"error": str(e)}}
"""
                # Execute the function code in a local namespace
                local_namespace = {}
                exec(function_code, {
                     'requests': requests, 'url': url, 'api_base': api_base}, local_namespace)
                return local_namespace['tool_function']

            # Create the tool function and add it to the list
            tool_function = create_tool_function(
                url, description, param_definitions)
            tools.append(tool_function)

    return tools
