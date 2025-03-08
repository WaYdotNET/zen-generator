from __future__ import annotations

import json
from ast import Module, fix_missing_locations, parse, unparse
from pathlib import Path
from typing import Any, Dict, Literal

import yaml

from zen_generator.core.exception import InvalidFile
from zen_generator.core.formatting import format_python_code


def parse_python_file_to_ast(source: Path) -> Module | None:
    """
    Parse a python file to an AST
    :param source: Path to the python file
    :return: AST or None
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
    """Scrive uno schema AsyncAPI su file."""
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
    async_api_content = async_api_content or {}
    if destination.is_dir():
        destination = destination / Path(f"{app_name}.yml")

    dumped = yaml.dump(async_api_content, default_flow_style=False, sort_keys=False)
    with open(destination, mode="w") as f:
        f.write(dumped)


def save_python_file(function_body: list[Any], destination: Path) -> None:
    python_module = Module(body=function_body, type_ignores=[])
    python_file_content = unparse(fix_missing_locations(python_module))
    python_file_content = format_python_code(python_file_content)
    with open(destination, mode="w") as f:
        f.write(python_file_content)
