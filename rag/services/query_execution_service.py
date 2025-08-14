"""
Query execution service for handling API request execution and response generation.

This service manages the execution of queries against identified endpoints,
including parameter generation, API calls, and natural language response generation.
"""

import json
import time
from typing import Dict, List, Any

import dspy
import requests

from rag.agents.final_response_signature import FINAL_RESPONSE_GENERATOR_AGENT, InputModel as FinalResponseGeneratorInputModel
from rag.agents.request_generator import (
    DataExtractorSignature,
    DataExtractorInputModel
)
from rag.query import get_all_endpoints, tool_factory
from config import LLM_API_KEYS


class QueryExecutionService:
    """Service class for query execution operations."""
    
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
    def _extract_data(schema: Dict, tools: List, query: str, schema_type: str, additional_context: Dict[str, Any] = None) -> Dict:
        """Extract structured data from query using the provided schema with strict validation."""
        if not schema:
            return {}
        
        # print(f"Extracting {schema_type} data")
        # print(f"Schema: {schema}")
        # print(f"Additional context: {additional_context}")
        
        # Enhance query with context if available
        enhanced_query = query
        if additional_context:
            context_str = "Previous steps results:\n"
            for step_key, step_data in additional_context.items():
                if step_key != "integration_manual":  # Skip manual in step results
                    context_str += f"{step_data['step']}: {str(step_data['response'])}\n"
            enhanced_query = f"{query}\n\n{context_str}"
            
            # Add integration manual if available
            if "integration_manual" in additional_context and additional_context["integration_manual"]:
                enhanced_query = f"{enhanced_query}\n\nIntegration Manual:\n{additional_context['integration_manual']}"
        
        data_extractor = dspy.Predict(DataExtractorSignature)
        result = data_extractor(input=DataExtractorInputModel(
            query=enhanced_query,
            schema=schema,
            schema_type=schema_type
        ))
        
        extracted_data = result.output.extracted_data
        # print(f"{schema_type} data extracted: {extracted_data}")
        
        # Validate that no extra fields were added
        if isinstance(extracted_data, dict) and isinstance(schema, list):
            schema_fields = {item.get('key', item.get('name', '')) for item in schema if item.get('key') or item.get('name')}
            extracted_fields = set(extracted_data.keys())
            extra_fields = extracted_fields - schema_fields
            
            if extra_fields:
                print(f"WARNING: Extra fields detected and will be removed: {extra_fields}")
                # Remove extra fields to enforce strict schema compliance
                extracted_data = {k: v for k, v in extracted_data.items() if k in schema_fields}
                print(f"Cleaned {schema_type} data: {extracted_data}")
        
        return extracted_data
    
    @staticmethod
    def _generate_parameters(vector: Dict, tools: List, query: str, additional_context: Dict[str, Any] = None) -> Dict:
        """Generate parameters for the API request using the unified data extractor."""
        return QueryExecutionService._extract_data(
            schema=vector['parameters'], 
            tools=tools, 
            query=query, 
            schema_type="parameters",
            additional_context=additional_context
        )
    
    @staticmethod
    def _generate_body(vector: Dict, tools: List, query: str, additional_context: Dict[str, Any] = None) -> Dict:
        """Generate body for the API request using the unified data extractor."""
        return QueryExecutionService._extract_data(
            schema=vector['body'], 
            tools=tools, 
            query=query, 
            schema_type="body",
            additional_context=additional_context
        )
    
    @staticmethod
    def _process_headers(headers: Dict) -> Dict:
        """Process headers to ensure all values are strings."""
        processed_headers = {}
        for key, value in headers.items():
            if isinstance(value, dict):
                # Convert dict values to JSON strings
                processed_headers[key] = json.dumps(value)
            elif isinstance(value, (list, tuple)):
                # Convert list/tuple values to JSON strings
                processed_headers[key] = json.dumps(value)
            else:
                # Keep other values as is (should be strings)
                processed_headers[key] = str(value)
        return processed_headers

    @staticmethod
    def _make_api_request(url: str, method: str, params: Dict, body: Dict, headers: Dict) -> requests.Response:
        """Make the actual API request based on the HTTP method."""
        # Process headers to ensure all values are strings
        processed_headers = QueryExecutionService._process_headers(headers)
        
        # Determine how to send the body based on Content-Type header
        content_type = processed_headers.get('Content-Type', '').lower()
        if 'x-www-form-urlencoded' in content_type:
            # Use data for form-urlencoded content
            body_param = {'data': body}
        else:
            # Use json for other content types (like application/json)
            body_param = {'json': body}
        
        method_handlers = {
            "GET": lambda: requests.get(url, params=params, headers=processed_headers),
            "POST": lambda: requests.post(url, params=params, headers=processed_headers, **body_param),
            "PUT": lambda: requests.put(url, params=params, headers=processed_headers, **body_param),
            "DELETE": lambda: requests.delete(url, params=params, headers=processed_headers),
            "HEAD": lambda: requests.head(url, params=params, headers=processed_headers)
        }
        
        handler = method_handlers.get(method.upper())
        if not handler:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        return handler()
    
    @staticmethod
    def _generate_natural_language_response(query: str, response_structure: Dict, response_data: Dict) -> str:
        """Generate natural language response from the API response."""
        final_response = FINAL_RESPONSE_GENERATOR_AGENT(input=FinalResponseGeneratorInputModel(
            query=query,
            structure_of_data=response_structure,
            data=response_data
        ))
        return final_response.output.natural_language_response
    
    @classmethod
    async def execute_query(cls, integration_id: str, api_base: str, query: str, 
                           vector: Dict, request_headers: Dict, llm_config: Any, 
                           natural_language_response: bool = False, additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main method to execute a query against an identified endpoint."""
        start_time = time.time()
        
        # Configure DSPy
        cls._configure_dspy(llm_config)
        
        # Setup tools
        all_endpoints = await get_all_endpoints(integration_id)
        tools = tool_factory(api_base, all_endpoints)
        
        # Generate parameters and body with context
        params = cls._generate_parameters(vector, tools, query, additional_context)
        body = cls._generate_body(vector, tools, query, additional_context)

        # Print params for debugging
        print(f"[DEBUG] Params being sent to requests: {params}")
        
        # Make API request
        api_start_time = time.time()
        url = vector['id'][vector['id'].index("_") + 1:]
        method = vector['method']
        
        response = cls._make_api_request(url, method, params, body, request_headers)
        
        api_latency = time.time() - api_start_time
        response_content = response.json()
        
        # Calculate latencies
        total_latency = time.time() - start_time
        kramen_latency = total_latency - api_latency
        
        result = {
            'request': {
                'endpoint': vector,
                'parameters': params,
                'body': body,
                'response': response_content
            },
            'api_latency': api_latency,
            'kramen_latency': kramen_latency
        }
        
        # Generate natural language response only if requested
        if natural_language_response:
            result['natural_language_response'] = cls._generate_natural_language_response(
                query, vector['response'], response_content
            )
        
        return result 