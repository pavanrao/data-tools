.PHONY: help sync lint test demo demo-reconcile demo-compare demo-ask \
        demo-chunking chunking-benchmark chunking-correlate \
        chunking-correlate-structured chunking-axes chunking-models \
        demo-slopify clean

help:
	@echo "sync   install the whole collection in a dev venv"
	@echo "lint   ruff check + format --check"
	@echo "test   run every tool's tests"
	@echo "demo   reconcile the hostile corpus, compare to a naive extractor, then ask"
	@echo "demo-chunking       screen chunking strategies with no model and no questions"
	@echo "chunking-benchmark  reproduce Chroma's published Precision Omega column"
	@echo "chunking-correlate  do query-free signals predict the measured ranking?"
	@echo "chunking-correlate-structured  the same, on documents with tables and code"
	@echo "chunking-axes       is the chunker the big knob, or the retriever?"
	@echo "chunking-models     which local model annotates best? (needs ollama)"
	@echo "demo-slopify        inject habits into YOUR draft, then look for them again"

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

# Query-free screening: no questions, no ground truth, no model. Runs anywhere.
demo-chunking:
	uv run python tools/chunking-lab/corpus/generate.py tools/chunking-lab/corpus/hostile
	@echo
	uv run chunking-lab metrics tools/chunking-lab/README.md \
	    --strategy fixed:800/400 --strategy fixed:400 \
	    --strategy recursive:400/200 --strategy recursive:200 \
	    --strategy structural --strategy sentence:4

# The correctness proof for the headline metric (chunking-lab C17): our
# Precision Omega against the column Chroma published. Needs the benchmark
# fetched once and the `benchmark` extra for the tokenizer; no key, no network
# after the fetch, no model.
chunking-benchmark:
	uv run python tools/chunking-lab/benchmarks/fetch.py
	uv run pytest tools/chunking-lab/tests/test_reproduction.py -v

# The section 9 experiment: score a grid over all five corpora, then ask whether
# the model-free intrinsic signals would have ranked them the same way. ~100s,
# no model, no key, no network beyond the one-time benchmark fetch.
CHUNKING_RESULTS ?= chunking-results.jsonl
chunking-correlate:
	uv run python tools/chunking-lab/benchmarks/fetch.py
	rm -f $(CHUNKING_RESULTS)
	uv run chunking-lab score --out $(CHUNKING_RESULTS) \
	    --strategy fixed:800/400 --strategy fixed:800 --strategy fixed:400/200 \
	    --strategy fixed:400 --strategy fixed:200 \
	    --strategy recursive:800/400 --strategy recursive:400/200 \
	    --strategy recursive:400 --strategy recursive:200 \
	    --strategy sentence:2 --strategy sentence:4 \
	    --strategy structural --strategy structural:1200 --strategy sentence-window:1
	@echo
	uv run chunking-lab correlate $(CHUNKING_RESULTS)
	@echo
	uv run chunking-lab correlate $(CHUNKING_RESULTS) --against iou

# The same experiment on documentation-shaped text. The Chroma corpora contain no
# Markdown tables and no code fences, so mid_table_rate and split_fence_rate are
# constant there -- untested rather than uninformative. This corpus has both, with
# gold spans known by construction, so those two signals finally get measured.
STRUCTURED_DIR ?= tools/chunking-lab/corpus/structured
STRUCTURED_RESULTS ?= chunking-structured-results.jsonl
chunking-correlate-structured:
	uv run python tools/chunking-lab/corpus/generate_docs.py $(STRUCTURED_DIR)
	rm -f $(STRUCTURED_RESULTS)
	uv run chunking-lab score --corpus-dir $(STRUCTURED_DIR) --out $(STRUCTURED_RESULTS) \
	    --by-question-type \
	    --strategy fixed:800/400 --strategy fixed:800 --strategy fixed:400/200 \
	    --strategy fixed:400 --strategy fixed:200 \
	    --strategy recursive:800/400 --strategy recursive:400/200 \
	    --strategy recursive:400 --strategy recursive:200 \
	    --strategy sentence:2 --strategy sentence:4 \
	    --strategy structural --strategy structural:1200 --strategy sentence-window:1
	@echo
	uv run chunking-lab correlate $(STRUCTURED_RESULTS)
	@echo
	uv run chunking-lab correlate $(STRUCTURED_RESULTS) --against iou

