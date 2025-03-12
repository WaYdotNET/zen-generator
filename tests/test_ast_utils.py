from __future__ import annotations

from ast import ClassDef, Constant, Expr, FunctionDef, Load, Name, Pass, arg, arguments


from zen_generator.core.ast_utils import generate_code_from_ast
from zen_generator.core.formatting import format_python_code


def test_generate_code_from_ast_with_function() -> None:
    func_def = FunctionDef(
        name="test_function",
        args=arguments(
            posonlyargs=[],
            args=[
                arg(arg="x", annotation=Name(id="str", ctx=Load())),
                arg(arg="y", annotation=Name(id="int", ctx=Load())),
            ],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
        ),
        body=[Pass()],
        decorator_list=[],
        returns=Name(id="None", ctx=Load()),
    )
    ast_nodes = [func_def]

    result = generate_code_from_ast(ast_nodes)

    expected_code = format_python_code("def test_function(x:str, y:int) -> None:\n    pass\n")
    assert result == expected_code


def test_generate_code_from_ast_with_class() -> None:
    class_def = ClassDef(
        name="TestClass",
        bases=[],
        keywords=[],
        body=[
            FunctionDef(
                name="__init__",
                args=arguments(
                    posonlyargs=[],
                    args=[arg(arg="self", annotation=None)],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=[Pass()],
                decorator_list=[],
                returns=Name(id="None", ctx=Load()),
            )
        ],
        decorator_list=[],
    )
    ast_nodes = [class_def]

    result = generate_code_from_ast(ast_nodes)

    expected_code = format_python_code("class TestClass:\n    def __init__(self) -> None:\n        pass\n")
    assert result == expected_code


def test_generate_code_from_ast_with_multiple_nodes() -> None:
    func_def = FunctionDef(
        name="test_function",
        args=arguments(
            posonlyargs=[],
            args=[
                arg(arg="x", annotation=Name(id="str", ctx=Load())),
                arg(arg="y", annotation=Name(id="bool", ctx=Load())),
            ],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[Constant(value=True)],
        ),
        body=[Pass()],
        decorator_list=[],
        returns=Name(id="None", ctx=Load()),
    )
    class_def = ClassDef(
        name="TestClass",
        bases=[],
        keywords=[],
        body=[
            FunctionDef(
                name="__init__",
                args=arguments(
                    posonlyargs=[],
                    args=[arg(arg="self", annotation=None)],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=[Pass()],
                decorator_list=[],
                returns=Name(id="None", ctx=Load()),
            )
        ],
        decorator_list=[],
    )
    ast_nodes = [func_def, class_def]

    result = generate_code_from_ast(ast_nodes)

    expected_code = format_python_code(
        "def test_function(x:str, y:bool = True) -> None:\n    pass\n\nclass TestClass:\n    def __init__(self) -> None:\n        pass\n"
    )
    assert result == expected_code
