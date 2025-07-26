# Scratchpad for Python 3.11 Project Scaffold Documentation

## Step 1: Python Packaging User Guide (https://packaging.python.org/en/latest/tutorials/packaging-projects/)

- Use a `src/` layout: place your package code in `src/your_package/`.
- Always include an empty `__init__.py` in your package directory.
- Project root should contain:
  - `pyproject.toml` (with [project] table per PEP 621)
  - `README.md`
  - `LICENSE`
  - `src/` (with your package)
  - `tests/` (for test code)
- Use a unique, memorable package name.
- Use a build backend that supports PEP 621 (e.g., hatchling, setuptools, flit, pdm).
- Use a virtual environment for development (`.venv` is a common name, not checked into VCS).
- Use `python3 -m build` or a tool like `uv` to build the project.
- Use `twine` to upload to PyPI/TestPyPI.
- Do not include `.venv` or build artifacts in version control.
- Include a license file and reference it in `pyproject.toml`.
- Use `pyproject.toml` for all project metadata and dependencies.

## Step 2: venv Best Practices (Python 3.11)

- Use `python -m venv .venv` in your project root to create a virtual environment named `.venv`.
- `.venv` should not be checked into version control (add to `.gitignore`).
- Activate the environment:
  - On macOS/Linux: `source .venv/bin/activate`
  - On Windows: `.venv\Scripts\activate.bat` (cmd) or `.venv\Scripts\Activate.ps1` (PowerShell)
- Always install project dependencies inside the virtual environment.
- The virtual environment is disposable: recreate it if broken or moved.
- Do not place project code inside `.venv`.
- Use `deactivate` to exit the environment.
- Use requirements files or `pyproject.toml` to record dependencies, not the environment itself.

## Step 3: uv Build Tool Best Practices

- Install `uv` via the standalone installer or with `pip install uv`.
- Use `uv init <project>` to initialize a new project (creates `.venv`, `pyproject.toml`, etc.).
- Use `uv add <package>` to add dependencies (updates lockfile and installs in `.venv`).
- Use `uv venv` to create or recreate the `.venv` environment.
- Use `uv pip sync` to install all dependencies from the lockfile.
- Use `uv run <command>` to run commands inside the environment.
- Use `uv lock` to update the lockfile after changing dependencies.
- Use `uv build` to build the project (if supported by your backend).
- Use `uv publish` to publish to PyPI (if needed).
- `uv` supports PEP 621 metadata in `pyproject.toml`.
- Prefer `uv` for all dependency, environment, and build management for speed and reproducibility.

## Step 4: PEP 621 Project Metadata in pyproject.toml

- Use a `[project]` table in `pyproject.toml` for all core metadata.
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
- Reference: https://peps.python.org/pep-0621/

## Next: Step 5 ...
