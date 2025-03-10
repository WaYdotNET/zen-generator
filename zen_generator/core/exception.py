"""This module contains custom exceptions used in the zen generator.

The main entry points are:

- `InvalidFile`: Raised when a file is not valid.
"""
from __future__ import annotations

from pathlib import Path


class InvalidFile(Exception):
    """Raised when a file is not valid.

    This exception is raised when a file that is supposed to be a Python file
    or a YAML file is not valid. It is also used when the file is empty.

    Attributes:
        message: Human readable string describing the exception.
        file_path: The path of the invalid file.
    """

    def __init__(self, message: str, file_path: Path) -> None:
        """Constructor of InvalidFile exception.

        Args:
            message: Human readable string describing the exception.
            file_path: The path of the invalid file.
        """
        self.message = message
        self.file_path = file_path

    pass
