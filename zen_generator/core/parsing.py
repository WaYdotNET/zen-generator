"""This module contains utilities for parsing Python code.

The functions in this module provide a higher-level interface than the `ast` module,
and are used to generate Python code from AsyncAPI specifications.

"""

from __future__ import annotations

import re
from ast import AsyncFunctionDef, FunctionDef, Module, get_docstring, walk
from typing import Any

from zen_generator.core.ast_utils import convert_annotations_to_asyncapi_schemas, parse_type_annotation

# Define regular expressions for Args and Returns sections
ARGS_PATTERN = re.compile(r"Args:(.*?)(?:Returns|$)", re.DOTALL)
RETURNS_PATTERN = re.compile(r"Returns:(.*?)$", re.DOTALL)
ARGS_DESCRIPTION_PATTERN = r"\s*([\w_]+)\s*\(\)\s*:\s*([^(\n)]+)"


def function_to_asyncapi_schemas(
    function_node: FunctionDef | AsyncFunctionDef,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Convert a function definition to AsyncAPI request and response schemas.

    Args:
        function_node: The function definition node

    Returns:
        A tuple containing the request and response schemas for the function
    """
    name = function_node.name
    docstring = get_docstring(function_node) or ""

    args_match = ARGS_PATTERN.search(docstring)
    returns_match = RETURNS_PATTERN.search(docstring)

    parameters_description = {}
    if args_match:
        args_section = args_match.group(1).strip()
        parameters_description = dict(re.findall(ARGS_DESCRIPTION_PATTERN, args_section))

    request_schema = _create_request_schema(function_node, name, docstring, parameters_description)
    response_schema = _create_response_schema(function_node, name, docstring, returns_match)

    return request_schema, response_schema


def _create_request_schema(
    function_node: FunctionDef | AsyncFunctionDef,
    name: str,
    docstring: str,
    parameters_description: dict,
) -> dict[str, Any]:
    """Convert a function definition to AsyncAPI request schema.

    Args:
        function_node: The function definition node
        name: The name of the function
        docstring: The docstring of the function
        parameters_description: A dictionary of parameter descriptions

    Returns:
        A dictionary representing the request schema
    """
    request_payload: dict[str, Any] = {
        "type": "object",
        "required": [],
        "properties": {},
    }

    request_schema = {
        "title": f"Request params for {name}",
        "summary": "",
        "description": docstring,
        "payload": request_payload,
    }

    for param in function_node.args.args:
        property_name = param.arg
        items = parse_type_annotation(param.annotation)
        conv = convert_annotations_to_asyncapi_schemas(items)
        description = parameters_description.get(param.arg, "")

        if conv.get("required"):
            request_payload["required"].append(property_name)
            del conv["required"]

        request_payload["properties"][property_name] = conv.get("properties")
        request_payload["properties"][property_name]["description"] = description

    return request_schema


def _create_response_schema(
    function_node: FunctionDef | AsyncFunctionDef,
    name: str,
    docstring: str,
    returns_match: re.Match | None,
) -> dict[str, Any]:
    """Convert a function definition to AsyncAPI response schema.

    Args:
        function_node: The function definition node
        name: The name of the function
        docstring: The docstring of the function
        returns_match: A regular expression match object for the "Returns" section

    Returns:
        A dictionary representing the response schema
    """
    response_description = ""
    if returns_match:
        response_description = returns_match.group(1).strip()
    elif "Returns:" in docstring:
        start_returns = docstring.find("Returns:") + len("Returns:")
        response_description = docstring[start_returns:].strip()

    response_schema = {
        "title": f"Response params for {name}",
        "summary": "",
        "description": response_description,
    }

    return_type = parse_type_annotation(function_node.returns)
    properties = convert_annotations_to_asyncapi_schemas(return_type)
    response_payload = properties.get("properties", {})
    response_schema["payload"] = response_payload

    if properties.get("required") and isinstance(response_payload, dict):
        response_payload["format"] = "required"

    return response_schema


def function_content_reader(tree: Module | None) -> tuple[str | None, dict[str, Any]]:
    """Read function content from a tree of nodes.

    Args:
        tree: The root node of the tree

    Returns:
        A tuple containing the docstring of the tree and a dictionary of functions
        where the keys are the names of the functions and the values are dictionaries
        containing the request and response schemas
    """
    functions_docstring = get_docstring(tree) if tree else ""
    functions_to_async: dict[str, Any] = {}

    if tree is not None:
        for node in walk(tree):
            if isinstance(node, (FunctionDef, AsyncFunctionDef)):
                request, response = function_to_asyncapi_schemas(node)
                functions_to_async.update({f"{node.name}": {"request": request, "response": response}})

    return functions_docstring, functions_to_async
