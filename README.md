# Zen Generator

This tool aims to improve the developer experience in creating current proxies, with its two (currently) simple
features:

- generate documentation (using the [asyncapi v.3.0.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0)
  standard) starting from the `proxy.py` file (containing the functions) and `interfaces.py` file (containing any
  interfaces necessary for the proxies themselves)
- generate the `proxy.py` file (containing only the function signatures) and `interfaces.py` file (containing any
  interfaces necessary for the proxies themselves, excluding the necessary imports)

- [FastApi] generate the `models.py` file (containing only the function signatures) and `endpoints.py` file (containing
  the necessary models for the `Fastapi` endpoints themselves, excluding the necessary imports)

**Regarding the `asyncapi v.3.0.0` standard, I used the `format=required` parameter in the response `payload` of a
function to correctly handle the `None` case, as it is possible to have more than one "object" as a function response**,
example

```python
def func_bar(foo: int) -> int | str | InterfaceBaz | None:
    ...
```

## Available Commands

To get a list of all available commands, use the helper

```shell
zen-generator  --help
```

The helper is also available for each individual command, example:

```shell
zen-generator generate-doc --help
```

### Generating documentation from python files

To generate the documentation file from the `proxy.py` and `interfaces.py` files, use the following command:

```shell
zen-generator generate-doc --source-interface my_app/interfaces.py --source-proxy my_app/proxy.py --destination foo/myapp_doc.yml --app-name my_app
```

### Generating `proxy.py` and `interfaces.py` files from `asyncapi` documentation

To generate the `proxy.py` and `interfaces.py` files from the `asyncapi` documentation file, use the following command:

```shell
zen-generator proxy-with-interface --source myapp_doc.yaml --destination foo/ --app-name foo
```

It is also possible to create only the `proxy.py` or `interfaces.py` file with the respective commands

```shell
zen-generator proxy --source foo/myapp_doc.yaml --destination baz/ --app-name foo
```

```shell
zen-generator interface --source myapp_doc.yaml --destination my_app_foo_bar/
```

### [FastApi] Generating `models.py` and `endpoints.py` files from `asyncapi` documentation

To generate the `models.py` and `endpoints.py` files from the `asyncapi` documentation file, use the following command:

```shell
zen-generator generate-fastapi --source tests/test.yaml --destination tests/output --app-name foo
```

## Examples

A small example of the current output (either starting from an asyncapi file and generating python files or vice versa)

my_app.yaml

```yaml
---
asyncapi: 3.0.0
info:
  title: Oh My App
  version: 0.0.1
  description: 'some docstring

    very nice app!!'
channels:
  foo:
    $ref: '#/components/channels/foo'
operations:
  foo:
    $ref: '#/components/operations/foo'
components:
  channels:
    foo:
      messages:
        request:
          $ref: '#/components/messages/foo_request'
        response:
          $ref: '#/components/messages/foo_response'
  operations:
    foo:
      action: receive
      description: "\n    Description of method foo\n    Args:\n\
        \        bar (): bar something\n        kinds (): types of params\n\
        \        other (): other\n\n    Returns:\n        I don't know what it returns\n\
        \    "
      channel:
        $ref: '#/channels/foo'
      messages:
        - $ref: '#/channels/foo/messages/request'
      reply:
        channel:
          $ref: '#/channels/foo'
        messages:
          - $ref: '#/channels/foo/messages/response'
  messages:
    foo_request:
      title: Request params for foo
      summary: ''
      description: ''
      payload:
        type: object
        required:
          - bar
          - kinds
        properties:
          bar:
            oneOf:
              - type: integer
              - type: string
              - $ref: '#/components/schemas/TaskBar'
            description: bar is something
          kinds:
            type: array
            items:
              type: string
            description: types of params
          other:
            oneOf:
              - type: integer
              - $ref: '#/components/schemas/FooBar'
            description: other
    foo_response:
      title: Request params for foo
      summary: ''
      description: I don't know what it returns
      payload:
        type: array
        items:
          $ref: '#/components/schemas/FooBar'
  schemas:
    TaskBar:
      type: object
      base_class: Choices
      required: [ ]
      properties: { }
    FooBar:
      type: object
      base_class: TypedDict
      required:
        - baz
        - foo
      properties:
        env:
          type: string
        baz:
          oneOf:
            - $ref: '#/components/schemas/FooBar'
            - type: array
              items:
                type: boolean
            - type: integer
        foo:
          oneOf:
            - type: string
            - type: object
```

proxy.py

```python
"""some docstring
very nice app!!"""
from __future__ import annotations
import logging
from .interfaces import TaskBar, FooBar

logger = logging.getLogger("foo")


def foo(
        bar: int | str | TaskBar, kinds: list[str], other: int | FooBar | None
) -> list[FooBar] | None:
    """
    Description of method foo
    Args:
        bar (): bar something
        kinds (): types of params
        other (): other

    Returns:
        I don't know what it returns
    """
    ...
```

interfaces.py

```python
from __future__ import annotations
from typing import TypedDict
from utils.enums import Choices


class TaskBar(Choices):
    pass


class FooBar(TypedDict):
    env: str | None
    baz: FooBar | list[bool] | int
    foo: str | object
```
