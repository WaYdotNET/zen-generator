"""This module contains utilities for generating Python code from AsyncAPI specifications."""

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

from zen_generator.core.ast_utils import (
    convert_asyncapi_property_to_ast_node,
    create_ast_function_definition,
    get_component_schemas,
)
from zen_generator.core.io import load_yaml, save_python_file


@dataclass
class BasePythonGenerator:
    """Base class for Python generators.

    This class provides a basic interface for generating Python code from
    AsyncAPI specifications.

    Attributes:
        asyncapi_file (Path): The path to the AsyncAPI file.
        output_file (Path): The path to the generated Python file.
        models_file (Path): The path to the generated models file.
        override_base_class (str | None): The base class to override in the generated code.
        decorator_list (Sequence[expr]): A list of decorators to apply to the generated class.
        additional_imports (Sequence[stmt | ImportFrom]): Additional imports to include in the generated code.
        extra_assignments (Sequence[stmt]): Additional assignments to include in the generated code.
    """

    models_ast: list[stmt] = field(init=False, repr=False, default_factory=list)
    functions_ast: list[stmt] = field(init=False, repr=False, default_factory=list)
    extra_imports: Sequence[stmt | ImportFrom] = field(default_factory=list)
    extra_assignments: Sequence[stmt] = field(default_factory=list)
    override_base_class: str | None = None
    decorator_list: Sequence[expr] = field(default_factory=list)
    source_content: dict[str, Any] = field(init=False, repr=False, default_factory=dict)
    component_schemas: dict[str, Any] = field(init=False, repr=False, default_factory=dict)
    is_async: bool = False

    def __post__init__(self) -> None:
        """Generate Python files from an AsyncAPI specification.

        This method takes in the path to the AsyncAPI file, the path to the generated
        models file, the path to the generated functions file and the name of the
        application. Optionally, it takes in a boolean indicating whether the generated
        code should be asynchronous.

        Args:
            source_file (Path): The path to the AsyncAPI file.
            models_file (Path): The path to the generated models file.
            functions_file (Path): The path to the generated functions file.
            app_name (str): The name of the application.
            is_async (bool): Whether the generated code should be asynchronous.

        Returns:
            None
        """
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
        """Generate Python files from an AsyncAPI specification.

        This method takes in the path to the AsyncAPI file, the path to the generated
        models file, the path to the generated functions file and the name of the
        application. Optionally, it takes in a boolean indicating whether the generated
        code should be asynchronous.

        Args:
            source_file: The path to the AsyncAPI file.
            models_file: The path to the generated models file.
            functions_file: The path to the generated functions file.
            app_name: The name of the application.
            is_async: Whether the generated code should be asynchronous.

        Returns:
            None
        """
        self.is_async = is_async
        self.source_content = load_yaml(source_file) or {}
        self.component_schemas = get_component_schemas(self.source_content) or {}

        self.generate_models_ast()
        save_python_file(self.models_ast, models_file)
        self.generate_function_ast(app_name, models_file.stem)
        save_python_file(self.functions_ast, functions_file)

    def _add_logger_setup(self, app_name: str) -> None:
        """Add logger setup to the module.

        This method adds a logger setup to the module, which creates a logger
        with the name of the application and sets up a basic configuration.

        Args:
            app_name (str): The name of the application.

        Returns:
            None
        """
        self.functions_ast.append(
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
        """Add docstring to the module.

        This method adds a docstring to the module, which contains the description
        of the application.

        Returns:
            None
        """
        docstring = self.source_content.get("info", {}).get("description", "Test API description")
        if isinstance(docstring, str):
            self.functions_ast.append(Expr(value=Constant(value=docstring)))

    def _add_models_import(self, module_name: str = "models") -> None:
        """Add import statement for the models module.

        This method adds an import statement to the module, which imports all
        the models defined in the `models` module.

        Args:
            module_name (str): The name of the module to import. Defaults to
                "models".

        Returns:
            None
        """
        if self.component_schemas.items():
            names = [alias(name=f"{model}") for model in self.component_schemas]
            import_from = ImportFrom(
                module=f".{module_name}",
                names=names,
                level=0,
            )
            self.functions_ast.append(import_from)

    def generate_models_ast(self) -> None:
        """Generate the models as a sequence of AST nodes.

        This method generates the models as a sequence of AST nodes, which
        correspond to the classes defined in the `models` module. The classes are
        generated from the `components/schemas` field of the AsyncAPI document.

        Returns:
            None
        """
        if not self.component_schemas:
            return

        self.models_ast.extend(self.extra_imports)

        for class_name, schema in self.component_schemas.items():
            class_body: list[stmt] = []
            base_class_id = self.override_base_class or schema.get("base_class", "object")
            if schema.get("properties"):
                for prop_name, prop_value in schema["properties"].items():
                    annotation = convert_asyncapi_property_to_ast_node(prop_value)
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
        """Generate the functions as a sequence of AST nodes.

        This method generates the functions as a sequence of AST nodes, which
        correspond to the functions defined in the `functions` module. The functions
        are generated from the `components/messages` field of the AsyncAPI document.

        Args:
            app_name (str): The name of the application.
            module_name (str, optional): The name of the module that contains the
                models. Defaults to "models".
            logger (bool, optional): Whether to add logger setup code. Defaults to
                True.

        Returns:
            None
        """
        self._add_docstring()

        self.functions_ast.append(ImportFrom(module="__future__", names=[alias(name="annotations")], level=0))
        self.functions_ast.extend(self.extra_imports)

        if logger:
            self.functions_ast.append(Import(names=[alias(name="logging")]))

        self._add_models_import(module_name)
        self.functions_ast.extend(self.extra_assignments)

        if logger:
            self._add_logger_setup(app_name)
        self._add_function_definitions()

    def _add_function_definitions(self) -> None:
        """Generate the functions as a sequence of AST nodes.

        This method generates the functions as a sequence of AST nodes, which
        correspond to the functions defined in the `functions` module. The functions
        are generated from the `components/messages` field of the AsyncAPI document.

        Args:
            components (dict): The components field of the AsyncAPI document.
            functions (dict): The functions field of the AsyncAPI document.

        Returns:
            None
        """
        components = self.source_content.get("components", {})
        functions = components.get("operations", {})

        if not functions:
            return

        for func_name in functions:
            processed_decorators = self._process_decorators(func_name)
            function_args = self._build_function_args(components, func_name)
            returns_node = self._build_return_annotation(components, func_name)
            description = functions[func_name].get("description")

            func_def = create_ast_function_definition(
                func_name, function_args, description, returns_node, self.is_async, processed_decorators
            )
            self.functions_ast.append(func_def)

    def _process_decorators(self, func_name: str) -> list[expr]:
        """Process decorators for a function.

        Process the decorator list for a function by replacing the `{func_name}`
        placeholder with the actual function name and converting the resulting
        string back to an AST node.

        Args:
            func_name (str): The name of the function.

        Returns:
            list[expr]: The processed decorator nodes.
        """
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
        """Generate function arguments from the components/messages field of the AsyncAPI document.

        This function generates the function arguments from the
        components/messages field of the AsyncAPI document. The function
        arguments are generated from the payload properties of the request message.

        Args:
            components (dict): The components field of the AsyncAPI document.
            func_name (str): The name of the function.

        Returns:
            list[arg]: The generated function arguments.
        """
        function_args: list[arg] = []
        request_params = components.get("messages", {}).get(f"{func_name}_request", {}).get("payload", {})

        if request_params.get("properties"):
            for param_name, param_value in request_params["properties"].items():
                annotation_node = convert_asyncapi_property_to_ast_node(param_value)
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
        """Generate the return annotation of the function from the components/messages field of the AsyncAPI document.

        This function generates the return annotation of the function from the
        components/messages field of the AsyncAPI document. The return annotation
        is generated from the payload properties of the response message.

        Args:
            components (dict): The components field of the AsyncAPI document.
            func_name (str): The name of the function.

        Returns:
            Any: The generated return annotation.
        """
        response = components.get("messages", {}).get(f"{func_name}_response", {})
        response_param = response.get("payload", {})
        returns_node = convert_asyncapi_property_to_ast_node(response_param)

        if response_param and not response_param.get("format") == "required" and returns_node:
            returns_node = BinOp(
                left=cast(expr, returns_node),
                op=BitOr(),
                right=Constant(value=None),
            )

        return returns_node
