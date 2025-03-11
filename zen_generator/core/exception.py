from __future__ import annotations

from pathlib import Path


class ZenException(Exception):
    pass


class InvalidFile(ZenException):
    def __init__(self, message: str, file_path: Path) -> None:
        """Constructor of InvalidFile exception.

        Args:
            message: Human readable string describing the exception.
            file_path: The path of the invalid file.
        """
        self.message = message
        self.file_path = file_path

    pass
