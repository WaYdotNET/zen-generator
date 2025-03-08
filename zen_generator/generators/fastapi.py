from __future__ import annotations

from ast import (
    Assign,
    Attribute,
    Call,
    Constant,
    ImportFrom,
    Load,
    Name,
    Store,
    alias,
    expr,
    stmt,
)
from pathlib import Path
from typing import Sequence

from zen_generator.core.ast_utils import get_component_schemas
from zen_generator.core.io import load_yaml, save_python_file
from zen_generator.generators.common_python import (
    generate_function_ast,
    generate_models_ast,
)


def generate_fastapi_from_asyncapi(
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
    additional_imports: Sequence[stmt] = [
        ImportFrom(module="pydantic", names=[alias(name="BaseModel")], level=0),
    ]
    model = generate_models_ast(
        component_schemas,
        additional_imports=additional_imports,
        include_typing_import=False,
    )
    save_python_file(model, models_file)

    decorator_list: Sequence[expr] = [
        Call(
            func=Attribute(value=Name(id="app", ctx=Load()), attr="get", ctx=Load()),
            args=[Constant(value="/{func_name}")],
            keywords=[],
        )
    ]
    additional_imports_after_models: Sequence[stmt] = [
        Assign(
            targets=[Name(id="app", ctx=Store())],
            value=Call(func=Name(id="FastAPI", ctx=Load()), args=[], keywords=[]),
        )
    ]
    function = generate_function_ast(
        source_content,
        component_schemas,
        app_name,
        models_file.stem,
        is_async,
        decorator_list=decorator_list,
        additional_imports=additional_imports,
        additional_imports_after_models=additional_imports_after_models,
    )
    save_python_file(function, functions_file)
