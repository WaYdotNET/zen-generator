from ast import Assign, ClassDef, Constant, Expr, FunctionDef, ImportFrom
from typing import Any
import pytest
from pathlib import Path
from zen_generator.core.ast_utils import generate_code_from_ast
from zen_generator.generators.common_python import BasePythonGenerator


@pytest.fixture
def asyncapi_file(tmp_path) -> Any:
    file = tmp_path / "asyncapi.yaml"
    file.write_text("""
    asyncapi: '2.0.0'
    info:
      title: Test API
      version: '1.0.0'
      description: Test API description
    components:
      schemas:
        TestModel:
          type: object
          properties:
            name:
              type: string
            age:
              type: integer
    """)
    return file


@pytest.fixture
def generator() -> BasePythonGenerator:
    return BasePythonGenerator()


def test_generate_files_from_asyncapi(generator, asyncapi_file, tmp_path):
    models_file = tmp_path / "models.py"
    functions_file = tmp_path / "functions.py"
    generator.generate_files_from_asyncapi(asyncapi_file, models_file, functions_file, "TestApp")

    assert models_file.exists()
    assert functions_file.exists()


def test_add_logger_setup(generator):
    generator._add_logger_setup("TestApp")
    assert any(isinstance(node, Assign) and node.targets[0].id == "logger" for node in generator.functions_ast)


def test_add_docstring(generator):
    generator._add_docstring()
    assert any(
        isinstance(node, Expr) and isinstance(node.value, Constant) and node.value.value == "Test API description"
        for node in generator.functions_ast
    )


def test_add_models_import(generator):
    generator.component_schemas = {"TestModel": {}}
    generator._add_models_import()
    assert any(isinstance(node, ImportFrom) and node.module == ".models" for node in generator.functions_ast)


def test_generate_models_ast(generator):
    generator.component_schemas = {
        "TestModel": {"properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
    }
    generator.generate_models_ast()
    assert any(isinstance(node, ClassDef) and node.name == "TestModel" for node in generator.models_ast)


def test_generate_function_ast(generator):
    generator.source_content = {
        "components": {"operations": {"test_function": {"description": "Test function description"}}}
    }
    generator.generate_function_ast("TestApp")
    assert any(isinstance(node, FunctionDef) and node.name == "test_function" for node in generator.functions_ast)

    def test_generate_files_from_asyncapi_with_async(generator, asyncapi_file, tmp_path):
        models_file = tmp_path / "models.py"
        functions_file = tmp_path / "functions.py"
        generator.generate_files_from_asyncapi(asyncapi_file, models_file, functions_file, "TestApp", is_async=True)

        assert models_file.exists()
        assert functions_file.exists()
        assert generator.is_async is True


def test_generate_files_from_asyncapi_without_async(generator, asyncapi_file, tmp_path):
    models_file = tmp_path / "models.py"
    functions_file = tmp_path / "functions.py"
    generator.generate_files_from_asyncapi(asyncapi_file, models_file, functions_file, "TestApp", is_async=False)

    assert models_file.exists()
    assert functions_file.exists()
    assert generator.is_async is False


def test_generate_models_ast_with_no_component_schemas(generator):
    generator.component_schemas = {}
    generator.generate_models_ast()
    assert generator.models_ast == []


def test_generate_function_ast_with_no_operations(generator):
    generator.source_content = {"components": {"operations": {}}}
    generator.generate_function_ast("TestApp", logger=False)
    # Even though there are no operations, the functions_ast might not be empty
    # because it can contain a docstring and an import from __future__.
    assert len(generator.functions_ast) == 2
    # Check if the first node is a docstring
    assert isinstance(generator.functions_ast[0], Expr)
    assert isinstance(generator.functions_ast[0].value, Constant)
    assert generator.functions_ast[0].value.value == "Test API description"
    # Check if the second node is an import from __future__
    assert isinstance(generator.functions_ast[1], ImportFrom)
    assert generator.functions_ast[1].module == "__future__"


def test_generate_function_ast_with_logger(generator):
    generator.source_content = {
        "components": {"operations": {"test_function": {"description": "Test function description"}}}
    }
    generator.generate_function_ast("TestApp", logger=True)
    assert any(isinstance(node, Assign) and node.targets[0].id == "logger" for node in generator.functions_ast)


def test_generate_function_ast_without_logger(generator):
    generator.source_content = {
        "components": {"operations": {"test_function": {"description": "Test function description"}}}
    }
    generator.generate_function_ast("TestApp", logger=False)

    assert not any(isinstance(node, Assign) and node.targets[0].id == "logger" for node in generator.functions_ast)
