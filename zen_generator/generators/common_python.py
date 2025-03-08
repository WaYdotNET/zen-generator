from __future__ import annotations

from ast import (
    AnnAssign,
    Assign,
    Attribute,
    BinOp,
    BitOr,
    Call,
    ClassDef,
    Constant,
    Expr,
    Import,
    ImportFrom,
    Load,
    Name,
    Pass,
    Store,
    alias,
    arg,
    expr,
    parse,
    stmt,
    unparse,
)
from typing import Any, Sequence, cast

from zen_generator.core.ast_utils import convert_property, create_ast_function_definition


def _add_logger_setup(function_body: list[stmt], app_name: str) -> None:
    """
    Add logger setup to the function file
    :param function_body: The function body
    :param app_name: The name of the application
    :return: None
    """
    function_body.append(
        Assign(
            targets=[Name(id="logger", ctx=Store())],
            value=Call(
                func=Attribute(
                    value=Name(id="logging", ctx=Load()),
                    attr="getLogger",
                    ctx=Load(),
                ),
                args=[Constant(value=app_name)],
                keywords=[],
            ),
        )
    )


def _add_docstring(function_body: list[stmt], source_content: dict[str, Any]) -> None:
    """
    Add the docstring to the function
    :param function_body:  The function body
    :param source_content:  The source content
    :return: None
    """
    try:
        docstring = source_content["info"]["description"]
        function_body.append(Expr(value=Constant(value=docstring)))
    except (KeyError, TypeError):
        pass


def _add_models_import(function_body: list[stmt], models: dict[str, Any], module_name: str = "models") -> None:
    """
    Add import for models
    :param function_body: The function body
    :param models: The models
    :return: None
    """
    if models.items():
        names = [alias(name=f"{model}") for model in models]
        import_from = ImportFrom(
            module=f".{module_name}",
            names=names,
            level=0,
        )
        function_body.append(import_from)


def generate_models_ast(
    schemas: dict[str, Any],
    override_base_class: str | None = None,
    include_typing_import: bool = True,
    include_enums_import: bool = True,
    additional_imports: Sequence[stmt | ImportFrom] | None = None,
) -> list[stmt]:
    """
    Generate the AST for the models
    :param schemas: The schemas
    :param override_base_class: The base class to override
    :param include_typing_import: Whether to include typing import
    :param include_enums_import: Whether to include enums import
    :param additional_imports: Additional imports
    :return: The AST
    """
    models_ast: list[stmt] = [ImportFrom(module="__future__", names=[alias(name="annotations")], level=0)]
    if additional_imports:
        models_ast.extend(additional_imports)

    if include_typing_import:
        models_ast.append(ImportFrom(module="typing", names=[alias(name="TypedDict")], level=0))
    if include_enums_import:
        models_ast.append(ImportFrom(module="utils.enums", names=[alias(name="Choices")], level=0))

    for class_name, schema in schemas.items():
        class_body: list[stmt] = []
        base_class_id = override_base_class or schema.get("base_class", "object")
        if schema.get("properties"):
            for prop_name, prop_value in schema["properties"].items():
                annotation = convert_property(prop_value)
                if annotation is not None and prop_name not in schema.get("required", []):
                    annotation = BinOp(
                        left=cast(expr, annotation),
                        op=BitOr(),
                        right=Constant(value=None),
                    )
                if annotation is not None:
                    class_body.append(
                        AnnAssign(
                            target=Name(id=prop_name, ctx=Store()),
                            annotation=cast(expr, annotation),
                            simple=1,
                        )
                    )
        else:
            class_body = [Pass()]

        klass = ClassDef(
            name=class_name,
            bases=[Name(id=base_class_id, ctx=Load())],
            body=class_body,
            decorator_list=[],
            keywords=[],
        )
        models_ast.append(klass)

    return models_ast


