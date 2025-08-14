"""
Endpoint service for handling endpoint identification and filtering operations.

This service handles the identification of relevant API endpoints based on user queries,
including query rephrasing, vector search, and endpoint filtering.
"""

import json
from typing import Dict, List, Any

from rag.agents.rephraser_signature import REPHRASER_AGENT, InputModel as RephraserInputModel
from rag.agents.endpoint_filterer_signature import ENDPOINT_FILTERER_AGENT, Endpoint, InputModel as EndpointFiltererInputModel
from rag.query import query_db
from schemas.raapi_schemas.query import Query


class EndpointService:
    """Service class for endpoint-related operations."""
    
    @staticmethod
    def _normalize_api_base(api_base: str) -> str:
        """Remove trailing slash from API base URL."""
        return api_base.rstrip('/')
    
    @staticmethod
    def _rephrase_query(query: str, rephraser: bool, rephrasal_instructions: str) -> str:
        """Rephrase the query if rephraser is enabled."""
        if not rephraser:
            return query
            
        rephrased_agent_output = REPHRASER_AGENT(input=RephraserInputModel(
            rephrasal_instructions=rephrasal_instructions,
            query=query
        ))
        return rephrased_agent_output.output.rephrased_query
    
    @staticmethod
    def _build_vector_data(search_result: List[Any], api_base: str) -> List[Dict[str, Any]]:
        """Build vector data from search results."""
        fetched_vectors = []
        for result in search_result:
            vector_data = {
                'id': f"{result.payload.get('method')}_{api_base}{result.payload.get('url')}",
                'metadata': {
                    'description': result.payload.get('description'),
                    'method': result.payload.get('method'),
                    'url': result.payload.get('url'),
                    'parameters': result.payload.get('parameters'),
                    'body': result.payload.get("body"),
                    'response': result.payload.get("response")
                }
            }
            fetched_vectors.append(vector_data)
        return fetched_vectors
    
    @staticmethod
    def _filter_endpoints(fetched_vectors: List[Dict], query: str) -> List[Endpoint]:
        """Filter endpoints based on the query."""
        endpoints = [
            Endpoint(
                url=e['id'][e['id'].index("_")+1:],
                description=e['metadata']['description'],
                method=e['metadata']['method']
            ) for e in fetched_vectors
        ]
        
        filtered_endpoints_output = ENDPOINT_FILTERER_AGENT(input=EndpointFiltererInputModel(
            query=query,
            endpoints=endpoints
        ))
        
        return filtered_endpoints_output.output.filtered_endpoints
    
    @staticmethod
    def _build_final_response(endpoints: List[Endpoint], fetched_vectors: List[Dict]) -> List[Dict]:
        """Build the final response by combining endpoints with their metadata."""
        final_response = []
        for endpoint in endpoints:
            for fetched_vector in fetched_vectors:
                if endpoint.method + "_" + endpoint.url == fetched_vector['id']:
                    data = dict(endpoint)
                    data['id'] = fetched_vector['id']
                    data['parameters'] = json.loads(fetched_vector['metadata']['parameters'])
                    data['body'] = json.loads(fetched_vector['metadata']['body'])
                    data['response'] = json.loads(fetched_vector['metadata']['response'])
                    final_response.append(data)
        return final_response
    
    @classmethod
    async def identify_endpoints(cls, integration_id: str, api_base: str, query: str, 
                                rephraser: bool, rephrasal_instructions: str) -> Dict[str, Any]:
        """Main method to identify relevant endpoints for a given query."""
        # Normalize API base
        normalized_api_base = cls._normalize_api_base(api_base)
        
        # Rephrase query if needed
        rephrased_query = cls._rephrase_query(query, rephraser, rephrasal_instructions)
        
        # Search for relevant endpoints
        search_result = await query_db(request=Query(
            integration_id=integration_id, 
            query=rephrased_query
        ))
        
        # Build vector data
        fetched_vectors = cls._build_vector_data(search_result, normalized_api_base)
        
        # Filter endpoints
        filtered_endpoints = cls._filter_endpoints(fetched_vectors, rephrased_query)
        
        # Build final response
        final_response = cls._build_final_response(filtered_endpoints, fetched_vectors)
        
        # Return the first (most relevant) endpoint instead of a list
        single_endpoint = final_response[0] if final_response else None
        
        return {
            'endpoint': single_endpoint,
            'rephrased_query': rephrased_query
        } 