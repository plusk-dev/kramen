import time
import json
import dspy
from fastapi import APIRouter, Header
import requests
from rag.agents.decomposer_agent import DECOMPOSER_AGENT, InputModel as DecomposerInputModel
from rag.agents.endpoint_filterer_signature import ENDPOINT_FILTERER_AGENT, Endpoint
from rag.agents.integration_picker import INTEGRATION_PICKER, InputModel as IntegrationPickerInputModel
from rag.agents.rephraser_signature import REPHRASER_AGENT
from rag.agents.text_response_generator import TEXT_RESPONSE_GENERATOR, InputModel as TextInputModel
from rag.query import get_all_endpoints, query_db, tool_factory
from schemas.raapi_schemas.query import Query
from schemas.raapi_schemas.rag import DeepThinkSchema, IdentifyEndpointsRequest, RunQuerySchema
from utils.api_key import validate_api_key
from rag.agents.request_generator import BodyGeneratorSignature, BodyInputModel, ParametersGeneratorSignature, ParametersInputModel, create_pydantic_model_from_json
from rag.agents.rephraser_signature import REPHRASER_AGENT, InputModel as RephraserInputModel
from rag.agents.endpoint_filterer_signature import ENDPOINT_FILTERER_AGENT, Endpoint, InputModel as EndpointFiltererInputModel
from rag.agents.final_response_signature import FINAL_RESPONSE_GENERATOR_AGENT, InputModel as FinalResponseGeneratorInputModel
from models import session, Integration
from utils.general import sqlalchemy_object_to_dict

run_query_router = APIRouter()


@run_query_router.post("/identify-endpoints")
async def identify_endpoints(request: IdentifyEndpointsRequest, api_key: str = Header()):
    await validate_api_key(api_key)

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
    start_time = time.time()  # Start timing the entire function

    lm = dspy.LM(model=request.llm_config.llm,
                 api_key=request.llm_config.llm_api_key)
    dspy.configure(lm=lm)
    print(request.request_headers)
    api_base = request.api_base.rstrip('/')
    all_endpoints = await get_all_endpoints(request.integration_id)
    tools = tool_factory(request.api_base, all_endpoints)
    params = {}
    body = {}
    response_content = {}

    retrieved_vectors = await identify_endpoints(IdentifyEndpointsRequest(
        api_base=api_base,
        integration_id=request.integration_id,
        query=request.query,
        rephrasal_instructions=request.rephrasal_instructions,
        rephraser=request.rephraser,
        llm_config=request.llm_config
    ), api_key=api_key)
    vector = retrieved_vectors['endpoints'][0]
    if vector['parameters']:
        PARAMETERS_GENERATOR_AGENT = dspy.ReAct(
            ParametersGeneratorSignature, tools=tools, max_iters=5)
        print(vector['parameters'])
        parameters = PARAMETERS_GENERATOR_AGENT(input=ParametersInputModel(
            query=request.query,
            request_parameters_schema=vector['parameters']
        ))
        params = parameters.output.request_parameters

    if vector['body']:
        BODY_GENERATOR_AGENT = dspy.ReAct(
            BodyGeneratorSignature, tools=tools, max_iters=5)
        print(vector['body'])
        body_model_instance = BODY_GENERATOR_AGENT(input=BodyInputModel(
            query=request.query,
            request_body_schema=vector['body']
        ))
        body = body_model_instance.output.request_body

    # Start timing the API call
    api_start_time = time.time()
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

    api_latency = time.time() - api_start_time  # Calculate API latency

    response_content = response.json()
    final_response = FINAL_RESPONSE_GENERATOR_AGENT(input=FinalResponseGeneratorInputModel(
        query=request.query,
        structure_of_data=vector['response'],
        data=response_content
    ))

    natural_language_response = final_response.output.natural_language_response

    total_latency = time.time() - start_time  # Calculate total latency
    kramen_latency = total_latency - api_latency  # Calculate Kramen latency

    return dict(
        natural_language_response=natural_language_response,
        rephrased_query=retrieved_vectors['rephrased_query'],
        request={
            'endpoint': vector,
            'parameters': params,
            'body': body,
            'response': response_content
        },
        api_latency=api_latency,
        kramen_latency=kramen_latency
    )
# 8gPsGafdnLscmLJMirl1M_3r8vGKeg
# client id: 4ULI3pE1B8gBZRxJoPu1GA
# jira token: ATATT3xFfGF0aT_RAUdP8sqaQnphOKtFWdiTzAI5FC2gu1Cux0R_D-sBnhmtF7pZ8Xv5rajtENkC1fJzutm8MP_zSmn50IDs-xuHGZFH8k7GbaVLk10ruE9jS8ezCefXclvg9ZLkpv8WToy0emRtbDT2iqquIRpGKnVKXirMidniJszU_VBNkmo=017BED34


@run_query_router.post("/deep")
async def deep(request: DeepThinkSchema, api_key: str = Header(...)):
    lm = dspy.LM(model=request.llm_config.llm,
                 api_key=request.llm_config.llm_api_key)
    dspy.configure(lm=lm)
    integrations = [
        sqlalchemy_object_to_dict(i)
        for i in session.query(Integration).filter(
            Integration.uuid.in_(request.integrations)
        ).all()
    ]

    decomposed = DECOMPOSER_AGENT(
        input=DecomposerInputModel(query=request.query))
    steps = decomposed.output.steps
    context = ""
    # print(integrations)
    step_responses = []
    for i in range(len(steps)):
        step = steps[i]
        id_agent = INTEGRATION_PICKER(input=IntegrationPickerInputModel(
            query=step,
            integrations=integrations
        ))
        integration_uuid = id_agent.output.uuid
        result = await run_endpoint(
            request=RunQuerySchema(
                rephraser=False,
                rephrasal_instructions="",
                integration_id=integration_uuid,
                api_base=request.api_base.get(integration_uuid),
                request_headers=request.request_headers.get(integration_uuid),
                additional_context=context,
                llm_config=request.llm_config,
                query=step
            ),
            api_key=api_key
        )
        context += "Query:\n" + step + "\nAnswer:\n" + \
            result['natural_language_response']
        step_responses.append({
            'step': step,
            'response': result
        })
    res = TEXT_RESPONSE_GENERATOR(input=TextInputModel(
        query=request.query,
        context=context
    ))

    return {"natural_language_response": res.output.response, "context": context, "steps": step_responses}
