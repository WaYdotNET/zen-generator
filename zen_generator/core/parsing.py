from __future__ import annotations

from ast import (
    AsyncFunctionDef,
    Constant,
    Expr,
    FunctionDef,
    get_docstring,
    Module,
    walk,
)
import re
from typing import Any

from zen_generator.core.ast_utils import (
    convert_annotations_to_asyncapi_schemas,
    convert_ast_annotation_to_dict,
)

# Define regular expressions for Args and Returns sections
ARGS_PATTERN = re.compile(r"Args:(.*?)(?:Returns|$)", re.DOTALL)
RETURNS_PATTERN = re.compile(r"Returns:(.*?)$", re.DOTALL)
ARGS_DESCRIPTION_PATTERN = r"\s*([\w_]+)\s*\(\)\s*:\s*([^(\n)]+)"


def function_to_asyncapi_schemas(
    function_node: FunctionDef | AsyncFunctionDef,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Parse a function node to a tuple with the request and response schemas
    :param function_node: Function node
    :return: Tuple with the request and response schemas
    """
    name = function_node.name
    docstring = _extract_docstring(function_node)

    args_match = ARGS_PATTERN.search(docstring)
    returns_match = RETURNS_PATTERN.search(docstring)

    parameters_description = {}
    if args_match:
        args_section = args_match.group(1).strip()
        parameters_description = dict(re.findall(ARGS_DESCRIPTION_PATTERN, args_section))

    request_schema = _create_request_schema(function_node, name, docstring, parameters_description)
    response_schema = _create_response_schema(function_node, name, docstring, returns_match)

    return request_schema, response_schema


def _extract_docstring(function_node: FunctionDef | AsyncFunctionDef) -> str:
    """
    Extract the docstring from the function node
    :param function_node: Function node
    :return: Docstring
    """
    for stmt in function_node.body:
        if isinstance(stmt, Expr) and isinstance(stmt.value, Constant):
            return stmt.value.s
    return ""


def _create_request_schema(
    function_node: FunctionDef | AsyncFunctionDef,
    name: str,
    docstring: str,
    parameters_description: dict,
) -> dict[str, Any]:
    """
    Create the request schema based on the function parameters
    :param function_node: Function node
    :param name: Function name
    :param docstring: Function docstring
    :param parameters_description: Parameters description
    :return: Request schema
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
        items = convert_ast_annotation_to_dict(param.annotation)
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
    """
    Create the response schema based on the function return type
    :param function_node: Function node
    :param name: Function name
    :param docstring: Function docstring
    :param returns_match: Returns match
    :return: Response schema
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

    return_type = convert_ast_annotation_to_dict(function_node.returns)
    properties = convert_annotations_to_asyncapi_schemas(return_type)
    response_payload = properties.get("properties", {})
    response_schema["payload"] = response_payload

    if properties.get("required") and isinstance(response_payload, dict):
        response_payload["format"] = "required"

    return response_schema


def function_content_reader(tree: Module | None) -> tuple[str | None, dict[str, Any]]:
    """
    Parse a proxy module to a dictionary
    :param tree: Python AST
    :return: Tuple with the docstring and the proxy dictionary
    """
    proxy_docstring = get_docstring(tree) if tree else ""
    proxy_to_async: dict[str, Any] = {}

    if tree is not None:
        for node in walk(tree):
            if isinstance(node, (FunctionDef, AsyncFunctionDef)):
                request, response = function_to_asyncapi_schemas(node)
                proxy_to_async.update({f"{node.name}": {"request": request, "response": response}})

    return proxy_docstring, proxy_to_async