# Which knob matters more? Each axis is measured with the other held fixed, then
# compared by the ratio between best and worst -- moving both at once would measure
# neither. Needs a real encoder to be worth quoting: EMBEDDER defaults to the local
# Ollama model the shared config already defaults to.
#
#   make chunking-axes                                  # local Ollama
#   make chunking-axes EMBEDDER=ollama/qwen3-embedding  # a different local model
#   make chunking-axes EMBEDDER=openai/text-embedding-3-small  # hosted
#
# `hashing` runs with nothing installed but is a bag of words; the tool prints a
# warning and you should not quote the result.
EMBEDDER ?= ollama/nomic-embed-text
AXES_DIR ?= tools/chunking-lab/corpus/structured
AXES_RESULTS ?= chunking-axes-results.jsonl
AXES_STRATEGIES ?= --strategy recursive:200 --strategy recursive:400 \
                   --strategy structural --strategy sentence:2 --strategy fixed:800/400
chunking-axes:
	uv run python tools/chunking-lab/corpus/generate_docs.py $(AXES_DIR)
	rm -f $(AXES_RESULTS)
	uv run chunking-lab score --corpus-dir $(AXES_DIR) --out $(AXES_RESULTS) \
	    --retriever bm25 $(AXES_STRATEGIES)
	uv run chunking-lab score --corpus-dir $(AXES_DIR) --out $(AXES_RESULTS) \
	    --retriever vector --embedder $(EMBEDDER) $(AXES_STRATEGIES)
	uv run chunking-lab score --corpus-dir $(AXES_DIR) --out $(AXES_RESULTS) \
	    --retriever hybrid --embedder $(EMBEDDER) $(AXES_STRATEGIES)
	@echo
	uv run chunking-lab axes $(AXES_RESULTS)

# Which model should you annotate with? Every model sees the SAME windows -- same
# documents, same seed -- so a yield difference is the model and not luck. Writes
# nothing: it answers "which model", after which you run the real pass with the
# winner. Override MODELS with whatever you have pulled.
#
#   make chunking-models
#   make chunking-models MODELS="--model ollama/qwen2.5:14b --model ollama/phi4"
MODEL_DOCS ?= CONVENTIONS.md docs/000_project-organization.md \
              docs/007_chunking-concepts.md tools/chunking-lab/README.md
MODELS ?= --model ollama/llama3.1 --model ollama/qwen2.5:7b --model ollama/qwen2.5:14b
chunking-models:
	@rm -rf .model-compare && mkdir -p .model-compare/docs
	@cp $(MODEL_DOCS) .model-compare/docs/
	uv run chunking-lab annotate .model-compare/docs --out .model-compare/unused \
	    --per-document 5 --seed 42 $(MODELS)
	@rm -rf .model-compare

# Ground truth with no labeller in it: inject habits at known positions, then run
# the model-free linter over the result.
#
#   make demo-slopify SLOPIFY_DRAFT=path/to/your-own-writing.md
#
# The draft has to be prose no model wrote -- your own older writing, or something
# public domain. Injecting into an AI-drafted file measures habits on top of habits
# and the labels stop saying which is which, so there is no default and no sample
# shipped: see docs/014 section 2.
SLOPIFY_DRAFT ?=
demo-slopify:
	@test -n "$(SLOPIFY_DRAFT)" || { \
	    echo "set SLOPIFY_DRAFT to a Markdown draft that no model wrote:"; \
	    echo "  make demo-slopify SLOPIFY_DRAFT=path/to/draft.md"; exit 2; }
	@test -f "$(SLOPIFY_DRAFT)" || { echo "no such file: $(SLOPIFY_DRAFT)"; exit 2; }
	@rm -rf .slopify && mkdir -p .slopify
	uv run slopify inject $(SLOPIFY_DRAFT) --seed 42 --count 8 \
	    --out .slopify/slopped.md --labels .slopify/labels.jsonl
	@echo "\n=== what was injected, and where ===\n"
	@cat .slopify/labels.jsonl
	@echo "\n=== what the model-free linter finds ===\n"
	uv run ai-sniffer check .slopify/slopped.md

clean:
	rm -rf .slopify tools/ingest-ledger/corpus/hostile tools/ingest-ledger/corpus/rfp \
	       tools/chunking-lab/corpus/hostile tools/chunking-lab/corpus/structured \
	       chunking-results.jsonl chunking-structured-results.jsonl \
	       chunking-axes-results.jsonl .model-compare \
	       *.ledger.db .pytest_cache .ruff_cache
