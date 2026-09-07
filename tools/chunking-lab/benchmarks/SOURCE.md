# The Chroma chunking benchmark

Five corpora and 472 questions, each annotated with the exact character ranges
that answer it. Used by this tool for **one purpose**: checking that our
`precision_omega` reproduces a published number.

## Provenance

| | |
|---|---|
| Upstream | [`brandonstarxel/chunking_evaluation`](https://github.com/brandonstarxel/chunking_evaluation) |
| Commit | `e708410d1c61cb76a85cd9d433630ef89b9c6b85` (pinned) |
| Path | `chunking_evaluation/evaluation_framework/general_evaluation_data` |
| Licence | MIT © 2024 Brandon Smith |
| Paper | [Evaluating Chunking Strategies for Retrieval](https://research.trychroma.com/evaluating-chunking) |

| File | SHA-256 |
|---|---|
| `corpora/chatlogs.md` | `543a98f8…65bda6` |
| `corpora/finance.md` | `1c48d015…08561f` |
| `corpora/pubmed.md` | `0fd9242f…7684ced` |
| `corpora/state_of_the_union.md` | `6fc21d56…531b37` |
| `corpora/wikitexts.md` | `74cafcdb…4b86c0` |
| `questions_df.csv` | `3ab39018…dda7a3` |

The full hashes live in `fetch.py`, which verifies every download against them.

## Fetched, not committed

1.6MB of text would roughly triple the pack size of a collection whose entire
history is 260KB, and this repo's precedent is to generate or fetch fixtures
rather than commit them. The pinned commit and the hashes are what make the
result reproducible: a changed byte upstream is a **failed check**, not a
silently different number.

```bash
uv run python tools/chunking-lab/benchmarks/fetch.py
```

## What it is used for

`tests/test_reproduction.py` asserts that our Precision Ω matches the published
column for the four `RecursiveCharacterTextSplitter` rows:

| chunk size / overlap | published Precision Ω |
|---|---|
| 800 / 400 | 6.7 |
| 400 / 200 | 13.9 |
| 400 / 0 | 17.7 |
| 200 / 0 | 29.9 |

Only the recursive rows, and only Precision Ω. That is not a limitation — it is
the point. **Precision Ω involves no retrieval**, so reproducing it needs no
embedding model, no vector store, no API key and no network. The other columns in
that table (recall, precision, IoU) all depend on a retriever, and reproducing
them would mean reproducing Chroma's embedding model too.

`tiktoken` is required only because the table's *sizes* are quoted in tokens; it
is the whole reason the `benchmark` extra exists. Nothing this tool measures for
itself needs a tokenizer.

## Why bother

Precision Ω is this tool's headline metric, and it had already been implemented
once from a misreading — "the minimal set of chunks covering the gold spans"
rather than "every chunk containing a gold character". The two coincide for a
non-overlapping partition and diverge as soon as chunks overlap, by about 28%
relative. Every unit test written against the wrong understanding passed.

A published table is the one test that could not.
