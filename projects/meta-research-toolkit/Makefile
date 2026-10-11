.PHONY: install test test-py test-ts coverage lint build clean

install:
	pip install -r requirements.txt
	bun install

test: test-py test-ts

test-py:
	pytest tests/python -v --cov=src/python --cov-report=html --cov-report=term

test-ts:
	bun test

coverage: test-py
	@echo "HTML coverage report: coverage/html/index.html"

lint:
	ruff check src/python
	bunx tsc --noEmit

build:
	bun run build

clean:
	rm -rf dist/ coverage/ .pytest_cache/ .mypy_cache/ node_modules/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