def generate_function_ast(
    source_content: dict[str, Any] | None,
    models: dict[str, Any] | None,
    app_name: str,
    module_name: str = "models",
    logger: bool = True,
    is_async: bool = False,
    additional_imports: Sequence[stmt] | None = None,
    additional_imports_after_models: Sequence[stmt] | None = None,
    decorator_list: Sequence[expr] | None = None,
) -> list[stmt]:
    """
    Generate the AST for the functions
    :param source_content: The source content
    :param models: The models
    :param app_name: The name of the application
    :param module_name: The name of the module
    :param logger: Whether to include logging
    :param is_async: Whether the function is async
    :param additional_imports: Additional imports
    :param additional_imports_after_models: Additional imports after models
    :param decorator_list: The list of decorators for the function
    :return: The AST
    """
    function_body: list[stmt] = []
    source_content = source_content or {}
    models = models or {}
    components = source_content.get("components", {})

    _add_docstring(function_body, source_content)

    function_body.append(ImportFrom(module="__future__", names=[alias(name="annotations")], level=0))
    if additional_imports:
        function_body.extend(additional_imports)

    if logger:
        function_body.append(Import(names=[alias(name="logging")]))

    _add_models_import(function_body, models, module_name)

    if additional_imports_after_models:
        function_body.extend(additional_imports_after_models)

    if logger:
        _add_logger_setup(function_body, app_name)
    _add_function_definitions(function_body, components, is_async, decorator_list)
    return function_body


def _add_function_definitions(
    function_body: list[stmt],
    components: dict[str, Any],
    is_async: bool = False,
    decorator_list: Sequence[expr] | None = None,
) -> None:
    """
    Add function definitions to the function
    :param function_body: The function body
    :param components: The components
    :param is_async: Whether the function is async
    :param decorator_list: The list of decorators for the function
    :return: None
    """
    functions = components.get("operations", {})

    for func_name in functions:
        processed_decorators = _process_decorators(decorator_list, func_name)
        function_args = _build_function_args(components, func_name)
        returns_node = _build_return_annotation(components, func_name)
        description = functions[func_name].get("description")

        func_def = create_ast_function_definition(
            func_name, function_args, description, returns_node, is_async, processed_decorators
        )
        function_body.append(func_def)


def _process_decorators(decorator_list: Sequence[expr] | None, func_name: str) -> list[expr]:
    """
    Process decorators and substitute function name placeholders
    :param decorator_list: List of decorator AST expressions
    :param func_name: Function name to substitute in decorators
    :return: List of processed decorator expressions
    """
    if not decorator_list:
        return []

    processed_decorators = []
    for dec in decorator_list:
        # Convert decorator to string, replace placeholder and convert back to AST
        dec_str = unparse(dec)
        dec_str = dec_str.replace("/{func_name}", f"/{func_name}")

        # Parse the string back to an AST
        parsed = parse(dec_str).body[0]
        if isinstance(parsed, Expr):
            processed_decorators.append(parsed.value)

    return processed_decorators


def _build_function_args(components: dict[str, Any], func_name: str) -> list[arg]:
    """
    Build function arguments from request parameters
    :param components: The components
    :param func_name: The function name
    :return: The function arguments
    """
    function_args: list[arg] = []
    request_params = components.get("messages", {}).get(f"{func_name}_request", {}).get("payload", {})

    if request_params.get("properties"):
        for param_name, param_value in request_params["properties"].items():
            annotation_node = convert_property(param_value)
            if annotation_node and param_name not in request_params.get("required", []):
                annotation_node = BinOp(
                    left=cast(expr, annotation_node),
                    op=BitOr(),
                    right=Constant(value=None),
                )
            if annotation_node:
                function_args.append(arg(arg=param_name, annotation=annotation_node))

    return function_args


def _build_return_annotation(components: dict[str, Any], func_name: str) -> Any:
    """
    Build return annotation from response parameters
    :param components: The components
    :param func_name: The function name
    :return: The return annotation
    """
    response = components.get("messages", {}).get(f"{func_name}_response", {})
    response_param = response.get("payload", {})
    returns_node = convert_property(response_param)

    if response_param and not response_param.get("format") == "required" and returns_node:
        returns_node = BinOp(
            left=cast(expr, returns_node),
            op=BitOr(),
            right=Constant(value=None),
        )

    return returns_node
