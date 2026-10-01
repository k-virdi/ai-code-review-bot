.PHONY: install dev ingest run api ui test lint fmt clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"
	pre-commit install || true

ingest:
	python scripts/ingest.py

run:
	python -m python_review_bot.cli.main review examples/buggy/example_sort_users.py --intent "Return users sorted by signup_date ascending"

api:
	uvicorn python_review_bot.api.main:app --reload --port 8000

ui:
	streamlit run streamlit_app.py

test:
	pytest -q

lint:
	ruff check src tests
	mypy src || true

fmt:
	ruff check --fix src tests
	ruff format src tests

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .chroma dist build *.egg-info
