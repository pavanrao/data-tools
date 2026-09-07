#!/usr/bin/env python3
"""Generate a structured documentation corpus with gold spans known by construction.

The Chroma benchmark is prose. All five of its corpora contain **zero** Markdown
tables and zero code fences -- even `finance.md`, whose ConvFinQA source tables
were flattened into sentences. So two of the intrinsic signals, `mid_table_rate`
and `split_fence_rate`, are *constant* on it: they never vary, there is nothing to
correlate, and they come out of the section 9 experiment untested rather than
uninformative.

This corpus exists to test them. Technical documentation is also a real retrieval
target in its own right, and it fails differently from prose: an answer in a table
row is meaningless without the header, and a code example cut in half is worse
than useless because it still looks like code.

**What is and is not being assumed.** The generator decides where the tables are
and where the answers are. It does **not** decide whether a chunker that shreds
tables scores worse on Precision Omega or IoU -- that relationship is measured. So
the experiment is honest, with one stated limitation: the text is synthetic, so
these numbers say how the signals behave on documentation *shaped* like this, not
how often such documents occur.

    uv run python tools/chunking-lab/corpus/generate_docs.py corpus/structured
"""

from __future__ import annotations

import sys
from pathlib import Path

from chunking_lab.corpus import Corpus, DocumentBuilder, write_dir

# --------------------------------------------------------------------- data

#: Generated rather than hand-written so the documents reach a size where chunk
#: size actually varies the number of chunks -- the Chroma corpora are 40KB to
#: 737KB, and a 2KB document gives an 800-character chunker two chunks and nothing
#: to correlate. Names are distinctive so BM25 has something to match on.
RESOURCES = [
    "documents",
    "chunks",
    "collections",
    "embeddings",
    "jobs",
    "webhooks",
    "workspaces",
    "api-keys",
    "audit-events",
    "exports",
    "imports",
    "schemas",
    "pipelines",
    "connectors",
    "retrievers",
    "rerankers",
    "evaluations",
    "datasets",
    "annotations",
    "snapshots",
    "quotas",
    "usage",
    "billing",
    "sessions",
]
VERBS = [("GET", "Lists"), ("POST", "Creates"), ("DELETE", "Removes")]
LIMITS = ["600/min", "300/min", "120/min", "60/min", "20/min", "10/min", "5/min"]
PARAMS = ["cursor", "page_size", "idempotency_key", "hard", "status", "since", "force", "secret"]

ENDPOINTS = [
    (
        f"/v1/{resource}",
        verb,
        LIMITS[(i * 3 + j) % len(LIMITS)],
        PARAMS[(i + j) % len(PARAMS)],
        f"{gerund} {resource.replace('-', ' ')} belonging to the workspace.",
    )
    for i, resource in enumerate(RESOURCES)
    for j, (verb, gerund) in enumerate(VERBS)
    if (i + j) % 2 == 0
]

SIGNALS = [
    ("queue_depth", "Ingestion is falling behind the write rate."),
    ("p99_latency_ms", "Search is degrading for interactive users."),
    ("error_rate", "Requests are failing before reaching the retriever."),
    ("index_lag_s", "Newly uploaded documents are not yet searchable."),
    ("disk_used_pct", "The index volume is approaching capacity."),
    ("cert_expiry_days", "The TLS certificate is close to expiry."),
    ("embed_queue_age_s", "Embedding workers are saturated."),
    ("dead_letter_count", "Messages are failing every delivery attempt."),
    ("shard_skew_pct", "One shard is taking a disproportionate share of traffic."),
    ("cache_hit_rate", "The embedding cache is being evicted too aggressively."),
    ("open_file_handles", "A descriptor leak is developing."),
    ("gc_pause_ms", "Garbage collection is stalling request handling."),
    ("replica_lag_s", "A read replica has fallen behind its primary."),
    ("retry_rate", "Upstream calls are failing and being retried."),
    ("oom_kills", "A worker is exceeding its memory limit."),
    ("token_spend_usd", "Model spend is above the daily budget."),
]
ALERTS = [
    (
        signal,
        str(50 * (i + 1)),
        str(200 * (i + 1)),
        "page" if i % 3 else "ticket",
        meaning,
    )
    for i, (signal, meaning) in enumerate(SIGNALS)
]

