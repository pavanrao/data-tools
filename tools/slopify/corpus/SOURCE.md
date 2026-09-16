# The reference prose

Source text for slopify's injections: technical writing by a named human, published
well before model-drafted prose was common. Used for **one purpose** — to be the
thing habits are injected into, so that a label says what was put there rather than
what was already present.

## Provenance

| | |
|---|---|
| Author | Simon Willison ([simonwillison.net](https://simonwillison.net/)) |
| Published | November 2018, October 2018, July 2021 |
| Licence | **None stated.** Default copyright, author retains all rights. |
| Fetched by | [`fetch.py`](fetch.py) into `reference/`, which is git-ignored |
| Pinned by | SHA-256 over the extracted prose, not the HTML |

| File | Words | SHA-256 |
|---|---|---|
| `willison-2018-docker-images.md` | 1,835 | `09a58032b7a3…3b0d` |
| `willison-2018-datasette-ideas.md` | 2,749 | `99c65d028912…4ada` |
| `willison-2021-standing-out.md` | 497 | `ac6b7eeb668d…7d1f` |

## Why it is fetched and not committed

These posts carry no reuse licence, so the repository holds the script and the
hashes and never the prose. `tools/chunking-lab/benchmarks/fetch.py` sets the
precedent for downloading a corpus and pinning it; the reason there was size, and
the reason here is that the text is not ours to redistribute.

The hash covers the extracted prose rather than the page, because the site template
carries a sponsor block that changes weekly while the article does not. A changed
hash means the post was edited or the extractor broke, and that is a failed check
instead of a quietly different number. When a post is revised upstream,
`fetch.py --update` prints the new hashes once someone has looked at the change.

## Why these, and what they are not

**Register.** ai-sniffer is aimed at engineers writing about their own work, which
is what these are: an argument for a design, a debugging narrative, and a piece of
career advice. Public-domain literary prose would be easier to ship and a worse
proxy — an antithesis in Victorian fiction is a style, not a tell.

**Date.** 2018 to 2021, before model-drafted prose was common enough to worry about.
That is what makes provenance checkable without anyone having to attest to it, which
is the failure recorded in [`docs/014`](../../../docs/014_slopify.md) §2.

**One author.** Every habit measured against this corpus is measured against one
person's voice. A detector tuned to it would be tuned to him. Widening this to
several authors is the obvious next improvement, and until then the numbers in
docs/014 §5 carry that limit.
