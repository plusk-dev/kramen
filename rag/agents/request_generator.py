from typing import List, Optional, Union
import typing
import dspy
from pydantic import BaseModel, Field, Json
from typing import List, Type, Optional
from pydantic import BaseModel, Field
from typing import Optional


def create_pydantic_model_from_json(parameters, model_name):
    type_mapping = {
        'integer': int,
        'number': float,
        'boolean': bool,
        'string': str,
        'object': dict,
        'array': list,
        'null': type(None)
    }

    model_cache = {}

    def parse_schema(schema):
        if not schema:
            return str

        if 'anyOf' in schema:
            types = []
            for type_def in schema['anyOf']:
                if type_def.get('type') == 'null':
                    continue
                base_type = type_mapping[type_def['type']]
                types.append(base_type)

            if len(types) == 1:
                return Optional[types[0]]
            return Optional[Union[tuple(types)]]

        if isinstance(schema, str):
            return type_mapping.get(schema, str)

        return type_mapping.get(schema.get('type'), str)

    def create_nested_model(params, nested_model_name):
        if nested_model_name in model_cache:
            return model_cache[nested_model_name]

        annotations = {}
        field_definitions = {}

        for param in params:
            param_name = param.get('name') or param.get('key')
            schema = param.get('schema') or param

            if schema.get('type') == 'object':
                properties = schema.get('properties', [])
                if not properties and 'fields' in schema:
                    properties = schema['fields']
                nested_type = create_nested_model(
                    properties,
                    f"{nested_model_name}_{param_name}"
                )
                python_type = nested_type
            else:
                python_type = parse_schema(schema)

            field_definitions[param_name] = Field(
                default=None,
                description=param.get(
                    'description', '') + "Generate a value for this particular parameter using the user query."
            )

            is_required = param.get('required', True)
            annotations[param_name] = Optional[python_type] if not is_required else python_type

        namespace = {
            '__annotations__': annotations,
            **field_definitions
        }

        model = type(nested_model_name, (BaseModel,), namespace)
        model_cache[nested_model_name] = model
        return model

    return create_nested_model(parameters, model_name)


class DataExtractorInputModel(BaseModel):
    query: str = Field(
        description=(
            "The user query from which data will be extracted. This contains the raw user input that needs to be parsed and structured according to the schema. "
            "Note: The query may include date/time information in brackets at the beginning (e.g., '[Current date and time: 2024-01-15 14:30:00 UTC]'). "
            "Use this temporal context if relevant to the query (e.g., for time-based operations, recent data, etc.), otherwise ignore it."
        )
    )
    schema: dict | list = Field(
        description="The schema definition that specifies the EXACT structure and fields required for the output. The extracted data must STRICTLY conform to this schema with NO additional fields allowed. Only fields explicitly defined in this schema should appear in the output."
    )
    schema_type: str = Field(
        description="The type of schema being processed. Should be either 'parameters' for request parameters or 'body' for request body schema.",
        default="parameters"
    )


class DataExtractorOutputModel(BaseModel):
    extracted_data: dict | list = Field(
        description="The structured data extracted from the query that STRICTLY conforms to the provided schema. CRITICAL REQUIREMENTS: 1) ONLY include fields that are explicitly defined in the schema - NO EXTRA FIELDS ALLOWED. 2) Every required field in the schema must be populated. 3) Optional fields should only be included if they can be determined from the query. 4) Do NOT add any fields that are not in the schema definition. 5) Do NOT modify field names from the schema. 6) The output structure must match the schema exactly. VIOLATION OF THESE RULES IS STRICTLY FORBIDDEN."
    )


