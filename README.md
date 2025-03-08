# Zen Generator

Zen Generator is a powerful CLI tool that improves the developer experience in creating and maintaining API functions and documentation. It provides bidirectional conversion between AsyncAPI specifications and Python code, with support for both pure Python and FastAPI implementations.

## Features

- Generate AsyncAPI documentation (v3.0.0) from Python source files:
  - Convert `functions.py` (containing functions) and `models.py` (containing models) into AsyncAPI specs
  - Full support for complex Python types and None handling

- Generate Python code from AsyncAPI documentation:
  - Create `functions.py` with function signatures
  - Create `models.py` with necessary model definitions
  - Automatic type conversion and imports management

- FastAPI Integration:
  - Generate `models.py` with Pydantic models
  - Generate `endpoints.py` with FastAPI route handlers
  - Full support for async/sync operations

**Regarding the `asyncapi v.3.0.0` standard, I used the `format=required` parameter in the response `payload` of a
function to correctly handle the `None` case, as it is possible to have more than one "object" as a function response**,
example

```python
def func_bar(foo: int) -> int | str | InterfaceBaz | None:
    ...
```

## Installation

```bash
pip install zen-generator
```

## Command Line Usage

Zen Generator provides a CLI with several commands. To see all available commands:

```bash
zen-generator --help
```

For help with a specific command:

```bash
zen-generator <command> --help
```

### 1. Generate AsyncAPI Documentation

Create AsyncAPI documentation from your Python files:

```bash
zen-generator asyncapi-documentation \
    --models-file models.py \
    --functions-file functions.py \
    --output-file asyncapi.yaml \
    --application-name "My App"
```

Options:
- `--models-file`: Path to your models file (default: models.py)
- `--functions-file`: Path to your functions file (default: functions.py)
- `--output-file`: Output path for AsyncAPI spec (default: asyncapi.yaml)
- `--application-name`: Name of your application (default: "Zen")

### 2. Generate Python Code

Create Python files from AsyncAPI documentation:

```bash
zen-generator pure-python \
    --asyncapi-file asyncapi.yaml \
    --models-file models.py \
    --functions-file functions.py \
    --application-name "My App" \
    --is-async
```

Options:
- `--asyncapi-file`: Path to AsyncAPI spec (default: asyncapi.yaml)
- `--models-file`: Output path for models (default: models.py)
- `--functions-file`: Output path for functions (default: functions.py)
- `--application-name`: Name of your application (default: "Zen")
- `--is-async`: Generate async code (default: false)
```

### 3. Generate FastAPI Code

Create FastAPI endpoints and models from AsyncAPI documentation:

```bash
zen-generator fastapi \
    --asyncapi-file asyncapi.yaml \
    --models-file models.py \
    --functions-file functions.py \
    --application-name "My App" \
    --is-async
```

Options:
- `--asyncapi-file`: Path to AsyncAPI spec (default: asyncapi.yaml)
- `--models-file`: Output path for models (default: models.py)
- `--functions-file`: Output path for functions (default: functions.py)
- `--application-name`: Name of your application (default: "Zen")
- `--is-async`: Generate async code (default: false)

## Type Handling

Zen Generator provides robust support for Python type annotations and their conversion to AsyncAPI schemas:

- Full support for basic Python types (int, str, bool, etc.)
- Support for complex types (Union, Optional, List, Dict)
- Proper handling of None/Optional types using AsyncAPI's format=required parameter
- Support for custom classes and TypedDict
- Automatic conversion of Python type hints to AsyncAPI schemas and vice versa

## Examples

Here's a complete example demonstrating the bidirectional conversion between Python code and AsyncAPI specification:

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
from .models import TaskBar, FooBar

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
    "
```

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

MIT License

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
