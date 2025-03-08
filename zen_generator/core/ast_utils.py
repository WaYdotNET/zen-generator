from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    AsyncFunctionDef,
    BinOp,
    BitOr,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    List,
    Load,
    Module,
    Name,
    Slice,
    Subscript,
    Tuple,
    arg,
    arguments,
    expr,
    fix_missing_locations,
    stmt,
    unparse,
    walk,
)
from typing import Any, Sequence, TypeAlias

from zen_generator.core.formatting import format_python_code
from zen_generator.core.type_system import (
    convert_asyncapi_to_python,
    convert_python_to_asyncapi,
)

AnnotationNode: TypeAlias = AST | Subscript | List | Name | BinOp | Constant | Tuple | Slice | None
SCHEMA_PREFIX = "#/components/schemas/"


def convert_ast_annotation_to_dict(
    ast_annotation: AnnotationNode,
) -> list[dict[str, Any]]:
    """
    Convert an AST annotation to a dictionary
    :param ast_annotation: AST annotation
    :return: List of dictionaries
    """
    match ast_annotation:
        case Subscript():
            kind = ast_annotation.value.id if hasattr(ast_annotation.value, "id") else None
            if kind == "dict" and hasattr(ast_annotation.slice, "elts"):
                value = [
                    ast_annotation.slice.elts[0].id,
                    ast_annotation.slice.elts[1].id,
                ]
            elif kind == "list":
                if isinstance(ast_annotation.slice, (Tuple, Subscript)):
                    value = convert_ast_annotation_to_dict(ast_annotation.slice)
                elif hasattr(ast_annotation.slice, "id"):
                    value = ast_annotation.slice.id
                else:
                    value = None
            else:
                value = ast_annotation.slice.id if hasattr(ast_annotation.slice, "id") else None
            return [{"slice": kind, "value": value}]
        case List():
            return [{"slice": "list", "value": None}]
        case Name():
            return [{"slice": None, "value": ast_annotation.id}]
        case BinOp():
            left_type = convert_ast_annotation_to_dict(ast_annotation.left)
            right_type = convert_ast_annotation_to_dict(ast_annotation.right)
            return left_type + right_type
        case Constant() if ast_annotation.value is None:
            return [{"slice": None, "value": None}]
        case _:
            return []


