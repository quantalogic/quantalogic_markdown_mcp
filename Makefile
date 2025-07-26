# User-friendly Makefile for Python project

.PHONY: help setup install lint test run clean

# Default target: show help
help:
	@echo "Available targets:"
	@echo "  setup   - Set up virtual environment and install dependencies (pip, uv, or poetry)"
	@echo "  install - Install the package in editable mode (pip install -e .)"
	@echo "  lint    - Run code linting (ruff or flake8)"
	@echo "  test    - Run tests with pytest"
	@echo "  run     - Run the main application (main.py)"
	@echo "  clean   - Remove build, dist, and cache files"

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