class DataExtractorSignature(dspy.Signature):
    """
    Extract structured data from a user query based on a provided schema with ZERO TOLERANCE for extra fields.
    
    CRITICAL RULES - NEVER VIOLATE THESE:
    1. ONLY extract fields that are explicitly defined in the provided schema
    2. NEVER add fields that are not in the schema - this is STRICTLY FORBIDDEN
    3. NEVER modify field names from the schema definition
    4. NEVER add nested objects or arrays unless explicitly defined in the schema
    5. NEVER include metadata, timestamps, or any other fields not in the schema
    
    This agent specializes in:
    1. Parsing user queries to identify ONLY relevant information that maps to schema fields
    2. Mapping query content EXCLUSIVELY to the exact schema fields provided
    3. Ensuring ABSOLUTE compliance with the provided schema structure
    4. Generating appropriate values ONLY for fields defined in the schema
    5. Handling optional fields by including them ONLY if they exist in the schema AND can be determined from the query
    6. Following platform-specific guidelines from integration manuals when available
    
    The agent MUST:
    - Extract ALL required fields from the query (as defined in the schema)
    - Respect field types defined in the schema EXACTLY
    - NEVER add any fields not present in the schema
    - Use appropriate defaults for missing optional fields (as defined in the schema)
    - Maintain data integrity and type consistency within the schema constraints
    - REJECT any temptation to add "helpful" extra fields
    - Follow platform-specific workflows and best practices outlined in integration manuals
    - Consider platform-specific requirements when extracting data (e.g., getting user IDs first for user-related queries)
    
    FAILURE TO FOLLOW THESE RULES WILL RESULT IN SYSTEM FAILURE.
    """
    input: DataExtractorInputModel = dspy.InputField(
        desc="Input containing the user query, schema definition, and schema type. The query provides the raw source data, while the schema defines the EXACT target structure for extraction with NO DEVIATION ALLOWED."
    )
    output: DataExtractorOutputModel = dspy.OutputField(
        desc="Output containing the extracted data that EXACTLY conforms to the provided schema with NO EXTRA FIELDS. Only fields defined in the schema are allowed in the output."
    )


# Legacy classes for backward compatibility (deprecated)
class ParametersInputModel(BaseModel):
    request_parameters_schema: dict | list = Field(
        description="Define the parameters required for the request as a query. Use this schema specifically to extract and structure the request parameters content in the final output."
    )
    query: str = Field(
        description="The input query from which the request parameters and request body will be extracted. Ensure that all relevant details for both are captured accurately."
    )


class ParametersOutputModel(BaseModel):
    request_parameters: dict = Field(
        description="A JSON object containing the request body with values derived from the query. If a request body schema is provided, this output must never be empty. Include only values explicitly mentioned in the query—do not add anything extra."
    )


class BodyInputModel(BaseModel):
    request_body_schema: dict | list = Field(
        description="Provide the schema for the request body. This will be used to extract and structure only the request body content in the final output."
    )
    query: str = Field(
        description="The input query from which the request parameters and request body will be extracted. Ensure that all relevant details for both are captured accurately."
    )


class BodyOutputModel(BaseModel):
    request_body: dict | list = Field(
        description="A JSON object containing the request body with values derived from the query. If a request body schema is provided, this output must never be empty. Include only values explicitly mentioned in the query—do not add anything extra."
    )


class ParametersGeneratorSignature(dspy.Signature):
    input: ParametersInputModel = dspy.InputField()
    output: ParametersOutputModel = dspy.OutputField()


class BodyGeneratorSignature(dspy.Signature):
    input: BodyInputModel = dspy.InputField()
    output: BodyOutputModel = dspy.OutputField()


# # Parse the schema
# schema = json.loads("""
# [
#     {"key":"id","type":"integer","description":"The unique identifier for the category.","required":true},
#     {"key":"parent_id","type":"object","description":"The unique identifier of the parent category, if applicable.","required":false},
#     {"key":"name","type":"string","description":"The name of the category.","required":true},
#     {"key":"icon","type":"string","description":"The URL of the icon representing the category.","required":true},
#     {"key":"custom_metadata","type":"object","description":"A dictionary containing additional metadata for the category.","required":true},
#     {"key":"last_modified","type":"string","description":"The timestamp indicating the last modification of the category.","required":true},
#     {"key":"poster","type":"object","description":"The URL of the poster image associated with the category, if any.","required":false},
#     {"key":"addable","type":"boolean","description":"Indicates whether the category is addable by users.","required":true},
#     {"key":"trending","type":"boolean","description":"Indicates whether the category is currently trending.","required":true},
#     {"key":"ics","type":"object","description":"The link to the ICS calendar file for the category","required":false},
#     {"key":"uuid","type":"string","description":"The universally unique identifier for the category.","required":true}
# ]
# """)

# # Generate the model
# CategoryModel = create_pydantic_model_from_json(schema, model_name="CategoryModel")
# print(CategoryModel.schema_json(indent=2))

# # Uncomment the following to test DSPy agent generation
# # agent = generate_custom_agent(output_model=CategoryModel, tools=[])
# # response = agent(input=InputModel(query="search for categories"))
# # print(response)
