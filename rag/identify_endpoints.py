import json
import dspy
from fastapi import APIRouter, Header
import requests
from rag.agents.endpoint_filterer_signature import ENDPOINT_FILTERER_AGENT, Endpoint
from rag.agents.rephraser_signature import REPHRASER_AGENT
from rag.query import get_all_endpoints, query_db, tool_factory
from schemas.raapi_schemas.query import Query
from schemas.raapi_schemas.rag import IdentifyEndpointsRequest, RunQuerySchema
from utils.api_key import validate_api_key
from rag.agents.request_generator import BodyGeneratorSignature, BodyInputModel, ParametersGeneratorSignature, ParametersInputModel, create_pydantic_model_from_json
from rag.agents.rephraser_signature import REPHRASER_AGENT, InputModel as RephraserInputModel
from rag.agents.endpoint_filterer_signature import ENDPOINT_FILTERER_AGENT, Endpoint, InputModel as EndpointFiltererInputModel
from rag.agents.final_response_signature import FINAL_RESPONSE_GENERATOR_AGENT, InputModel as FinalResponseGeneratorInputModel
from rag.router import run_query_router


@run_query_router.post("/identify-endpoints")
async def identify_endpoints(request: IdentifyEndpointsRequest, api_key: str = Header()):
    validate_api_key(api_key)

    api_base = request.api_base.rstrip('/')

    rephrased_query = request.query
    if request.rephraser:
        rephrased_agent_output = REPHRASER_AGENT(input=RephraserInputModel(
            rephrasal_instructions=request.rephrasal_instructions,
            query=request.query
        ))
        rephrased_query = rephrased_agent_output.output.rephrased_query

    search_result = await query_db(request=Query(integration_id=request.integration_id, query=rephrased_query))

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

    filtered_endpoints_output = ENDPOINT_FILTERER_AGENT(input=EndpointFiltererInputModel(
        query=rephrased_query,
        endpoints=[Endpoint(
            url=e['id'][e['id'].index("_")+1:],
            description=e['metadata']['description'],
            method=e['metadata']['method']
        ) for e in fetched_vectors]
    ))

    endpoints = filtered_endpoints_output.output.filtered_endpoints

    final_response = []
    for endpoint in endpoints:
        for fetched_vector in fetched_vectors:
            if endpoint.method + "_" + endpoint.url == fetched_vector['id']:
                data = dict(endpoint)
                data['id'] = fetched_vector['id']
                data['parameters'] = json.loads(
                    fetched_vector['metadata']['parameters'])
                data['body'] = json.loads(fetched_vector['metadata']['body'])
                data['response'] = json.loads(
                    fetched_vector['metadata']['response'])
                final_response.append(data)

    response = {}
    response['endpoints'] = final_response
    response['rephrased_query'] = rephrased_query
    return response


@run_query_router.post("/action")
async def run_endpoint(request: RunQuerySchema, api_key: str = Header(...)):
    validate_api_key(api_key)
    lm = dspy.LM(model=request.llm_config.llm,
                 api_key=request.llm_config.llm_api_key)
    dspy.configure(lm=lm)
    api_base = request.api_base.rstrip('/')
    all_endpoints = await get_all_endpoints(request.integration_id)
    tools = tool_factory(request.api_base, all_endpoints)
    params = {}
    body = {}
    response_content = {}

    vector = await identify_endpoints(IdentifyEndpointsRequest(
        api_base=api_base,
        integration_id=request.integration_id,
        query=request.query,
        rephrasal_instructions=request.rephrasal_instructions,
        rephraser=request.rephraser,
        llm_config=request.llm_config
    ), api_key=api_key)
    vector = vector['endpoints'][0]
    if vector['parameters']:
        PARAMETERS_GENERATOR_AGENT = dspy.ReAct(
            ParametersGeneratorSignature, tools=tools, max_iters=5)
        params_model = create_pydantic_model_from_json(
            vector['parameters'],
            "RequestParametersModel"
        )
        parameters = PARAMETERS_GENERATOR_AGENT(input=ParametersInputModel(
            query=request.query,
            request_parameters_schema=params_model.model_json_schema()[
                'properties']
        ))
        params = parameters.output.request_parameters

    # Generate body if needed
    if vector['body']:
        BODY_GENERATOR_AGENT = dspy.ReAct(
            BodyGeneratorSignature, tools=tools, max_iters=5)
        body_model = create_pydantic_model_from_json(
            vector['body'],
            "RequestBodyModel"
        )
        body_model_instance = BODY_GENERATOR_AGENT(input=BodyInputModel(
            query=request.query,
            request_body_schema=body_model.model_json_schema()['properties']
        ))
        body = body_model_instance.output.request_body

    # Make the HTTP request
    url = vector['id'][vector['id'].index("_") + 1:]
    method = vector['method']

    response = None
    if method == "GET":
        response = requests.get(
            url, params=params, headers=request.request_headers)
    elif method == "POST":
        response = requests.post(
            url, params=params, json=body, headers=request.request_headers)
    elif method == "PUT":
        response = requests.put(
            url, params=params, json=body, headers=request.request_headers)
    elif method == "DELETE":
        response = requests.delete(
            url, params=params, headers=request.request_headers)
    elif method == "HEAD":
        response = requests.head(
            url, params=params, headers=request.request_headers)

    response_content = response.json()
    print(response_content)
    final_response = FINAL_RESPONSE_GENERATOR_AGENT(input=FinalResponseGeneratorInputModel(
        query=request.query,
        structure_of_data=vector['response'],
        data=response_content
    ))

    natural_language_response = final_response.output.natural_language_response

    return dict(
        natural_language_response=natural_language_response,
        request={
            'endpoint': url,
            'method': method,
            'parameters': params,
            'body': body,
            'response': response_content
        }
    )
