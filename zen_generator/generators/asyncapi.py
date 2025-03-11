"""This module contains utilities for generating AsyncAPI documents."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from zen_generator.core.ast_utils import convert_annotations_to_asyncapi_schemas, generate_component_schemas
from zen_generator.core.io import parse_python_file_to_ast, save_yaml_file
from zen_generator.core.parsing import function_content_reader


def create_async_api_content(
    app_name: str,
    models_schema: dict[str, Any],
    functions_docstring: str | None,
    functions_parsed: dict[str, Any],
):
    """Generate the AsyncAPI document from the provided models and functions content.

    The function takes in the application name, the models schema, the functions docstring
    and the functions parsed content and generates the AsyncAPI document.

    :param app_name: The name of the application
    :param models_schema: The models schema
    :param functions_docstring: The functions docstring
    :param functions_parsed: The functions parsed content
    :return: The generated AsyncAPI document
    """
    channels = {}
    operations = {}
    components = {
        "channels": {},
        "operations": {},
        "messages": {},
        "schemas": models_schema,
    }
    for func, content in functions_parsed.items():
        # channels
        channels[func] = {"$ref": f"#/components/channels/{func}"}

        # operations
        operations[func] = {"$ref": f"#/components/operations/{func}"}

        # components.channels
        components["channels"][func] = {
            "messages": {
                "request": {"$ref": f"#/components/messages/{func}_request"},
                "response": {"$ref": f"#/components/messages/{func}_response"},
            }
        }

        # components.operations
        components["operations"][func] = {
            "action": "receive",
            "description": content.get("description", ""),
            "channel": {"$ref": f"#/channels/{func}"},
            "messages": [{"$ref": f"#/channels/{func}/messages/request"}],
            "reply": {
                "channel": {"$ref": f"#/channels/{func}"},
                "messages": [{"$ref": f"#/channels/{func}/messages/response"}],
            },
        }

        # components.messages
        components["messages"][f"{func}_request"] = content.get("request")
        components["messages"][f"{func}_response"] = content.get("response")

    async_api_content: dict[str, Any] = {
        "asyncapi": "3.0.0",
        "info": {
            "title": app_name,
            "version": "0.0.1",
            "description": functions_docstring,
        },
        "channels": channels,
        "operations": operations,
        "components": components,
    }
    return async_api_content


def generate_asyncapi_schema(model_name: str, attributes: dict[str, Any]) -> dict[str, Any]:
    """Generate an AsyncAPI schema for a given model.

    The function takes in a model name and a dictionary of attributes
    and returns a dictionary containing the AsyncAPI schema.

    :param model_name: The name of the model
    :param attributes: The model attributes
    :return: The generated AsyncAPI schema
    """
    properties = {}
    required = []

    for attr_name, attr_info in attributes.items():
        python_type = attr_info.get("type")
        asyncapi_type = convert_annotations_to_asyncapi_schemas(python_type)

        if not asyncapi_type:
            continue

        property_schema = {"type": asyncapi_type}

        if "description" in attr_info:
            property_schema["description"] = attr_info["description"]

        if attr_info.get("required", False):
            required.append(attr_name)

        properties[attr_name] = property_schema

    schema = {"type": "object", "properties": properties}

    if required:
        schema["required"] = required

    return {model_name: schema}


def generate_asyncapi_document(
    title: str,
    version: str,
    models: dict[str, dict[str, Any]],
    servers: Optional[dict[str, dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Generate an AsyncAPI document from the provided model and function definitions.

    Args:
        title (str): The title of the AsyncAPI document
        version (str): The version of the AsyncAPI document
        models (dict[str, dict[str, Any]]): The models as a dictionary of dictionaries
        servers (dict[str, dict[str, Any]], optional): The servers as a dictionary of dictionaries

    Returns:
        dict[str, Any]: The generated AsyncAPI document
    """
    components: dict[str, dict[str, Any]] = {"schemas": {}}
    for model_name, attributes in models.items():
        components["schemas"].update(generate_asyncapi_schema(model_name, attributes))

    asyncapi_doc = {
        "asyncapi": "2.5.0",
        "info": {"title": title, "version": version},
        "components": components,
    }

    if servers:
        asyncapi_doc["servers"] = servers

    return asyncapi_doc


def generate_asyncapi_from_files(models_file: Path, functions_file: Path, output_path: Path, app_name: str) -> None:
    """Generate an AsyncAPI document from the provided model and function definitions.

    Args:
        models_file (Path): The path to the file containing the model definitions.
        functions_file (Path): The path to the file containing the function definitions.
        output_path (Path): The path where the generated AsyncAPI document will be saved.
        app_name (str): The name of the application.

    Returns:
        None
    """
    models_ast = parse_python_file_to_ast(models_file)
    models_schema = generate_component_schemas(models_ast)

    functions_ast = parse_python_file_to_ast(functions_file)
    functions_docstring, functions_parsed = function_content_reader(functions_ast)

    async_api_content = create_async_api_content(app_name, models_schema, functions_docstring, functions_parsed)

    save_yaml_file(async_api_content, output_path, app_name)
