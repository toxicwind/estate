.PHONY: all test clean lint

all: test

test:
	python3 -m unittest discover -s tests -p "test_*.py" -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	python3 -c "import ruff" 2>/dev/null && ruff check . || echo "Ruff not pre-installed in environment, skipping static lint."
