import json
import uuid
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from models import Integration, session
from schemas.raapi_schemas.rag import EditVectorSchema
from utils.upsert import upsert_vector, qdrant_client
from schemas.dungo_schemas.integrations import CreateIntegrationModel, DeleteIntegrationEndpointModel, DeleteIntegrationModel, UpdateIntegrationDescriptionModel

from schemas.raapi_schemas.upsert import UpsertSchema
from utils.general import sqlalchemy_object_to_dict
from utils.openapi import find_ref_schema, convert_schema_to_fields, process_parameters

integrations_router = APIRouter()


@integrations_router.post("/create")
async def create_integrations(request: CreateIntegrationModel):
    integration = Integration(
        name=request.name,
        description=request.description,
        uuid=str(uuid.uuid4()),
        icon=request.icon,
        auth_structure=request.auth_structure,
    )
    session.add(integration)
    session.commit()
    return sqlalchemy_object_to_dict(integration)


@integrations_router.get("/all")
async def all_integrations():
    integrations = session.query(Integration).all()
    res = []
    for i in integrations:
        res.append(sqlalchemy_object_to_dict(i))

    return res


@integrations_router.post("/delete")
async def delete_integration(request: DeleteIntegrationModel):
    integration = session.query(Integration).filter(
        Integration.id == request.id
    ).first()
    
    if integration is None:
        raise HTTPException(status_code=404, detail={
                            "message": "Integration not found"})
    
    qdrant_client.delete_collection(collection_name=integration.uuid)
    session.delete(integration)
    session.commit()

    return {"message": "Integration deleted successfully"}


@integrations_router.post("/upload-openapi")
async def upload_openapi(
    integration_id: str = Form(...),
    selected_endpoints: str = Form(...),
    file: UploadFile = File(...)
):
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are allowed")
    
    # Parse selected endpoints
    try:
        selected_endpoints_list = json.loads(selected_endpoints)
        if not isinstance(selected_endpoints_list, list):
            raise ValueError("selected_endpoints must be a list")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid selected_endpoints format: {str(e)}")
    
    # Read and parse the JSON file
    try:
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    routes = []
    paths = data['paths']
    components = data.get('components', {}).get('schemas', {})
    
    print(f"Processing {len(paths)} paths")
    print(f"Found {len(components)} component schemas")

    for path, path_content in paths.items():
        for method, request_content in path_content.items():
            route = {
                'method': method.upper(),
                'url': path,
                'description': request_content.get('description', ''),
                'text': request_content.get('description', ''),
                'integration_id': integration_id,
                'tool': False
            }
            
            # Check if this endpoint is in the selected endpoints
            # If selected_endpoints_list is empty, select all endpoints
            if selected_endpoints_list and str(method.upper() + "_" + path) not in selected_endpoints_list:
                continue

            print(f"\nProcessing endpoint: {method.upper()} {path}")
            print(f"Has requestBody: {'requestBody' in request_content}")
            if 'requestBody' in request_content:
                print(f"requestBody content types: {list(request_content['requestBody'].get('content', {}).keys())}")

            parameters = request_content.get('parameters', [])
            route['parameters'] = process_parameters(parameters)

            request_body = request_content.get('requestBody', {})
            
            # Handle multiple content types for request body
            body_schema = {}
            content_types = request_body.get('content', {})
            
            # Try different content types in order of preference
            for content_type in ['application/json', 'application/x-www-form-urlencoded', 'multipart/form-data']:
                if content_type in content_types:
                    body_schema = content_types[content_type].get('schema', {})
                    break
            
            # If no specific content type found, try to get any schema from content
            if not body_schema and content_types:
                for content_type, content_data in content_types.items():
                    if 'schema' in content_data:
                        body_schema = content_data['schema']
                        break

            if body_schema:
                if '$ref' in body_schema:
                    body_schema = find_ref_schema(
                        body_schema['$ref'], components)
                body_fields = convert_schema_to_fields(body_schema, components)
                route['body'] = json.dumps(body_fields)
                print(f"Body fields for {method.upper()} {path}: {body_fields}")
            else:
                route['body'] = '[]'
                print(f"No body schema found for {method.upper()} {path}")

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
async def endpoints(integration_id=Query(str, description="ID of the integration")):
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


@integrations_router.post("/delete-endpoint")
async def delete_endpoint(request: DeleteIntegrationEndpointModel):
    search_results = qdrant_client.scroll(
        collection_name=request.integration_id,
        limit=100,
        with_payload=True,
        with_vectors=False,
    )
    points = search_results[0]
    matching_point = None
    for point in points:
        print(point.payload.get("url"))
        if point.payload.get("url") == request.new_metadata["url"]:
            matching_point = point
            break
    qdrant_client.delete(
        collection_name=request.integration_id,
        points_selector=[matching_point.id],
    )
    if not matching_point:
        return JSONResponse(content={"message": "No matching vector found for the given URL"}, status_code=404)
    return {
        "message": "endpoint deleted"
    }


@integrations_router.post("/edit-endpoint")
async def edit_vector(request: EditVectorSchema):
    existing_collections = qdrant_client.get_collections().collections
    exists = any(collection.name ==
                 request.integration_id for collection in existing_collections)

    if not exists:
        return JSONResponse(content={"message": "the given bot does not exist"}, status_code=404)

    search_results = qdrant_client.scroll(
        collection_name=request.integration_id,
        limit=100,
        with_payload=True,
        with_vectors=False,
    )
    points = search_results[0]
    matching_point = None
    for point in points:
        print(point.payload.get("url"))
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
            points_selector=[matching_point.id],
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


@integrations_router.post("/update-integration-description")
async def update_integration_description(request: UpdateIntegrationDescriptionModel):
    integration = session.query(Integration).filter(
        Integration.id == request.id
    ).first()
    
    if integration is None:
        raise HTTPException(status_code=404, detail={
                            "message": "Integration not found"})
    
    integration.description = request.description
    session.commit()

    return sqlalchemy_object_to_dict(integration)
