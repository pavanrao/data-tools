.PHONY: help sync lint test demo clean

help:
	@echo "sync   install the whole collection in a dev venv"
	@echo "lint   ruff check + format --check"
	@echo "test   run every tool's tests"
	@echo "demo   build the hostile corpus and reconcile it"

sync:
	uv sync --all-extras

lint:
	uv run ruff check .
	uv run ruff format --check .

test:
	uv run pytest

demo:
	uv run python tools/ingest-ledger/corpus/generate.py tools/ingest-ledger/corpus/hostile
	@echo
	uv run ingest-ledger report --in-process tools/ingest-ledger/corpus/hostile

clean:
	rm -rf tools/ingest-ledger/corpus/hostile *.ledger.db .pytest_cache .ruff_cache
