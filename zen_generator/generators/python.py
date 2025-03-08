from __future__ import annotations

from ast import Assign, Attribute, Call, Constant, ImportFrom, Load, Name, Store, alias

from zen_generator.generators.common_python import BasePythonGenerator


class Generator:
    @staticmethod
    def fastapi_generator() -> BasePythonGenerator:
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
        return BasePythonGenerator(
            additional_imports=[
                ImportFrom(module="typing", names=[alias(name="TypedDict")], level=0),
                ImportFrom(module="utils.enums", names=[alias(name="Choices")], level=0),
            ]
        )
