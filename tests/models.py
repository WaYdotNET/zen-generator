from __future__ import annotations

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
