.PHONY: install test lint typecheck demo
install:
	python -m pip install -e ".[dev]"
test:
	python -m pytest
lint:
	python -m ruff check .
	python -m ruff format --check .
typecheck:
	python -m mypy
demo:
	python -m repopulse scan examples/sample-project
