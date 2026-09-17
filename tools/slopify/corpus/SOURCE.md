# The reference prose

Source text for slopify's injections: technical writing by named humans, published
before model-drafted prose was common. Used for **one purpose** — to be the thing
habits are injected into, so that a label says what was put there rather than what
was already present.

## What is in it

| File | Author | Published | Words |
|---|---|---|---|
| `willison-2018-datasette-ideas.md` | Simon Willison | 2018-10-04 | 2,749 |
| `willison-2018-docker-images.md` | Simon Willison | 2018-11-19 | 1,835 |
| `benita-2021-hash-indexes.md` | Haki Benita | 2021-01-11 | 3,243 |
| `starburst-2021-data-mesh.md` | Daniel Abadi | 2021-03-25 | 2,375 |
| `willison-2021-standing-out.md` | Simon Willison | 2021-07-17 | 497 |
| `pavlo-2022-databases-review.md` | Andy Pavlo | 2022-12-31 | 3,104 |

Four authors, 13,803 words as fetched, 12,268 of it prose the parser will inject
into. Hashes are in [`fetch.py`](fetch.py).

## Licence, and why the prose is fetched rather than committed

**None of these states reuse terms.** Default copyright applies and the authors
retain all rights, so the repository holds this script and the hashes and never the
text. `reference/` is git-ignored. `tools/chunking-lab/benchmarks/fetch.py` sets
the precedent for downloading a corpus and pinning it; the reason there was size,
and the reason here is that the text is not ours to redistribute.

The hash covers the extracted prose rather than the page, because these templates
carry navigation and sponsor blocks that change while the article does not. A
changed hash means the post was edited or an extractor broke, and that is a failed
check instead of a quietly different number. `fetch.py --update` reprints the
hashes once someone has looked at the change.

## Provenance

Every post is by a named author writing under their own name, and five of the six
predate ChatGPT's release outright. That is what makes provenance checkable without
anyone having to attest to it, which is the failure recorded in
[`docs/014`](../../../docs/014_slopify.md) §2.

**One exception, stated rather than buried.** `pavlo-2022-databases-review.md` is
dated 31 December 2022, a month after ChatGPT's release, so its date does not place
it before model-drafted prose the way the others do. It is in the corpus on Pavan's
judgement that the models of December 2022 were not capable of writing it. Its
per-source numbers are reported separately in docs/014 §5a so the effect of
including it is visible rather than assumed.

## Register, and what this corpus is not

**Register.** ai-sniffer is aimed at engineers writing about their own work, which
is what these are: two design arguments, a database internals walkthrough, a
debugging narrative, an opinion piece on data architecture, and a year in review.
Public-domain literary prose would be easier to ship and a worse proxy — an
antithesis in Victorian fiction is a style, not a tell.

**Four authors is still few.** Willison contributes three of the six posts and the
highest habit rate in §5a; Pavlo the lowest, at a quarter of it. A detector tuned to
these numbers would be tuned to those four voices. Adding more authors is a few
lines in `fetch.py`, and until then the numbers carry that limit.