CHANGES = [
    "Adds cursor pagination to the list endpoints.",
    "Fixes a crash when a PDF has no text layer.",
    "Introduces the chunks endpoint.",
    "Removes the deprecated v0 namespace entirely.",
    "Raises the default request timeout to thirty seconds.",
    "Adds webhook delivery retries with exponential backoff.",
    "Switches the default embedding model.",
    "Adds character offsets to every search hit.",
    "Makes the reranker optional per request.",
    "Corrects the rate limit headers on 429 responses.",
    "Adds an export endpoint for annotations.",
    "Deduplicates identical chunks within a document.",
    "Reports the tokenizer used for each index.",
    "Allows overlap to be configured per collection.",
    "Fixes offsets on documents containing combining characters.",
    "Adds a dry-run mode to the import endpoint.",
    "Removes implicit retries from the client.",
    "Adds structured logging to the ingestion worker.",
    "Splits the search and rerank quotas.",
    "Fixes a leak in the connection pool.",
    "Adds per-workspace usage reporting.",
    "Makes chunk identifiers stable across reindexing.",
    "Improves the error message for an expired key.",
    "Adds a health endpoint that checks the index, not just the process.",
]
RELEASES = [
    (
        f"{4 - i // 9}.{(24 - i) % 9}.{i % 4}",
        f"2026-{((24 - i) % 12) + 1:02d}-{((i * 7) % 27) + 1:02d}",
        change,
        "yes" if i % 8 == 0 else "no",
    )
    for i, change in enumerate(CHANGES)
]


def _table(header: list[str], widths: list[int]) -> str:
    row = "| " + " | ".join(h.ljust(w) for h, w in zip(header, widths, strict=True)) + " |\n"
    rule = "|" + "|".join("-" * (w + 2) for w in widths) + "|\n"
    return row + rule


def _row(cells: list[str], widths: list[int]) -> str:
    return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, widths, strict=True)) + " |"


# ---------------------------------------------------------------- documents


def api_reference() -> Corpus:
    """Answers inside table rows and inside fenced examples."""
    w = [22, 8, 10, 18]
    d = DocumentBuilder("api_reference.md")
    d.add("# API Reference\n\nEvery endpoint is versioned and rate limited per workspace.\n\n")
    d.add("## Endpoints\n\nRate limits are per workspace, not per key.\n\n")
    d.add(_table(["path", "method", "rate limit", "key parameter"], w))
    for path, method, limit, param, _ in ENDPOINTS:
        d.answer(
            _row([path, method, limit, param], w),
            question=f"What is the rate limit for {method} {path}?",
            about="answer is a table row; useless once separated from the header",
        ).add("\n")
    d.add("\nExceeding a limit returns 429 with a Retry-After header.\n\n")

    d.add("## Descriptions\n\n")
    for path, method, _, _, description in ENDPOINTS:
        d.add(f"### {method} {path}\n\n").answer(
            description,
            question=f"What does {method} {path} do?",
            about="prose answer under a heading",
        ).add("\n\n")

    d.add("## Authenticating\n\nEvery request carries a bearer token.\n\n")
    d.answer(
        "```python\nimport requests\n\n"
        "def search(query: str, token: str) -> dict:\n"
        "    response = requests.post(\n"
        '        "https://api.example.com/v1/search",\n'
        '        headers={"Authorization": f"Bearer {token}"},\n'
        '        json={"query": query, "top_k": 5},\n'
        "        timeout=30,\n"
        "    )\n"
        "    response.raise_for_status()\n"
        "    return response.json()\n```",
        question="How do you authenticate a search request?",
        about="answer is a fenced code block containing blank lines",
    )
    d.add("\n\nThe token is sent on every request; there is no session.\n")
    return d.build()


