from __future__ import annotations

from pathlib import Path

from zen_generator.core.ast_utils import generate_component_schemas
from zen_generator.core.io import parse_python_file_to_ast
from zen_generator.core.parsing import function_content_reader
from zen_generator.generators.asyncapi import create_async_api_content


def test_generate_yaml_from_functions_and_models() -> None:
    source_models: Path = Path("./models.py")
    source_functions: Path = Path("./functions.py")
    app_name: str = "Fake"

    models_ast = parse_python_file_to_ast(source_models)
    models_schema = generate_component_schemas(models_ast)

    functions_ast = parse_python_file_to_ast(source_functions)
    functions_docstring, functions_parsed = function_content_reader(functions_ast)

    async_api_content = create_async_api_content(app_name, models_schema, functions_docstring, functions_parsed)
    assert async_api_content
