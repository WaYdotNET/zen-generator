"""This module contains utilities for generating Python code from AsyncAPI specifications.

The functions in this module provide a higher-level interface than the `ast` module,
and are used to generate Python code from AsyncAPI specifications.

"""
from __future__ import annotations

from ast import Assign, Attribute, Call, Constant, ImportFrom, Load, Name, Store, alias

from zen_generator.generators.common_python import BasePythonGenerator


class Generator:
    """Class for generating Python code from AsyncAPI specification.

    Attributes:
        asyncapi_file (Path): The path to the AsyncAPI file.
        output_file (Path): The path to the generated Python file.
        models_file (Path): The path to the generated models file.
        override_base_class (str | None): The base class to override in the generated code.
        decorator_list (Sequence[expr]): A list of decorators to apply to the generated class.
        additional_imports (Sequence[stmt | ImportFrom]): Additional imports to include in the generated code.
        additional_assingments (Sequence[stmt]): Additional assignments to include in the generated code.

    Methods:
        generate_files_from_asyncapi: Generate Python files from an AsyncAPI specification.
    """
    @staticmethod
    def fastapi_generator() -> BasePythonGenerator:
        """Generate a FastAPI generator from an AsyncAPI specification.

        Returns:
            BasePythonGenerator: A generator for generating FastAPI code from an AsyncAPI specification.
        """
        return BasePythonGenerator(
            override_base_class="BaseModel",
            additional_imports=[
                ImportFrom(module="fastapi", names=[alias(name="FastAPI")], level=0),
            ],
            additional_assingments=[
                Assign(
                    targets=[Name(id="app", ctx=Store())],
                    value=Call(func=Name(id="FastAPI", ctx=Load()), args=[], keywords=[]),
                )
            ],
            decorator_list=[
                Call(
                    func=Attribute(value=Name(id="app", ctx=Load()), attr="get", ctx=Load()),
                    args=[Constant(value="/{func_name}")],
                    keywords=[],
                )
            ],
        )

    @staticmethod
    def pure_python_generator() -> BasePythonGenerator:
        """Generate a pure Python generator from an AsyncAPI specification.

        Returns:
            BasePythonGenerator: A generator for generating pure Python code from an AsyncAPI specification.
        """
        return BasePythonGenerator(
            additional_imports=[
                ImportFrom(module="typing", names=[alias(name="TypedDict")], level=0),
                ImportFrom(module="utils.enums", names=[alias(name="Choices")], level=0),
            ]
        )
