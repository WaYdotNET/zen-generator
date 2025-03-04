from __future__ import annotations

from pathlib import Path

from rich import print


def generate_asyncapi(models_file: Path, functions_file: Path, output_file: Path, application_name: str) -> None:
    print(models_file, functions_file, output_file, application_name)
