from __future__ import annotations

from pathlib import Path

import typer
from rich import print
from typing_extensions import Annotated

from zen_generator.generators.asyncapi import generate_asyncapi_from_files
from zen_generator.generators.fastapi import generate_fastapi_from_asyncapi
from zen_generator.generators.pure_python import generate_pure_python_from_asyncapi

app = typer.Typer()


@app.command()
def asyncapi_documentation(
    models_file: Annotated[Path, typer.Option()] = Path("models.py"),
    functions_file: Annotated[Path, typer.Option()] = Path("functions.py"),
    output_file: Annotated[Path, typer.Option()] = Path("asyncapi.yaml"),
    application_name: Annotated[str, typer.Option()] = "Zen",
):
    print("Preparing to generate the documentation")
    if models_file.is_file() and functions_file.is_file():
        generate_asyncapi_from_files(models_file, functions_file, output_file, application_name)
    else:
        print(
            f":boom: :boom: [bold red]the source file '{models_file}' "
            f"or the file '{functions_file}' is not a file![/bold red]"
        )
        raise typer.Abort()


@app.command()
def pure_python(
    asyncapi_file: Annotated[Path, typer.Option()] = Path("asyncapi.yaml"),
    models_file: Annotated[Path, typer.Option()] = Path("models.py"),
    functions_file: Annotated[Path, typer.Option()] = Path("functions.py"),
    application_name: Annotated[str, typer.Option()] = "Zen",
    is_async: Annotated[bool, typer.Option()] = False,
):
    print("Preparing to generate models and functions from the asyncapi file")
    if asyncapi_file.is_file():
        generate_pure_python_from_asyncapi(asyncapi_file, models_file, functions_file, application_name, is_async)
    else:
        print(
            f":boom: :boom: [bold red]the source file '{asyncapi_file}' "
            f"or the file '{functions_file}' is not a file![/bold red]"
        )
        raise typer.Abort()


@app.command()
def fastapi(
    asyncapi_file: Annotated[Path, typer.Option()] = Path("asyncapi.yaml"),
    models_file: Annotated[Path, typer.Option()] = Path("models.py"),
    functions_file: Annotated[Path, typer.Option()] = Path("functions.py"),
    application_name: Annotated[str, typer.Option()] = "Zen",
    is_async: Annotated[bool, typer.Option()] = False,
):
    print("Preparing to generate models and functions from the asyncapi file")
    if asyncapi_file.is_file():
        generate_fastapi_from_asyncapi(asyncapi_file, models_file, functions_file, application_name, is_async)
    else:
        print(
            f":boom: :boom: [bold red]the source file '{asyncapi_file}' "
            f"or the file '{functions_file}' is not a file![/bold red]"
        )
        raise typer.Abort()


@app.callback()
def main():
    print("Welcome to the zen generator")


if __name__ == "__main__":
    app()
