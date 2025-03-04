from __future__ import annotations

from pathlib import Path

from core.utils import import_string
from rich import print
import typer
from typing_extensions import Annotated

app = typer.Typer()


@app.command()
def asyncapi_documentation(
    models_file: Annotated[Path, typer.Option()] = "models.py",
    functions_file: Annotated[Path, typer.Option()] = "functions.py",
    output_file: Annotated[Path, typer.Option()] = "asyncapi.yaml",
    application_name: Annotated[str, typer.Option()] = "Zen",
):
    print("Preparing to generate the documentation")
    if models_file.is_file() and functions_file.is_file():
        generate_asyncapi = import_string("pure-python.generate_asyncapi")
        generate_asyncapi(models_file, functions_file, output_file, application_name)
    else:
        print(
            f":boom: :boom: [bold red]the source file '{models_file}' "
            f"or the file '{functions_file}' is not a file![/bold red]"
        )
        raise typer.Abort()


@app.callback()
def main():
    print("Welcome to the zen generator")


if __name__ == "__main__":
    app()
