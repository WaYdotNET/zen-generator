"""This module contains utilities for working with Abstract Syntax Trees (ASTs).

The functions in this module provide a higher-level interface than the `ast` module,
and are used to generate Python code from AsyncAPI specifications.

"""
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
    """Convert an AST annotation to a dictionary.

    Args:
        ast_annotation: The AST annotation

    Returns:
        A dictionary containing information about the annotation
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
    """Convert a list of dictionaries (result of `convert_ast_annotation_to_dict`) to an AsyncAPI schema.

    Args:
        input_annotation: A list of dictionaries containing the annotation information.

    Returns:
        A dictionary containing the AsyncAPI schema.
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
    """Generate a dictionary containing the AsyncAPI schema for a ClassDef node.

    Args:
        node: The ClassDef node to generate the schema for.

    Returns:
        A dictionary containing the AsyncAPI schema.
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
    """Converts an AST tree to a formatted string of Python code.

    Args:
        ast_nodes: A list of AST nodes to convert.

    Returns:
        A formatted string of Python code.
    """
    module = Module(body=ast_nodes, type_ignores=[])
    raw_code = unparse(fix_missing_locations(module))
    return format_python_code(raw_code)


def components_schemas(tree: AST | None) -> dict[str, Any]:
    """Generates a dictionary containing the component schemas from an AST tree.

    Args:
        tree: The AST tree to parse. If None, an empty dictionary is returned.

    Returns:
        A dictionary containing the component schemas.
    """
    result: dict[str, Any] = {}
    if not tree:
        return result

    for node in walk(tree):
        if isinstance(node, ClassDef):
            result[node.name] = parse_class(node)
    return result


def get_component_schemas(source: dict[str, Any] | None) -> dict[str, Any] | None:
    """Gets the component schemas from an AsyncAPI dictionary.

    Args:
        source: The AsyncAPI dictionary. If None, None is returned.

    Returns:
        The component schemas as a dictionary or None if the source does not contain
        the component schemas.
    """
    source = source or {}
    try:
        return source["components"]["schemas"]
    except KeyError:
        return None


def generate_bin_op(
    values: Sequence[str | Name | Subscript | Constant | BinOp | None],
) -> Name | Subscript | Constant | BinOp | None:
    """Generates a binary operation from a sequence of values.

    If the sequence is empty, returns None.
    If the sequence contains only one value, returns the value.
    If the sequence contains more than one value, returns a binary operation
    where the left operand is the result of the recursive call with the
    sequence of values excluding the last one, and the right operand is the
    last value in the sequence.

    The binary operation is generated with the BitOr operator.

    Args:
        values: A sequence of values to generate the binary operation from.

    Returns:
        A Name, Subscript, Constant, BinOp or None representing the generated
        binary operation.
    """
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
    """Converts an AsyncAPI property to an AST node.

    Args:
        pro: The AsyncAPI property to convert

    Returns:
        The AST node representing the property
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
    """Convert an AsyncAPI array property to an AST node.

    Args:
        pro: The AsyncAPI array property to convert

    Returns:
        The AST Subscript

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
    """Create a new AST function definition node.

    Args:
        function_name: The name of the function
        function_arguments: The arguments of the function
        docstring: The docstring of the function
        return_annotation: The return annotation of the function
        is_async: Whether the function is async
        decorator_list: The list of decorators for the function

    Returns:
        The AST function definition node

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