def runbook() -> Corpus:
    """Answers in an alert table and in fenced configuration."""
    w = [20, 10, 10, 8]
    d = DocumentBuilder("runbook.md")
    d.add("# Operations Runbook\n\nOn-call triages within fifteen minutes of a page.\n\n")
    d.add("## Alert thresholds\n\nWarning pages the channel; critical pages a human.\n\n")
    d.add(_table(["signal", "warning", "critical", "action"], w))
    for signal, warn, crit, action, _ in ALERTS:
        d.answer(
            _row([signal, warn, crit, action], w),
            question=f"What is the critical threshold for {signal}?",
            about="answer is a table row",
        ).add("\n")
    d.add("\nThresholds are reviewed quarterly.\n\n")

    d.add("## What each alert means\n\n")
    for signal, _, _, _, meaning in ALERTS:
        d.add(f"### {signal}\n\n").answer(
            meaning,
            question=f"What does the {signal} alert indicate?",
            about="prose under a heading",
        ).add("\n\n")

    d.add("## Draining a node\n\nRemove it from the pool before restarting.\n\n")
    d.answer(
        "```bash\nkubectl cordon $NODE\n\n"
        "kubectl drain $NODE --ignore-daemonsets --delete-emptydir-data\n\n"
        "kubectl wait --for=delete pod -l app=indexer --timeout=300s\n```",
        question="How do you drain a node before restarting it?",
        about="fenced block with blank lines inside",
    )
    d.add("\n\nUncordon once the node reports ready.\n\n")
    d.add("## Rolling back\n\nRoll back before investigating.\n\n")
    d.answer(
        "```bash\nhelm rollback indexer --wait --timeout 5m\n```",
        question="What command rolls back a release?",
        about="short fenced block",
    )
    d.add("\n\nThe rollback is complete when the deployment reports ready.\n")
    return d.build()


def changelog() -> Corpus:
    """A dense table with short entries -- the densest structure in the corpus."""
    w = [8, 12, 66]
    d = DocumentBuilder("changelog.md")
    d.add("# Changelog\n\nDates are release dates, not merge dates.\n\n")
    d.add(_table(["version", "date", "change"], w))
    for version, date, change, _ in RELEASES:
        d.answer(
            _row([version, date, change], w),
            question=f"What changed in version {version}?",
            about="answer is one row of a dense table",
        ).add("\n")
    d.add("\n## Breaking changes\n\nOnly two releases required action.\n\n")
    for version, _, _, breaking in RELEASES:
        if breaking == "yes":
            d.add(f"### {version}\n\n").answer(
                f"Version {version} is a breaking release and requires a migration step.",
                question=f"Is version {version} a breaking release?",
                about="prose answer, short",
            ).add("\n\n")
    d.add("Everything else upgrades in place.\n")
    return d.build()


