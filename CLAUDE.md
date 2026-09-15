# CLAUDE.md

Normative rules for code: [CONVENTIONS.md](CONVENTIONS.md).
Project shape and the add-a-tool checklist: [docs/000](docs/000_project-organization.md).
This file holds only what those two don't.

## Gotchas that have cost time

- `make sync` is `uv sync --all-extras`. A bare `uv sync` leaves two
  ingest-ledger tests failing — see B1 in [docs/BACKLOG.md](docs/BACKLOG.md).
- A newly added workspace member needs
  `uv sync --all-extras --reinstall-package data-tools-<name>`. Plain `uv sync`
  resolves it but does not install it.
- Tests run under `--import-mode=importlib`. Shared test state goes in a
  `conftest.py` fixture; `from test_foo import bar` will not resolve.
- The MCP Python SDK uses snake_case attributes (`structured_content`,
  `input_schema`, `is_error`), not the camelCase names in the specification.
- PRs are merged with a merge commit, not squashed. Docs land in the same PR
  as the code they describe.

## Writing FINDINGS.md and LEARNINGS.md

These are logs of things that actually happened. An entry that could have been
written without doing the work is not an entry.

Have these three before adding one: what was actually run, with the command or
config; the number or the exact error text, copied rather than recalled; and
what was expected instead.

Then review the draft for the habits that make prose read as machine-written.
The single definition of those habits is the catalogue in
[tools/ai-sniffer/agent/ai-sniffer.md](tools/ai-sniffer/agent/ai-sniffer.md). Run
`uv run ai-sniffer check FILE` for the countable ones, and the ai-sniffer agent or
`ai-sniffer review FILE` for the structural ones. In the eval on 2026-09-15, Sonnet
caught far more held-out habits than Haiku (36 to 43 of 63, against 7 to 10), so
review with Sonnet ([docs/012](docs/012_ai-sniffer.md) §4a). The reviewer only
quotes what it finds, so you make the fixes.

Of those habits, generic detail standing in for a real one matters most. One real
specific, like what you assumed and for how long, does more than cutting ten
adjectives.

Corrections stay visible: when a number changes, correct in place and leave the
superseded value with a note.
