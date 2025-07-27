# User-friendly Makefile for Python project

.PHONY: help setup install lint test run clean build check-build publish-test publish

# Default target: show help
help:
	@echo "Available targets:"
	@echo "  setup        - Set up virtual environment and install dependencies (pip, uv, or poetry)"
	@echo "  install      - Install the package in editable mode (pip install -e .)"
	@echo "  lint         - Run code linting (ruff or flake8)"
	@echo "  test         - Run tests with pytest"
	@echo "  run          - Run the main application (main.py)"
	@echo "  clean        - Remove build, dist, and cache files"
	@echo "  build        - Build distribution packages (wheel and source)"
	@echo "  check-build  - Validate built packages with twine"
	@echo "  publish-test - Publish to TestPyPI (requires TestPyPI API token)"
	@echo "  publish      - Publish to production PyPI (requires PyPI API token)"

setup:
	@echo "Setting up virtual environment and installing dependencies..."
	@if [ -f uv.lock ]; then \
		pip install uv && uv sync; \
	elif [ -f requirements.txt ]; then \
		python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt; \
	elif [ -f pyproject.toml ]; then \
		pip install .; \
	else \
		echo "No requirements found!"; exit 1; \
	fi

install:
	@echo "Installing package in editable mode..."
	pip install -e .

lint:
	@echo "Running linter (ruff preferred, fallback to flake8)..."
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check src/ tests/; \
	elif command -v flake8 >/dev/null 2>&1; then \
		flake8 src/ tests/; \
	else \
		echo "No linter found. Install ruff or flake8."; exit 1; \
	fi

test:
	@echo "Running tests with pytest..."
	pytest

run:
	@echo "Running main.py..."
	python3 quantalogic-markdown-edit-mcp/main.py

clean:
	@echo "Cleaning build, dist, and cache files..."
	rm -rf build/ dist/ *.egg-info __pycache__ .pytest_cache .mypy_cache .venv
	find . -type d -name '__pycache__' -exec rm -rf {} +

build: clean
	@echo "Building distribution packages..."
	uv run python -m build
	@echo "Distribution packages built in dist/"

check-build: build
	@echo "Validating built packages..."
	uv run twine check dist/*
	@echo "Package validation complete ✓"

publish-test: check-build
	@echo "Publishing to TestPyPI..."
	@echo "Make sure you have a TestPyPI API token ready."
	@echo "Username should be: __token__"
	@echo "Password should be: your TestPyPI API token (including pypi- prefix)"
	uv run twine upload --repository testpypi dist/*
	@echo "Published to TestPyPI ✓"
	@echo "Test installation with: pip install --index-url https://test.pypi.org/simple/ quantalogic-markdown-mcp"

publish: check-build
	@echo "Publishing to production PyPI..."
	@echo "⚠️  WARNING: This will publish to production PyPI!"
	@echo "Make sure you have a PyPI API token ready."
	@echo "Username should be: __token__"
	@echo "Password should be: your PyPI API token (including pypi- prefix)"
	@read -p "Are you sure you want to publish to production PyPI? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	uv run twine upload dist/*
	@echo "Published to PyPI ✓"
	@echo "Install with: pip install quantalogic-markdown-mcp"
