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

Then check the draft for these, which are what make prose read as
machine-written:

| Habit | Fix |
|---|---|
| No contractions anywhere | Use them. This alone does most of the work. |
| Every paragraph pivoting on "not X, but Y" | One per entry at most. |
| A short aphorism closing each section | Cut it. Let the entry stop when the content stops. |
| Telling the reader how to react: "note that", "consider", "sit with that" | Delete. |
| Triads: three examples, three clauses, everywhere | Use two, or four. |
| Hedged universals: "almost every", "most people" | Name who, or drop the claim. |
| Uniform sentence length | Vary it. A long sentence carrying a subordinate clause is fine. |
| Generic detail standing in for real detail: "I was surprised" | Say what you assumed, and for how long. |

The last row matters most. Absence of contingency is the deepest tell, and one
real specific does more than cutting ten adjectives.

Corrections stay visible: when a number changes, correct in place and leave the
superseded value with a note.

#218 `ai-sniffer` in [IDEAS.md](IDEAS.md) is the tool that would check this
automatically. Until it exists, this table is the manual version.
