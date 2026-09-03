# Conventions

How every tool in this collection is shaped, so that any one of them can be used
alone and all of them can be used together.

## The three seams

Tools **never import each other**. They compose along three seams:

### 1. CLI seam

Every tool is an independently installable distribution with a console script.

```bash
# one tool, nothing else installed
uvx --from "git+https://github.com/pavanrao/data-tools#subdirectory=tools/ingest-ledger" \
    ingest-ledger report ./corpus

# or the whole collection, in dev
uv sync && uv run ingest-ledger report ./corpus
```

Single-file utilities that don't earn a package use [PEP 723][pep723] inline
script metadata so `uv run script.py` resolves its own dependencies.

[pep723]: https://peps.python.org/pep-0723/

### 2. Data seam

Tools exchange **artifacts, not objects**: JSONL records and a SQLite ledger
whose schema lives in `data-tools-core`. A record always carries a
`Provenance` (source path, content hash, unit kind, unit id) so any downstream
tool can trace a value back to the byte range it came from.

This is what lets `ingest-ledger` feed `chunking-lab` (#25) or `docs-rag` (#1)
without either knowing the other exists.

### 3. MCP seam

A tool that is useful to an agent exposes a server at `<package>.mcp:server`
and advertises it in the `data_tools.mcp` entry-point group. `mcp-gateway`
(#16) mounts every installed one behind a single endpoint.

## Package layout

```
tools/<tool-name>/
├── pyproject.toml          # name = "data-tools-<tool-name>"
├── README.md               # what it does, install, usage, prior art
├── src/<tool_name>/
│   ├── cli.py              # console script entry point
│   └── ...
└── tests/
```

- Directory and CLI use `kebab-case`; the Python package uses `snake_case`.
- Distribution name is always `data-tools-<tool-name>`.
- Register in the `data_tools.tools` entry-point group so `dt` discovers it.

## Rules

1. **A tool runs with only its own dependencies installed.** If it needs
   another tool, it shells out or reads its artifacts — it does not import it.
2. **Heavy or optional backends are extras**, never base dependencies. Degrade
   gracefully and *record which path ran* rather than silently substituting.
3. **The deterministic core is model-free.** LLM calls sit behind the
   `data_tools_core.llm` interface and are always optional; a tool that cannot
   run without a model is a tool that cannot be tested.
4. **Pin third-party integrations exactly** and isolate each behind one adapter
   module, so an upstream break costs one file.
5. **Every non-obvious status is evidence-bearing.** When a tool reports a
   verdict, the record says which probe produced it and what it saw.
