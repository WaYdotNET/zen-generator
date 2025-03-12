from __future__ import annotations

from pathlib import Path

import pytest

from zen_generator.cli import fastapi, pure_python
from zen_generator.core.ast_utils import generate_code_from_ast, get_component_schemas
from zen_generator.core.exception import InvalidFile
from zen_generator.core.io import load_yaml
from zen_generator.generators.python import Generator


def test_source_path_yaml_is_valid() -> None:
    file: Path = Path("async_api_test.yaml")
    assert load_yaml(file)


def test_source_path_yaml_directory_is_not_valid() -> None:
    file: Path = Path("./")
    with pytest.raises(InvalidFile, match="The source is a directory"):
        load_yaml(file)


def test_source_path_yaml_not_found_is_not_valid() -> None:
    file: Path = Path("./fake_path")
    with pytest.raises(InvalidFile):
        load_yaml(file)


def test_generate_model() -> None:
    source: Path = Path("./test_models.yaml")
    source_content = load_yaml(source)
    component_schemas = get_component_schemas(source_content) or {}

    generator = Generator.pure_python_generator()
    generator.component_schemas = component_schemas
    generator.generate_models_ast()

    model = generator.models_ast
    py = generate_code_from_ast(model)

    aspect_result = """from __future__ import annotations

from typing import TypedDict

from utils.enums import Choices


class TaskAttachment(TypedDict):
    name: str
    kind: str


class UserTaxDeclarationInfo(TypedDict):
    utd_id: int | None
    full_environment: bool


class Mida4TaskEnvironmentChoices(Choices):
    pass


class FooBar(TypedDict):
    env: str | None
    baz: UserTaxDeclarationInfo | list[bool] | int
    foo: str | object
"""

    assert py == aspect_result


def test_generate_functions() -> None:
    source = Path("./test_functions.yaml")
    app_name = "Fake"
    generator = Generator.pure_python_generator()

    generator.load_asyncapi_content(source)
    generator.generate_function_ast(app_name)
    py = generate_code_from_ast(generator.functions_ast)

    aspect_result = """\"\"\"Test API description\"\"\"

from __future__ import annotations

import logging
from typing import TypedDict

from utils.enums import Choices

logger = logging.getLogger("Fake")


def get_attachments_from_utd(utd_id: int | str | TaskAttachment, kinds: list[str]) -> list[TaskAttachment]: ...


def generate_sync_task(
    utd_info: UserTaxDeclarationInfo, sequence: int | None, skip_create_f24s: bool
) -> int | None: ...


def generate_iiacc_task(
    utd_info: UserTaxDeclarationInfo, fiscal_elements: list[object] | None
) -> int | str | TaskAttachment | None: ...


def generate_iva_sync_task(
    user_id: int, ref_year: int, environment: Mida4TaskEnvironmentChoices, custom_actions: object | None
) -> None: ...
"""

    assert py == aspect_result


def test_generate_functions_and_model_from_yaml(tmp_path) -> None:
    models_file = tmp_path / "models.py"
    functions_file = tmp_path / "functions.py"
    source = Path("./test.yaml")
    app_name = "Fake"

    assert not models_file.exists() and not functions_file.exists()

    pure_python(source, models_file, functions_file, app_name)

    assert models_file.exists() and functions_file.exists()


## FASTAPI


def test_generate_fastapi_models() -> None:
    source: Path = Path("./test_models.yaml")
    source_content = load_yaml(source)
    component_schemas = get_component_schemas(source_content) or {}

    generator = Generator.fastapi_generator()
    generator.component_schemas = component_schemas
    generator.generate_models_ast()

    model = generator.models_ast
    py = generate_code_from_ast(model)

    aspect_result = """from __future__ import annotations

from fastapi import FastAPI


class TaskAttachment(BaseModel):
    name: str
    kind: str


class UserTaxDeclarationInfo(BaseModel):
    utd_id: int | None
    full_environment: bool


class Mida4TaskEnvironmentChoices(BaseModel):
    pass


class FooBar(BaseModel):
    env: str | None
    baz: UserTaxDeclarationInfo | list[bool] | int
    foo: str | object
"""

    assert py == aspect_result


def test_generate_endpoints() -> None:
    source = Path("./test_functions.yaml")
    app_name = "Fake"
    generator = Generator.fastapi_generator()

    generator.load_asyncapi_content(source)
    generator.generate_function_ast(app_name)
    py = generate_code_from_ast(generator.functions_ast)

    aspect_result = """\"\"\"Test API description\"\"\"

from __future__ import annotations

import logging

from fastapi import FastAPI

app = FastAPI()
logger = logging.getLogger("Fake")


@app.get("/get_attachments_from_utd")
def get_attachments_from_utd(utd_id: int | str | TaskAttachment, kinds: list[str]) -> list[TaskAttachment]: ...


@app.get("/generate_sync_task")
def generate_sync_task(
    utd_info: UserTaxDeclarationInfo, sequence: int | None, skip_create_f24s: bool
) -> int | None: ...


@app.get("/generate_iiacc_task")
def generate_iiacc_task(
    utd_info: UserTaxDeclarationInfo, fiscal_elements: list[object] | None
) -> int | str | TaskAttachment | None: ...


@app.get("/generate_iva_sync_task")
def generate_iva_sync_task(
    user_id: int, ref_year: int, environment: Mida4TaskEnvironmentChoices, custom_actions: object | None
) -> None: ...
"""
    assert py == aspect_result


def test_generate_fastapi_from_yaml(tmp_path) -> None:
    models_file = tmp_path / "models.py"
    functions_file = tmp_path / "functions.py"
    source = Path("./test.yaml")
    app_name = "Fake"

    assert not models_file.exists() and not functions_file.exists()

    fastapi(source, models_file, functions_file, app_name)

    assert models_file.exists() and functions_file.exists()
