# Conventions

How every tool in this collection is shaped, so that any one of them can be used
alone and all of them can be used together.

This is the normative summary. The reasoning behind each rule — and the log of
decisions that were tried and replaced — lives in
[`docs/000_project-organization.md`](docs/000_project-organization.md) and
[`docs/001_architecture-and-decisions.md`](docs/001_architecture-and-decisions.md).

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

A tool that is useful to an agent advertises a **zero-argument server factory**
in the `data_tools.mcp` entry-point group. A factory rather than a module-level
server, so discovery never constructs a store or loads a model at import time.
`mcp-gateway` (#16) mounts every installed one behind a single endpoint.
`repo-rag` is the worked example (`repo_rag.mcp_server:create_server`).

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
- Register in the `data_tools.tools` entry-point group so `dt` discovers it, and
  give `main()` a one-line docstring — `dt ls` prints it as the tool's summary.
- Ship a `__main__.py` too, so `python -m <tool_name>` works when the scripts
  directory is not on `PATH` or the launch directory is unknown.
- Target Python `>=3.13`.

### The spin-out seam

A tool depends on the shared library *normally*, and overrides the source
**dev-only**:

```toml
dependencies = ["data-tools-core", ...]

[tool.uv.sources]
data-tools-core = { workspace = true }
```

uv strips `[tool.uv.sources]` from built wheels, so deleting that one block is
the entire "leave the workspace" step:

```bash
git subtree split -P tools/<name> -b <name>-split   # keeps history
# push to a new repo, delete the block, depend on the published data-tools-core
```

Declare it from day one. It costs three lines and it is what makes rule 1
enforceable rather than aspirational.

## Rules

1. **A tool runs with only its own dependencies installed.** If it needs
   another tool, it shells out or reads its artifacts — it does not import it.
2. **Heavy or optional backends are extras**, never base dependencies. Degrade
   gracefully and *record which path ran* rather than silently substituting.
3. **The deterministic core is model-free.** LLM calls sit behind the
   `data_tools_core.llm` interface and are always optional; a tool that cannot
   run without a model is a tool that cannot be tested. The interface is two
   protocols (`EmbeddingProvider`, `ChatProvider`); no tool imports a vendor or
   LiteLLM directly, and the backend is imported *inside the call* so that
   `import data_tools_core.llm` never drags in a model stack. Install it with
   the `llm` extra.
4. **Pin third-party integrations exactly** and isolate each behind one adapter
   module, so an upstream break costs one file.
5. **Every non-obvious status is evidence-bearing.** When a tool reports a
   verdict, the record says which probe produced it and what it saw.
6. **Tests run with nothing optional installed.** Inject fake providers; patch
   the one lazy backend accessor. The suite needs no network and no model. It
   runs under `--import-mode=importlib`, so pass shared test constants as
   fixtures — a bare `from conftest import ...` will not resolve.
