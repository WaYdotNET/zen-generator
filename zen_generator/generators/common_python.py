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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence, cast

from zen_generator.core.ast_utils import convert_property, create_ast_function_definition, get_component_schemas
from zen_generator.core.io import load_yaml, save_python_file


@dataclass
class BasePythonGenerator:
    models_ast: list[stmt] = field(init=False, repr=False, default_factory=list)
    fuctions_ast: list[stmt] = field(init=False, repr=False, default_factory=list)
    additional_imports: Sequence[stmt | ImportFrom] = field(default_factory=list)
    additional_assingments: Sequence[stmt] = field(default_factory=list)
    override_base_class: str | None = None
    decorator_list: Sequence[expr] = field(default_factory=list)
    source_content: dict[str, Any] = field(init=False, repr=False, default_factory=dict)
    component_schemas: dict[str, Any] = field(init=False, repr=False, default_factory=dict)
    is_async: bool = False

    def __post__init__(self) -> None:
        self.models_ast.extend(
            [
                ImportFrom(module="__future__", names=[alias(name="annotations")], level=0),
            ]
        )

    def generate_files_from_asyncapi(
        self,
        source_file: Path,
        models_file: Path,
        functions_file: Path,
        app_name: str,
        is_async: bool = False,
    ) -> None:
        """
        Generate the Python files from the AsyncAPI specification
        :param source_file: The source file
        :param models_file: The models file
        :param functions_file: The functions file
        :param app_name: The name of the application
        :param is_async: Whether the function is async
        :return: None
        """
        self.is_async = is_async
        self.source_content = load_yaml(source_file) or {}
        self.component_schemas = get_component_schemas(self.source_content) or {}

        self.generate_models_ast()
        save_python_file(self.models_ast, models_file)
        self.generate_function_ast(app_name, models_file.stem)
        save_python_file(self.fuctions_ast, functions_file)

    def _add_logger_setup(self, app_name: str) -> None:
        """
        Add logger setup to the function file
        :param app_name: The name of the application
        :return: None
        """
        self.fuctions_ast.append(
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

    def _add_docstring(self) -> None:
        """
        Add the docstring to the function
        :param source_content:  The source content
        :return: None
        """
        try:
            docstring = self.source_content["info"]["description"]
            self.fuctions_ast.append(Expr(value=Constant(value=docstring)))
        except (KeyError, TypeError):
            pass

    def _add_models_import(self, module_name: str = "models") -> None:
        """
        Add import for models
        :param models: The models
        :return: None
        """
        if self.component_schemas.items():
            names = [alias(name=f"{model}") for model in self.component_schemas]
            import_from = ImportFrom(
                module=f".{module_name}",
                names=names,
                level=0,
            )
            self.fuctions_ast.append(import_from)

    def generate_models_ast(self) -> None:
        """
        Generate the AST for the models
        :param schemas: The schemas
        :param include_typing_import: Whether to include typing import
        :param include_enums_import: Whether to include enums import
        :return: The AST
        """
        if not self.component_schemas:
            return

        self.models_ast.extend(self.additional_imports)

        for class_name, schema in self.component_schemas.items():
            class_body: list[stmt] = []
            base_class_id = self.override_base_class or schema.get("base_class", "object")
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
            self.models_ast.append(klass)

    def generate_function_ast(
        self,
        app_name: str,
        module_name: str = "models",
        logger: bool = True,
    ) -> None:
        self._add_docstring()

        self.fuctions_ast.append(ImportFrom(module="__future__", names=[alias(name="annotations")], level=0))
        self.fuctions_ast.extend(self.additional_imports)

        if logger:
            self.fuctions_ast.append(Import(names=[alias(name="logging")]))

        self._add_models_import(module_name)
        self.fuctions_ast.extend(self.additional_assingments)

        if logger:
            self._add_logger_setup(app_name)
        self._add_function_definitions()

    def _add_function_definitions(self) -> None:
        components = self.source_content.get("components", {})
        functions = components.get("operations", {})

        for func_name in functions:
            processed_decorators = self._process_decorators(func_name)
            function_args = self._build_function_args(components, func_name)
            returns_node = self._build_return_annotation(components, func_name)
            description = functions[func_name].get("description")

            func_def = create_ast_function_definition(
                func_name, function_args, description, returns_node, self.is_async, processed_decorators
            )
            self.fuctions_ast.append(func_def)

    def _process_decorators(self, func_name: str) -> list[expr]:
        processed_decorators = []
        for dec in self.decorator_list:
            # Convert decorator to string, replace placeholder and convert back to AST
            dec_str = unparse(dec)
            dec_str = dec_str.replace("/{func_name}", f"/{func_name}")

            # Parse the string back to an AST
            parsed = parse(dec_str).body[0]
            if isinstance(parsed, Expr):
                processed_decorators.append(parsed.value)

        return processed_decorators

    def _build_function_args(self, components: dict[str, Any], func_name: str) -> list[arg]:
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

    def _build_return_annotation(self, components: dict[str, Any], func_name: str) -> Any:
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
