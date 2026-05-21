.PHONY: install dev test lint typecheck trace clean

install:
	pip install -e ".[dev]"

dev:
	uvicorn src.web:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

test-one:
	@# Usage: make test-one T=tests/test_planner.py::test_routes_constitution
	pytest $(T) -v

cov:
	pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck:
	mypy src/

trace:
	@# Usage: make trace ID=<turn_id>
	python scripts/view_trace.py --turn-id $(ID)

reset-user:
	@# Usage: make reset-user P=+85291234567
	python scripts/reset_user.py --phone $(P)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
