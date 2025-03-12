from __future__ import annotations

from pathlib import Path

import typer
from rich import print
from typing_extensions import Annotated

from zen_generator.generators.asyncapi import generate_asyncapi_from_files
from zen_generator.generators.python import Generator

app = typer.Typer()


@app.command()
def asyncapi_documentation(
    models_file: Annotated[Path, typer.Option()] = Path("models.py"),
    functions_file: Annotated[Path, typer.Option()] = Path("functions.py"),
    output_file: Annotated[Path, typer.Option()] = Path("asyncapi.yaml"),
    application_name: Annotated[str, typer.Option()] = "Zen",
) -> None:
    """Generate AsyncAPI documentation from source code.

    Generate the AsyncAPI documentation from the source code in the models_file
    and functions_file. The output will be a yaml file saved in the output_file
    with the name of the application as title.

    Args:
        models_file: The path to the file containing the models.
        functions_file: The path to the file containing the functions.
        output_file: The path to the output file.
        application_name: The name of the application.
    """
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
) -> None:
    """Generate pure Python models and functions from AsyncAPI file.

    Generate the models and functions from the AsyncAPI file in the asyncapi_file.
    The output will be two files, one for the models and one for the functions,
    saved in the models_file and functions_file respectively.

    Args:
        asyncapi_file: The path to the AsyncAPI file.
        models_file: The path to the output file for the models.
        functions_file: The path to the output file for the functions.
        application_name: The name of the application.
        is_async: Whether the generated functions should be async or not.
    """
    print("Preparing to generate models and functions from the asyncapi file")
    if asyncapi_file.is_file():
        generator = Generator.pure_python_generator()
        generator.generate_files_from_asyncapi(asyncapi_file, models_file, functions_file, application_name, is_async)
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
) -> None:
    """Generate FastAPI models and functions from AsyncAPI file.

    Generate the models and functions from the AsyncAPI file in the asyncapi_file.
    The output will be two files, one for the models and one for the functions,
    saved in the models_file and functions_file respectively.

    Args:
        asyncapi_file: The path to the AsyncAPI file.
        models_file: The path to the output file for the models.
        functions_file: The path to the output file for the functions.
        application_name: The name of the application.
        is_async: Whether the generated functions should be async or not.

    """
    print("Preparing to generate models and functions from the asyncapi file")
    if asyncapi_file.is_file():
        generator = Generator.fastapi_generator()
        generator.generate_files_from_asyncapi(asyncapi_file, models_file, functions_file, application_name, is_async)
    else:
        print(
            f":boom: :boom: [bold red]the source file '{asyncapi_file}' "
            f"or the file '{functions_file}' is not a file![/bold red]"
        )
        raise typer.Abort()


@app.callback()
def main() -> None:
    print("Welcome to the zen generator")
    app()


if __name__ == "__main__":
    app()
