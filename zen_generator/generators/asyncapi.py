"""This module contains utilities for generating AsyncAPI documents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from zen_generator.core.ast_utils import convert_annotations_to_asyncapi_schemas, generate_component_schemas
from zen_generator.core.io import parse_python_file_to_ast, save_yaml_file
from zen_generator.core.parsing import function_content_reader


def create_async_api_content(
    app_name: str,
    models_schema: dict[str, Any],
    api_description: str | None,
    functions_parsed: dict[str, Any],
):
    """Generate the AsyncAPI document from the provided models and functions content.

    The function takes in the application name, the models schema, the functions docstring
    and the functions parsed content and generates the AsyncAPI document.

    :param app_name: The name of the application
    :param models_schema: The models schema
    :param api_description: The api docstring
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
            "description": content.get("request", {}).get("description", ""),
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
            "description": api_description or "",
        },
        "channels": channels,
        "operations": operations,
        "components": components,
    }
    return async_api_content


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
    api_description, functions_parsed = function_content_reader(functions_ast)

    async_api_content = create_async_api_content(app_name, models_schema, api_description, functions_parsed)

    save_yaml_file(async_api_content, output_path, app_name)
