"""This module contains utilities for working with files.

The functions in this module provide a higher-level interface than the `ast` module,
and are used to generate Python code from AsyncAPI specifications.

"""
from __future__ import annotations

import json
from ast import Module, fix_missing_locations, parse, unparse
from pathlib import Path
from typing import Any, Dict, Literal

import yaml

from zen_generator.core.exception import InvalidFile
from zen_generator.core.formatting import format_python_code


def parse_python_file_to_ast(source: Path) -> Module | None:
    """Parse a Python file to its AST.

    Args:
        source: The path of the file to parse.

    Returns:
        The parsed AST or None if the file is a directory or doesn't exist.
    """
    if source.is_file():
        source_text = source.read_text()
        return parse(source_text)
    elif source.is_dir():
        raise InvalidFile("The source is a directory")
    elif not source.exists():
        raise InvalidFile("The source doesn't exist")
    return None


def load_yaml(source: Path) -> dict[str, Any] | None:
    """Load a YAML file as a dictionary.

    Args:
        source: The path of the file to load.

    Returns:
        The loaded YAML file as a dictionary or None if the file is a directory or
        doesn't exist.
    """
    if source.is_file():
        with open(source, "r") as file:
            return yaml.safe_load(file)
    elif source.is_dir():
        raise InvalidFile("The source is a directory")
    elif not source.exists():
        raise InvalidFile("The source doesn't exist")
    return None


def write_asyncapi_schema(
    schema: Dict[str, Any],
    output_path: Path,
    format_type: Literal["yaml", "json"] = "yaml",
) -> None:
    """Write an AsyncAPI schema to a file.

    Write the provided AsyncAPI schema to the specified output path in the
    specified format.

    Args:
        schema: The AsyncAPI schema to write.
        output_path: The path of the file to write.
        format_type: The format of the output file. Should be either "yaml" or
            "json". Defaults to "yaml".
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format_type == "yaml":
        content = yaml.dump(schema, default_flow_style=False)
        file_path = output_path.with_suffix(".yaml")
    else:
        content = json.dumps(schema, indent=2)
        file_path = output_path.with_suffix(".json")

    file_path.write_text(content)
    print(f"Schema AsyncAPI generato: {file_path}")


def save_yaml_file(async_api_content: dict[str, Any] | None, destination: Path, app_name: str) -> None:
    """Save the AsyncAPI content to a file.

    Save the provided AsyncAPI content to the specified destination file or
    directory. If the destination is a directory, the file name will be the
    application name with a .yml extension.

    Args:
        async_api_content: The AsyncAPI content to write.
        destination: The path of the file to write.
        app_name: The name of the application.
    """
    async_api_content = async_api_content or {}
    if destination.is_dir():
        destination = destination / Path(f"{app_name}.yml")

    dumped = yaml.dump(async_api_content, default_flow_style=False, sort_keys=False)
    with open(destination, mode="w") as f:
        f.write(dumped)


def save_python_file(function_body: list[Any], destination: Path) -> None:
    """Save the Python code to a file.

    Save the provided Python code to the specified destination file. The code
    will be formatted according to the PEP 8 style guide.

    Args:
        function_body: The Python code to write.
        destination: The path of the file to write.
    """
    python_module = Module(body=function_body, type_ignores=[])
    python_file_content = unparse(fix_missing_locations(python_module))
    python_file_content = format_python_code(python_file_content)
    with open(destination, mode="w") as f:
        f.write(python_file_content)
