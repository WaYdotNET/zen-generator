from pathlib import Path
from zen_generator.generators.asyncapi import generate_asyncapi_from_files, create_async_api_content


def test_create_async_api_content() -> None:
    content = {"asyncapi": "2.0.0", "info": {"title": "Test API", "version": "1.0.0"}}
    models_schema = {"TestModel": {"type": "object", "properties": {"id": {"type": "integer"}}}}
    functions_docstring = "This is a test function."
    functions_parsed = {
        "test_function": {"description": "A test function", "request": {"payload": {}}, "response": {"payload": {}}}
    }
    output = create_async_api_content("Test API", models_schema, functions_docstring, functions_parsed)
    assert output is not None
    assert "asyncapi" in output
    assert output["info"]["title"] == "Test API"


def test_generate_asyncapi_from_files(tmp_path) -> None:
    models_file = Path("models.py")
    functions_file = Path("functions.py")
    output_file = tmp_path / "output_path.yaml"
    app_name = "TestApp"
    assert not output_file.exists()
    generate_asyncapi_from_files(models_file, functions_file, output_file, app_name)
    assert output_file.exists()
    with output_file.open() as f:
        content = f.read()

    # check that the content contains the expected functions and models
    assert "get_attachments_from_utd" in content
    assert "empty" in content
    assert "generate_sync_task" in content
    assert "generate_iiacc_task" in content
    assert "generate_iva_sync_task" in content
    assert "Descrizione metodo get_attachments_from_utd" in content

    assert "TaskAttachment" in content
    assert "UserTaxDeclarationInfo" in content
    assert "Mida4TaskEnvironmentChoices" in content