def tutorial() -> Corpus:
    """Long prose with long fenced blocks -- fences a size-based cut will straddle."""
    d = DocumentBuilder("tutorial.md")
    d.add("# Getting Started\n\nThis walks through indexing a folder and querying it.\n\n")

    steps = [
        (
            "Install the client",
            "The client needs Python 3.13 or newer, and refuses to start on anything older "
            "rather than failing later in a way that is hard to diagnose.",
            "```bash\npython -m venv .venv\n\nsource .venv/bin/activate\n\n"
            "pip install example-client==4.2.0\n```",
            "How do you install the client?",
        ),
        (
            "Configure credentials",
            "Credentials are read from the environment and never from a file, so that a key "
            "cannot be committed by accident.",
            "```bash\nexport EXAMPLE_API_KEY=sk-live-workspace-acme\n\n"
            "export EXAMPLE_WORKSPACE=acme-production\n```",
            "Where does the client read its credentials from?",
        ),
        (
            "Choose a chunk size",
            "Start at four hundred characters with no overlap; it is rarely the best setting "
            "and it is rarely a bad one.",
            "```python\nfrom example import Client, ChunkConfig\n\n"
            "config = ChunkConfig(\n    size=400,\n    overlap=0,\n"
            '    strategy="recursive",\n)\n```',
            "What chunk size should you start with?",
        ),
        (
            "Index a folder",
            "Indexing is incremental: files whose digest has not changed are skipped entirely, "
            "so a re-run costs almost nothing.",
            "```python\nfrom example import Client\n\nclient = Client()\n\n"
            "job = client.index(\n"
            '    "./handbook",\n    config=config,\n    workers=4,\n)\n\n'
            "print(job.id, job.status)\n```",
            "How do you index a folder?",
        ),
        (
            "Watch the job",
            "A job moves through queued, running and either complete or failed; it never "
            "reports complete with files it could not read.",
            "```python\nfor event in client.follow(job.id):\n"
            "    print(event.stage, event.files_done, event.files_total)\n\n"
            '    if event.stage == "failed":\n        raise SystemExit(event.error)\n```',
            "How do you follow the progress of an indexing job?",
        ),
        (
            "Query it",
            "A query returns chunks with the character offsets they came from, so every answer "
            "can be traced back to a position in a source file.",
            "```python\nhits = client.search(\n"
            '    "what is the escalation threshold?",\n    top_k=5,\n)\n\n'
            "for hit in hits:\n"
            "    print(hit.path, hit.start, hit.end, hit.score)\n```",
            "How do you run a query and see source offsets?",
        ),
        (
            "Add a reranker",
            "Reranking retrieves widely and keeps a few, which costs latency and usually buys "
            "precision on queries with rare terms.",
            "```python\nhits = client.search(\n"
            '    "expired signing certificate",\n'
            "    top_k=5,\n    candidates=50,\n"
            '    rerank="cross-encoder-small",\n)\n```',
            "How do you enable reranking on a query?",
        ),
        (
            "Handle rate limits",
            "A 429 carries a Retry-After header; honouring it is cheaper than backing off "
            "blindly, and the client does not retry for you.",
            "```python\nimport time\n\n"
            "while True:\n    response = client.raw_search(query)\n\n"
            "    if response.status_code != 429:\n        break\n\n"
            '    time.sleep(float(response.headers["Retry-After"]))\n```',
            "How should a client handle a 429 response?",
        ),
        (
            "Export the index",
            "An export is a point-in-time snapshot; chunk identifiers in it stay valid across "
            "a later reindex.",
            "```bash\nexample export --workspace acme-production \\\n"
            "  --format jsonl \\\n  --out ./snapshot.jsonl\n```",
            "How do you export a point-in-time snapshot?",
        ),
        (
            "Clean up",
            "Deleting a collection removes its chunks and its embeddings, and the operation "
            "cannot be undone from the client.",
            '```python\nclient.collections.delete(\n    "handbook",\n    hard=True,\n)\n```',
            "How do you delete a collection and its embeddings?",
        ),
    ]
    for i, (title, prose, code, question) in enumerate(steps, start=1):
        d.add(f"## Step {i} — {title}\n\n")
        d.answer(
            prose,
            question=f"Step {i}: {title.lower()} — what should you know?",
            about="prose answer between headings",
        ).add("\n\n")
        d.answer(code, question=question, about="long fenced block with blank lines").add("\n\n")

    d.add("## Troubleshooting\n\nMost failures are credential problems.\n\n")
    d.answer(
        "If the client reports 401, the workspace and the key belong to different accounts.",
        question="What does a 401 from the client usually mean?",
        about="prose answer at the end of the document",
    )
    d.add("\n")
    return d.build()


