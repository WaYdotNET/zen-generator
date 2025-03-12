# tests/conftest.py
from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def change_test_dir():
    os.chdir(os.path.dirname(__file__))
