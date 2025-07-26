# Python 3.11 Project Scaffold Specification

This document provides concise, actionable guidance for structuring a modern Python 3.11 project using `.venv`, the `uv` build tool, and PEP 621-compliant `pyproject.toml` metadata. All recommendations are based on the latest official sources.

## 1. Project Directory Structure

```
project-root/
├── .venv/                # Virtual environment (not in VCS)
├── pyproject.toml        # Project metadata (PEP 621)
├── README.md             # Project overview
├── LICENSE               # License file
├── src/
│   └── your_package/
│       ├── __init__.py
│       └── ...           # Your code modules
├── tests/                # Test suite
└── ...                   # Other files (e.g., docs, scripts)
```

- Place all source code in `src/your_package/`.
- Always include an empty `__init__.py` in your package directory.
- Keep `.venv` out of version control (add to `.gitignore`).

## 2. Virtual Environment Best Practices

- Create a virtual environment in the project root:
  - `python -m venv .venv`
- Activate with `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate.bat` (Windows).
- Install all dependencies inside the environment.
- Never place project code inside `.venv`.
- Recreate the environment if it becomes corrupted or is moved.
- Use `deactivate` to exit the environment.

## 3. Using `uv` for Dependency and Build Management

- Install `uv` via the standalone installer or `pip install uv`.
- Initialize a new project: `uv init <project>`
- Add dependencies: `uv add <package>`
- Create or recreate the environment: `uv venv`
- Sync dependencies: `uv pip sync`
- Run commands: `uv run <command>`
- Update lockfile: `uv lock`
- Build the project: `uv build`
- Publish to PyPI: `uv publish`
- Prefer `uv` for all dependency, environment, and build management for speed and reproducibility.

References:
- [uv documentation](https://docs.astral.sh/uv/)


## 4. PEP 621 Project Metadata in `pyproject.toml`

- Use a `[project]` table for all core metadata.
- The project name should be descriptive and unique, e.g. `quantalogic-markdown-edit-mcp`.
- Required fields: `name`, `version`, `description`, `readme`, `requires-python`, `license`, `authors`.
- Recommended fields: `maintainers`, `keywords`, `classifiers`, `urls`, `dependencies`, `optional-dependencies`.
- Use SPDX license identifiers or reference a license file.
- Use arrays for `authors` and `maintainers` (each with `name` and/or `email`).
- Use arrays for `keywords` and `classifiers`.
- Use `[project.urls]` for homepage, documentation, repository, etc.
- Use `[project.scripts]` and `[project.entry-points]` for CLI entry points.
- Use `dependencies` for runtime requirements (PEP 508 strings).
- Use `[project.optional-dependencies]` for extras (e.g., test, docs).
- Use `dynamic` only if a field is provided by the build backend, not statically.
- Do not add custom fields to `[project]`; use `[tool.<toolname>]` for tool-specific config.

References:
- [PEP 621](https://peps.python.org/pep-0621/)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)




## 5. Type Annotations and Static Type Checking

- Use Python type hints throughout your codebase for clarity and maintainability.
- For static type checking, use [Pyright](https://github.com/microsoft/pyright) (official, TypeScript implementation by Microsoft).
- Install with:
  - `pip install pyright`
- Run type checks with:
  - `pyright`
- Integrate Pyright into your CI or pre-commit hooks for automated checks.


## 6. Code Quality and Testing Tools

- **isort**: Automatically sort and organize imports for consistency and readability.
  - Install with: `pip install isort`
  - Run on your codebase: `isort .`
  - Optionally configure in `pyproject.toml` under `[tool.isort]`.
  - Reference: [isort documentation](https://pycqa.github.io/isort/)

- **pytest**: Use as the test runner for all tests in the `tests/` directory.
  - Install with: `pip install pytest`
  - Run tests: `pytest`
  - Optionally configure in `pyproject.toml` under `[tool.pytest.ini_options]` or use a `pytest.ini` file.
  - Reference: [pytest documentation](https://docs.pytest.org/en/stable/)


## 7. Additional Best Practices

- Include a `LICENSE` file and reference it in `pyproject.toml`.
- Do not include `.venv` or build artifacts in version control.
- Use `README.md` for project documentation.
- Place all tests in the `tests/` directory.
- Use a unique, memorable package name.
- Use `uv` as the backend for build and dependency management for speed, reproducibility, and modern workflow. Configure your `pyproject.toml` to use `uv` as the build backend.

---

For more details, see the official documentation:
- [Python Packaging User Guide](https://packaging.python.org/)
- [venv module docs](https://docs.python.org/3.11/library/venv.html)
- [uv documentation](https://docs.astral.sh/uv/)
- [PEP 621](https://peps.python.org/pep-0621/)
- [Pyright (Microsoft)](https://github.com/microsoft/pyright)
- [isort](https://pycqa.github.io/isort/)
- [pytest](https://docs.pytest.org/en/stable/)