def spec() -> Corpus:
    """Two tables in one section, so a cut between them still lands in a table."""
    w1, w2 = [16, 10, 34], [16, 40]
    d = DocumentBuilder("spec.md")
    d.add("# Chunk Record Specification\n\nThe wire format for a single chunk.\n\n")
    d.add("## Fields\n\nAll offsets are character offsets into the normalised document.\n\n")
    d.add(_table(["field", "type", "meaning"], w1))
    fields = [
        ("chunk_id", "string", "Stable identifier, unique within a document."),
        ("document_id", "string", "Identifier of the document this chunk came from."),
        ("start", "integer", "First character of the chunk, inclusive."),
        ("end", "integer", "Last character of the chunk, exclusive."),
        ("retrieval_text", "string", "The text that was indexed for searching."),
        ("return_text", "string", "The text handed to the model, which may be wider."),
        ("sha256", "string", "Digest of the source document at index time."),
        ("strategy", "string", "Spec string naming the chunker and its parameters."),
        ("declared_overlap", "integer", "Characters of overlap the strategy declares."),
        ("code_path", "string", "Which lane produced this record."),
        ("tokenizer", "string", "Tokenizer used, or null when sizes are in characters."),
        ("created_at", "timestamp", "When the record was written, in UTC."),
        ("ordinal", "integer", "Position of the chunk within its document."),
        ("language", "string", "Detected language tag, or null when undetermined."),
    ]
    for name, kind, meaning in fields:
        d.answer(
            _row([name, kind, meaning], w1),
            question=f"What does the {name} field contain?",
            about="table row in the first of two adjacent tables",
        ).add("\n")

    d.add("\n### Constraints\n\nA record that breaks any of these is rejected.\n\n")
    d.add(_table(["constraint", "rule"], w2))
    constraints = [
        ("ordering", "start must be strictly less than end."),
        ("bounds", "end must not exceed the length of the source document."),
        ("overlap", "Overlap between neighbours must not exceed declared_overlap."),
        ("coverage", "No non-whitespace character may belong to zero chunks."),
        ("monotonic", "Chunks of one document must be emitted in ascending order."),
        ("digest", "sha256 must match the document the offsets refer to."),
        ("identity", "chunk_id must be stable across a reindex of unchanged content."),
        ("augmentation", "return_text may differ from the source only if declared."),
        ("encoding", "All text fields must be valid UTF-8 with no lone surrogates."),
        ("nullability", "tokenizer and language may be null; no other field may be."),
    ]
    for name, rule in constraints:
        d.answer(
            _row([name, rule], w2),
            question=f"What is the {name} constraint on a chunk record?",
            about="table row in the second adjacent table",
        ).add("\n")

    d.add("\n## Example\n\nA single record, as emitted.\n\n")
    d.answer(
        '```json\n{\n  "chunk_id": "handbook.md#0042",\n'
        '  "start": 4120,\n  "end": 4533,\n'
        '  "retrieval_text": "Escalation is approved by the duty director.",\n'
        '  "return_text": "Escalation is approved by the duty director.",\n'
        '  "sha256": "3f786850e387550fdab836ed7e6dc881de23001b"\n}\n```',
        question="What does a chunk record look like on the wire?",
        about="fenced JSON block",
    )
    d.add("\n\nUnknown fields are ignored by readers.\n")
    return d.build()


BUILDERS = (api_reference, runbook, changelog, tutorial, spec)


def build() -> list[Corpus]:
    return [builder() for builder in BUILDERS]


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "corpus/structured")
    corpora = build()
    gold = write_dir(corpora, target)
    total = sum(len(c.questions) for c in corpora)
    print(f"wrote {len(corpora)} documents and {total} questions to {target}\n")
    for corpus in corpora:
        tables = sum(1 for line in corpus.text.splitlines() if line.strip().startswith("|"))
        fences = corpus.text.count("```")
        print(
            f"  {corpus.name:<20} {len(corpus.text):>6} chars  "
            f"{len(corpus.questions):>3} questions  {tables:>3} table rows  {fences:>2} fences"
        )
