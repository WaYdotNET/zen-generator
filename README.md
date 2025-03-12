<img src="https://github.com/WaYdotNET/zen-generator/raw/main/zen-generator-small.png" alt="Zen Generator Logo" width="200" height="200">

# Zen Generator 🚀

A bidirectional Python code generator that converts between AsyncAPI 3.0 specifications and Python code (pure Python or FastAPI implementations).

## Features ✨

- Bidirectional conversion between [AsyncAPI 3.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0) and Python code
- Generate Python code from AsyncAPI 3.0 specifications:
  - Pure Python implementations with type hints
  - FastAPI endpoints with Pydantic models
- Generate AsyncAPI 3.0 specifications from Python code
- Automatic type inference and mapping
- Support for both async and sync functions

## Installation 📦

```bash
pip install zen-generator
```

## Quick Start 🏃

Convert between AsyncAPI 3.0 specifications and Python code:

```bash
# Generate FastAPI implementation from AsyncAPI spec
zen-generator fastapi

# Generate pure Python implementation from AsyncAPI spec  
zen-generator pure-python 

# Generate AsyncAPI spec from Python code
zen-generator asyncapi-documentation
```

### Command Line Interface

The CLI is built with Typer and provides three main commands:

**Usage**:

```console
$ [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `--install-completion`: Install completion for the current shell.
- `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
- `--help`: Show this message and exit.

**Commands**:

- `asyncapi-documentation`
- `pure-python`
- `fastapi`

## `asyncapi-documentation`

**Usage**:

```console
$ asyncapi-documentation [OPTIONS]
```

**Options**:

- `--models-file PATH`: [default: models.py]
- `--functions-file PATH`: [default: functions.py]
- `--output-file PATH`: [default: asyncapi.yaml]
- `--application-name TEXT`: [default: Zen]
- `--help`: Show this message and exit.

## `pure-python`

**Usage**:

```console
$ pure-python [OPTIONS]
```

**Options**:

- `--asyncapi-file PATH`: [default: asyncapi.yaml]
- `--models-file PATH`: [default: models.py]
- `--functions-file PATH`: [default: functions.py]
- `--application-name TEXT`: [default: Zen]
- `--is-async / --no-is-async`: [default: no-is-async]
- `--help`: Show this message and exit.

## `fastapi`

**Usage**:

```console
$ fastapi [OPTIONS]
```

**Options**:

- `--asyncapi-file PATH`: [default: asyncapi.yaml]
- `--models-file PATH`: [default: models.py]
- `--functions-file PATH`: [default: functions.py]
- `--application-name TEXT`: [default: Zen]
- `--is-async / --no-is-async`: [default: no-is-async]
- `--help`: Show this message and exit.

## Generated Code Examples 📝

### Models (models.py)

```python
from __future__ import annotations
from pydantic import BaseModel

class UserModel(BaseModel):
    id: int
    name: str
    email: str | None = None
```

### FastAPI Implementation (functions.py)

```python
from __future__ import annotations
from fastapi import FastAPI
from .models import UserModel

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: int) -> UserModel:
    ...
```

### Pure Python Implementation (functions.py)

```python
from __future__ import annotations
from typing import Optional
from .models import UserModel

def get_user(user_id: int) -> UserModel:
    ...
```

## Development Setup 🛠️

Requirements:
- Python 3.10+
- uv (Python packaging toolchain)

```bash
# Install uv if not already installed
pip install uv

# Clone repository
git clone https://github.com/WaYdotNET/zen-generator.git
cd zen-generator

# Create and activate virtual environment with uv
uv venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies with uv
uv sync

# Run tests
python -m pytest
```

## Best Practices 💡

1. **AsyncAPI Specification**
   - Follow [AsyncAPI 3.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0) guidelines
   - Define clear schema types
   - Include comprehensive examples
   - Use semantic versioning

2. **Code Generation**
   - Review generated code for correctness
   - Implement business logic in function stubs
   - Keep generated files synchronized
   - Use type hints consistently

3. **Project Organization**
   - Maintain clear separation between models and functions
   - Follow standard Python package structure
   - Implement proper error handling

## Contributing 🤝

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Submit a pull request

## License 📄

MIT License - see LICENSE file for details

## Support 💬

- GitHub Issues: [Report bugs or suggest features](https://github.com/WaYdotNET/zen-generator/issues)

---

Made with ❤️ by [WaYdotNET](https://github.com/WaYdotNET)
