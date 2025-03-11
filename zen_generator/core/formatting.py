"""This module contains utilities for formatting Python code."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def format_python_code(code: str) -> str:
    """Format python code using Ruff.

    Format a given string of python code using the Ruff formatter.

    Args:
        code (str): Python code to format

    Returns:
        str: Formatted python code if successful, original code otherwise.
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as tmp:
        tmp.write(code)
        tmp_path = Path(tmp.name)

    try:
        # https://docs.astral.sh/ruff/formatter/#line-breaks
        # ruff check --select I --fix
        subprocess.run(
            ["ruff", "check", "--select", "I", "--fix", str(tmp_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # ruff format
        subprocess.run(
            ["ruff", "format", str(tmp_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        formatted_code: str = tmp_path.read_text()
        return formatted_code
    except subprocess.CalledProcessError:
        return code
    finally:
        tmp_path.unlink(missing_ok=True)
