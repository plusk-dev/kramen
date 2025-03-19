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


class ParametersInputModel(BaseModel):
    request_parameters_schema: dict | list = Field(
        description="Define the parameters required for the request as a query. Use this schema specifically to extract and structure the request parameters content in the final output."
    )
    query: str = Field(
        description="The input query from which the request parameters and request body will be extracted. Ensure that all relevant details for both are captured accurately."
    )


class ParametersOutputModel(BaseModel):
    request_parameters: dict = Field(
        description="A JSON object containing the request parameters with values derived from the query. If a request parameters schema is provided, ensure this output is never empty. Include only values explicitly mentioned in the query—do not add anything extra. If there is a parameter named 'query', use very specific keywords only as the value for that parameter, never use the entire user query."
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
