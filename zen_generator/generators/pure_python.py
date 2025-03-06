from __future__ import annotations

from pathlib import Path

from zen_generator.core.ast_utils import get_component_schemas
from zen_generator.core.io import load_yaml, save_python_file
from zen_generator.generators.common_python import generate_function_ast, generate_models_ast


def generate_pure_python_from_asyncapi(
    source: Path,
    models_file: Path,
    functions_file: Path,
    app_name: str,
    is_async: bool = False,
) -> None:
    """
    Generate the Python files from the AsyncAPI specification
    :param source: The source file
    :param models_file: The models file
    :param functions_file: The functions file
    :param app_name: The name of the application
    :param is_async: Whether the function is async
    :return: None
    """
    source_content = load_yaml(source)
    component_schemas = get_component_schemas(source_content) or {}

    model = generate_models_ast(component_schemas)
    save_python_file(model, models_file)
    function = generate_function_ast(source_content, component_schemas, app_name, models_file.stem, is_async)
    save_python_file(function, functions_file)
