from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from zen_generator.core.ast_utils import (
    components_schemas,
    convert_annotations_to_asyncapi_schemas,
)
from zen_generator.core.io import parse_python_file_to_ast, save_yaml_file
from zen_generator.core.parsing import function_content_reader


def create_async_api_content(
    app_name: str,
    interface_schema: dict[str, Any],
    proxy_docstring: str | None,
    proxy_parsed: dict[str, Any],
):
    """
    Create an AsyncAPI document from the provided interface schema and parsed proxy content.
    :param app_name: The name of the application
    :param interface_schema: The schema of the interface
    :param proxy_docstring: The docstring of the proxy
    :param proxy_parsed: The parsed proxy content
    :return: The generated AsyncAPI document
    """
    channels = {}
    operations = {}
    components = {
        "channels": {},
        "operations": {},
        "messages": {},
        "schemas": interface_schema,
    }
    for func, content in proxy_parsed.items():
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
            "description": proxy_docstring,
        },
        "channels": channels,
        "operations": operations,
        "components": components,
    }
    return async_api_content


def generate_asyncapi_schema(model_name: str, attributes: dict[str, Any]) -> dict[str, Any]:
    """
    Generate an AsyncAPI schema for the specified model.
    :param model_name: The name of the model
    :param attributes: The attributes of the model
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
    """
    Generate an AsyncAPI document from the provided models and metadata.

    This function creates a well-formed AsyncAPI document with the specified title, version,
    and model schemas.

    :param title: The title of the AsyncAPI document
    :param version: The version of the API
    :param models: A dictionary mapping model names to their attributes
    :param servers: Optional dictionary of server configurations to include in the document
    :return: A dictionary representing the complete AsyncAPI document
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
    """
    Generate an AsyncAPI document from the provided model and function files.
    :param models_file: The path to the file containing data models definitions
    :param functions_file: The path to the file containing function definitions
    :param output_path: The path where to save the generated AsyncAPI document
    :param app_name: The name of the application to be included in the document
    :return: None
    """
    models_ast = parse_python_file_to_ast(models_file)
    models_schema = components_schemas(models_ast)

    functions_ast = parse_python_file_to_ast(functions_file)
    functions_docstring, functions_parsed = function_content_reader(functions_ast)

    async_api_content = create_async_api_content(app_name, models_schema, functions_docstring, functions_parsed)

    save_yaml_file(async_api_content, output_path, app_name)