def convert_annotations_to_asyncapi_schemas(
    input_annotation: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Convert Python type annotations to AsyncAPI schema format
    :param input_annotation: List of dictionaries representing parsed annotations
    :return: AsyncAPI schema representation
    """
    required = True
    schema_items: list[dict[str, Any]] = []

    valid_annotations = [annotation for annotation in input_annotation if annotation["value"] is not None]

    if len(valid_annotations) < len(input_annotation):
        required = False

    for annotation in valid_annotations:
        if isinstance(annotation["value"], str):
            primitive_type = convert_python_to_asyncapi(annotation["value"])
            if primitive_type:
                value = primitive_type
                item_type = "type"
            else:
                value = f"{SCHEMA_PREFIX}{annotation['value']}"
                item_type = "$ref"
        else:
            value = "object"
            item_type = "type"

        if annotation["slice"] == "list":
            schema_items.append({"type": "array", "items": {item_type: value}})
        else:
            schema_items.append({item_type: str(value)})

    properties: dict[str, Any] = (
        {} if not schema_items else schema_items[0] if len(schema_items) == 1 else {"oneOf": schema_items}
    )
    return {"required": required, "properties": properties}


def parse_class(node: ClassDef) -> dict[str, Any]:
    """
    Parse a class node to a dictionary
    :param node: Class node
    :return: Dictionary
    """
    try:
        base = node.bases[0]
        base_class = base.id if hasattr(base, "id") else "object"
    except (IndexError, AttributeError):
        base_class = "object"

    properties = {}
    required = []
    schema = {"type": "object", "base_class": base_class}
    for class_element in node.body:
        if isinstance(class_element, AnnAssign) and isinstance(class_element.target, Name):
            property_name = class_element.target.id
            items = convert_ast_annotation_to_dict(class_element.annotation)
            conv = convert_annotations_to_asyncapi_schemas(items)
            if conv.get("required"):
                required.append(property_name)
                del conv["required"]
            properties[property_name] = conv.get("properties")

    schema["required"] = required
    schema["properties"] = properties
    return schema


def convert_ast_to_code(ast_nodes: list[Any]) -> str:
    """
    Convert AST nodes to Python code
    :param ast_nodes: List of AST nodes
    :return: Python code
    """
    module = Module(body=ast_nodes, type_ignores=[])
    raw_code = unparse(fix_missing_locations(module))
    return format_python_code(raw_code)


def components_schemas(tree: AST | None) -> dict[str, Any]:
    """
    Parse AST tree to components schemas
    :param tree: AST tree
    :return: Components schemas
    """
    result: dict[str, Any] = {}
    if not tree:
        return result

    for node in walk(tree):
        if isinstance(node, ClassDef):
            result[node.name] = parse_class(node)
    return result


def get_component_schemas(source: dict[str, Any] | None) -> dict[str, Any] | None:
    source = source or {}
    try:
        return source["components"]["schemas"]
    except KeyError:
        return None


def generate_bin_op(
    values: Sequence[str | Name | Subscript | Constant | BinOp | None],
) -> Name | Subscript | Constant | BinOp | None:
    if not values:
        return None

    if len(values) == 1:
        value = values[0]
        if value is None:
            return Constant(value=None)
        elif isinstance(value, str):
            return Name(id=value, ctx=Load())
        else:
            return value
    else:
        left = generate_bin_op(values[:-1])
        right = generate_bin_op([values[-1]])
        if left is not None and right is not None:
            return BinOp(left=left, op=BitOr(), right=right)
        else:
            return left or right


def convert_property(
    pro: dict[str, Any] | None,
) -> Name | Subscript | Constant | BinOp | None:
    """
    Convert an AsyncAPI property to an AST node
    :param pro: AsyncAPI property
    :return: AST node
    """

    match pro:
        case None:
            return Constant(value=None)
        case {"type": "array"}:
            return _convert_array_property(pro)
        case {"type": type_value}:
            return Name(id=convert_asyncapi_to_python(type_value), ctx=Load())
        case {"$ref": ref_value}:
            ref_name = ref_value.replace(SCHEMA_PREFIX, "")
            return Name(id=convert_asyncapi_to_python(ref_name), ctx=Load())
        case {"oneOf": one_of_values}:
            type_nodes = [convert_property(one_of) for one_of in one_of_values]
            return generate_bin_op(type_nodes)
        case _:
            return Constant(value=None)


def _convert_array_property(pro: dict[str, Any]) -> Subscript:
    """
    Convert an AsyncAPI array property to an AST node
    :param pro: AsyncAPI array property
    :return: AST node
    """
    items = pro.get("items", {})

    if "$ref" in items:
        type_name = items.get("$ref").replace(SCHEMA_PREFIX, "")
    else:
        type_name = items.get("type", "")

    item_type = convert_asyncapi_to_python(type_name)

    return Subscript(
        value=Name(id="list", ctx=Load()),
        slice=Name(id=item_type, ctx=Load()),
        ctx=Load(),
    )


def create_ast_function_definition(
    function_name: str,
    function_arguments: Sequence[arg],
    docstring: str | None,
    return_annotation: Any,
    is_async: bool = False,
    decorator_list: list[expr] | None = None,
) -> FunctionDef | AsyncFunctionDef:
    """
    Create a function definition AST node.
    :param function_name:  The name of the function
    :param function_arguments:  The arguments of the function
    :param docstring:  The docstring of the function
    :param return_annotation: The return annotation of the function
    :param is_async:  Whether the function is async
    :param decorator_list: The list of decorators for the function
    :return:  The function definition AST node
    """
    decorator_list = decorator_list or []
    body: list[stmt] = [Expr(value=Constant(value=Ellipsis))]

    if docstring:
        body.insert(0, Expr(value=Constant(value=docstring)))

    func_def_class = AsyncFunctionDef if is_async else FunctionDef

    return func_def_class(
        name=function_name,
        args=arguments(
            posonlyargs=[],
            args=list(function_arguments),
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
        ),
        body=body,
        decorator_list=decorator_list,
        returns=return_annotation,
    )
