.PHONY: help sync lint test demo demo-reconcile demo-compare demo-ask clean

help:
	@echo "sync   install the whole collection in a dev venv"
	@echo "lint   ruff check + format --check"
	@echo "test   run every tool's tests"
	@echo "demo   reconcile the hostile corpus, compare to a naive extractor, then ask"

sync:
	uv sync --all-extras

lint:
	uv run ruff check .
	uv run ruff format --check .

test:
	uv run pytest

demo: demo-reconcile demo-compare demo-ask

demo-reconcile:
	uv run python tools/ingest-ledger/corpus/generate.py tools/ingest-ledger/corpus/hostile
	@echo
	uv run ingest-ledger report --in-process tools/ingest-ledger/corpus/hostile

demo-compare:
	@echo "\n=== the same corpus, read by an ordinary extractor ===\n"
	uv run ingest-ledger compare --in-process tools/ingest-ledger/corpus/hostile

demo-ask:
	@echo "\n=== query-time abstention ===\n"
	uv run python tools/ingest-ledger/corpus/generate.py tools/ingest-ledger/corpus/rfp --rfp
	uv run ingest-ledger index --in-process --ledger rfp.ledger.db tools/ingest-ledger/corpus/rfp
	@echo
	uv run ingest-ledger ask --ledger rfp.ledger.db "who owns the intellectual property?"
	@echo
	@# exit 3 is the refusal itself, not a failure -- see query.Verdict
	uv run ingest-ledger ask --ledger rfp.ledger.db "what are the payment schedule milestones?" || test $$? -eq 3

clean:
	rm -rf tools/ingest-ledger/corpus/hostile tools/ingest-ledger/corpus/rfp \
	       *.ledger.db .pytest_cache .ruff_cache
