# quantalogic-markdown-edit-mcp

A modern Python 3.11 project scaffolded with best practices: PEP 621, uv, Pyright, isort, pytest, and more.

## Features
- Fast, reproducible dependency management with [uv](https://docs.astral.sh/uv/)
- PEP 621-compliant metadata in `pyproject.toml`
- Type checking with [Pyright](https://github.com/microsoft/pyright)
- Import sorting with [isort](https://pycqa.github.io/isort/)
- Testing with [pytest](https://docs.pytest.org/en/stable/)

## Project Structure
```
project-root/
├── .venv/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── your_package/
│       ├── __init__.py
│       └── ...
├── tests/
└── ...
```

## Getting Started
1. Clone the repo
2. Run `uv venv` to create the environment
3. Run `uv pip sync` to install dependencies
4. Run `pytest`, `isort .`, or `pyright` as needed

---
See `pyproject.toml` and the project scaffold spec for details.
