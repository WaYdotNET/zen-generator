from __future__ import annotations

ASYNCAPI_TO_PYTHON_TYPES: dict[str, str] = {
    "string": "str",
    "integer": "int",
    "boolean": "bool",
    "array": "list",
    "object": "object",
}


def convert_asyncapi_to_python(asyncapi_type: str) -> str:
    """
    Convert an AsyncAPI type to the corresponding Python type.
    :param asyncapi_type: The AsyncAPI type
    :return: The corresponding Python type
    """
    return ASYNCAPI_TO_PYTHON_TYPES.get(asyncapi_type, asyncapi_type)


def convert_python_to_asyncapi(python_type: str) -> str | None:
    """
    Convert a Python type to the corresponding AsyncAPI type.
    :param python_type: The Python type
    :return: The corresponding AsyncAPI type
    """
    reverse_mapping = {py: asyncapi for asyncapi, py in ASYNCAPI_TO_PYTHON_TYPES.items()}
    return reverse_mapping.get(python_type)
