from __future__ import annotations

from _ast import (
    Assign,
    Attribute,
    BinOp,
    BitOr,
    Call,
    Constant,
    Expr,
    FunctionDef,
    ImportFrom,
    Load,
    Module,
    Name,
    Store,
    Subscript,
    alias,
    arg,
    arguments,
)

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class TaskAttachment(BaseModel):
    name: str
    kind: str


class UserTaxDeclarationInfo(BaseModel):
    utd_id: int | None
    full_environment: bool


class Mida4TaskEnvironmentChoices(BaseModel):
    pass


class FooBar(BaseModel):
    env: str | None
    baz: UserTaxDeclarationInfo | list[bool] | int
    foo: str | object


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/get_attachments_from_utd")
def get_attachments_from_utd(
    utd_id: int | str | TaskAttachment, kinds: list[str], other: int | FooBar | None
) -> list[TaskAttachment]: ...


Module(
    body=[
        ImportFrom(module="__future__", names=[alias(name="annotations")], level=0),
        ImportFrom(module="fastapi", names=[alias(name="FastAPI")], level=0),
        Assign(
            targets=[Name(id="app", ctx=Store())],
            value=Call(func=Name(id="FastAPI", ctx=Load()), args=[], keywords=[]),
        ),
        FunctionDef(
            name="get_attachments_from_utd",
            args=arguments(
                posonlyargs=[],
                args=[
                    arg(
                        arg="utd_id",
                        annotation=BinOp(
                            left=BinOp(
                                left=Name(id="int", ctx=Load()),
                                op=BitOr(),
                                right=Name(id="str", ctx=Load()),
                            ),
                            op=BitOr(),
                            right=Name(id="TaskAttachment", ctx=Load()),
                        ),
                    ),
                    arg(
                        arg="kinds",
                        annotation=Subscript(
                            value=Name(id="list", ctx=Load()),
                            slice=Name(id="str", ctx=Load()),
                            ctx=Load(),
                        ),
                    ),
                    arg(
                        arg="other",
                        annotation=BinOp(
                            left=BinOp(
                                left=Name(id="int", ctx=Load()),
                                op=BitOr(),
                                right=Name(id="FooBar", ctx=Load()),
                            ),
                            op=BitOr(),
                            right=Constant(value=None),
                        ),
                    ),
                ],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=[Expr(value=Constant(value=Ellipsis))],
            decorator_list=[
                Call(
                    func=Attribute(value=Name(id="app", ctx=Load()), attr="get", ctx=Load()),
                    args=[Constant(value="/get_attachments_from_utd")],
                    keywords=[],
                )
            ],
            returns=Subscript(
                value=Name(id="list", ctx=Load()),
                slice=Name(id="TaskAttachment", ctx=Load()),
                ctx=Load(),
            ),
        ),
    ],
    type_ignores=[],
)
