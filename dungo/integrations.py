import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from models import Integration, session
from schemas.raapi_schemas.rag import EditVectorSchema
from utils.upsert import upsert_vector, qdrant_client
from schemas.dungo_schemas.integrations import CreateIntegrationModel, DeleteIntegrationModel
from schemas.dungo_schemas.openapi import UploadOpenapiModel
from schemas.raapi_schemas.upsert import UpsertSchema
from utils.auth import verify_token
from utils.general import sqlalchemy_object_to_dict
from utils.openapi import find_ref_schema, convert_schema_to_fields, process_parameters

integrations_router = APIRouter()


@integrations_router.post("/create")
async def create_integrations(request: CreateIntegrationModel, user=Depends(verify_token)):
    integration = Integration(
        name=request.name,
        uuid=str(uuid.uuid4()),
        owner_id=user['id'],
    )
    session.add(integration)
    session.commit()
    return sqlalchemy_object_to_dict(integration)


@integrations_router.get("/all")
async def all_integrations(user=Depends(verify_token)):
    integrations = session.query(Integration).filter(
        Integration.owner_id == user['id']).all()
    res = []
    for i in integrations:
        res.append(sqlalchemy_object_to_dict(i))

    return res


@integrations_router.post("/delete")
async def delete_integration(request: DeleteIntegrationModel, user=Depends(verify_token)):
    integration = session.query(Integration).filter(
        Integration.id == request.id,
        Integration.owner_id == user['id']
    ).first()

    if integration is None:
        raise HTTPException(status_code=404, detail={
                            "message": "Integration not found"})

    session.delete(integration)
    session.commit()

    return {"message": "Integration deleted successfully"}


@integrations_router.post("/upload-openapi")
async def upload_openapi(
    request: UploadOpenapiModel,
    user=Depends(verify_token)
):
    if type(request.data) == str:
        request.data = json.loads(request.data)
    routes = []
    paths = request.data['paths']
    components = request.data.get('components', {}).get('schemas', {})

    for path, path_content in paths.items():
        for method, request_content in path_content.items():
            route = {
                'method': method.upper(),
                'url': path,
                'description': request_content.get('description', ''),
                'text': request_content.get('description', ''),
                'integration_id': request.integration_id,
                'tool': False
            }
            if str(method.upper() + "_" + path) not in request.selected_endpoints:
                continue

            parameters = request_content.get('parameters', [])
            route['parameters'] = process_parameters(parameters)

            request_body = request_content.get('requestBody', {})
            content = request_body.get(
                'content', {}).get('application/json', {})
            body_schema = content.get('schema', {})

            if body_schema:
                if '$ref' in body_schema:
                    body_schema = find_ref_schema(
                        body_schema['$ref'], components)
                body_fields = convert_schema_to_fields(body_schema, components)
                route['body'] = json.dumps(body_fields)
            else:
                route['body'] = '[]'

            success_response = request_content.get(
                'responses', {}).get('200', {})
            content = success_response.get(
                'content', {}).get('application/json', {})
            response_schema = content.get('schema', {})

            if response_schema:
                if '$ref' in response_schema:
                    response_schema = find_ref_schema(
                        response_schema['$ref'], components)
                response_fields = convert_schema_to_fields(
                    response_schema, components)
                route['response'] = json.dumps(response_fields)
            else:
                route['response'] = '[]'

            routes.append(route)

    for route in routes:
        await upsert_vector(request=UpsertSchema(
            integration_id=route['integration_id'], text=route['text'], metadata=route))

    return routes


@integrations_router.get("/endpoints")
async def endpoints(integration_id=Query(str, description="ID of the integration"), user=Depends(verify_token)):
    try:
        search_results = qdrant_client.scroll(
            collection_name=integration_id,
            limit=100,
            with_payload=True,
            with_vectors=False,
        )
        points = search_results[0]
        return [point.payload for point in points]
    except:
        return []


@integrations_router.post("/edit-endpoint")
async def edit_vector(request: EditVectorSchema, user=Depends(verify_token)):
    existing_collections = qdrant_client.get_collections().collections
    exists = any(collection.name ==
                 request.integration_id for collection in existing_collections)

    if not exists:
        return JSONResponse(content={"message": "the given bot does not exist"}, status_code=404)

    points = qdrant_client.query_points(
        collection_name=request.integration_id, with_payload=True).points

    matching_point = None
    for point in points:
        if point.payload.get("url") == request.new_metadata["url"]:
            matching_point = point
            break

    if not matching_point:
        return JSONResponse(content={"message": "No matching vector found for the given URL"}, status_code=404)

    # Check if the description has changed
    if request.new_metadata.get("description") != matching_point.payload.get("description"):
        # Delete the existing point
        qdrant_client.delete(
            collection_name=request.integration_id,
            points=[matching_point.id]
        )
        # Placeholder comment for creating a new point later
        # TODO: Add logic to create a new point with the updated description
        await upsert_vector(UpsertSchema(
            integration_id=request.integration_id,
            text=request.new_metadata.get("description"),
            metadata=request.new_metadata
        ))

    else:
        # Update the existing point with the new metadata
        qdrant_client.overwrite_payload(
            collection_name=request.integration_id,
            points=[matching_point.id],
            payload=request.new_metadata
        )

    return {"message": "operation successful"}
