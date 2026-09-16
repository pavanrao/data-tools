# slopify — put the tells back in, on purpose

Takes a passage a human wrote and injects the habits
[`ai-sniffer`](../ai-sniffer/) looks for, at positions it records. Deterministic
and seeded: the same input and seed give the same output every time, and each
injection is written out as a label in the format
`tools/ai-sniffer/eval/labels.jsonl` already uses.

It is the inverse of the reviewer, and it exists because every number in
ai-sniffer's eval rests on 179 labels one person wrote. Injection gives ground
truth with no labeller's judgement in it, and so gives **per-habit recall**,
which the hand labels cannot: they hold 34 antithesis labels and 2 restatement.

```bash
uv run slopify habits                        # the eleven injectable habits
uv run slopify inject DRAFT.md --seed 42 --count 12 \
    --out slopped.md --labels labels.jsonl
uv run ai-sniffer check slopped.md           # what a detector finds
```

Standard library only: no model and no network.

## What it does to a paragraph

One injector per habit in ai-sniffer's catalogue. Each returns the rewritten
paragraph and the exact words a reader would quote as the habit — or nothing,
when the paragraph offers no site for it.

| habit | what it does |
| --- | --- |
| `antithesis` | rewrites a claim into "X isn't a detail. It is Y." |
| `fragment` | appends a verbless phrase, built from a noun in the paragraph |
| `triad` | appends a sentence whose only shape is three of something |
| `dramatic-beat` | breaks the last sentence out as a one-line paragraph |
| `closer` | appends a line saying what it all meant |
| `restatement` | says the previous sentence again, adding nothing |
| `cliche-emphasis` | prefixes a sentence with "The key insight is that" |
| `generic-detail` | replaces a figure with "a fair number of" |
| `reader-instruction` | prefixes a sentence with "Note that" |
| `hedge` | softens a universal: "every" becomes "almost every" |
| `emphasis-word` | inserts "exactly" after a copula |

Declining is the normal case, not a failure. A paragraph with no copula cannot
be given an antithesis without inventing a claim, and an invented claim would
make the ground truth a fiction.

## What it never touches

Front matter, fenced code, tables, HTML blocks, lists, headings and block
quotes come through byte for byte. Only prose paragraphs are eligible, because a
habit injected into a code fence is a habit no reader ever sees.

## The labels

One JSONL record per injection, in ai-sniffer's label format plus the seed:

```json
{"id": "draft-01", "draft": "draft.md", "habit": "hedge", "severity": "high",
 "quote": "almost every trailing", "source": "injected", "seed": 42, "line": 19}
```

`line` is read from the **rendered** draft, because injecting into an early
paragraph moves every line below it. Each quote is verified present in the final
text before its label is written; a later injection can rewrite the sentence an
earlier one landed in, and a label nobody can find would score every detector at
zero.

Every injected label is `high`. A template instance is the strong form of its
habit by construction, and grading some of them "low" would be a judgement —
the thing injection exists to avoid.

## Limits, to state wherever its numbers appear

**Injected habits are what a template produces on demand, not what a model
produces when left alone.** A tool can score well here and badly on real drafts,
so these numbers are a diagnostic and ai-sniffer's hand-labelled held-out
numbers stay the headline.

**Source text matters.** Inject into prose no model wrote. Injecting into an
AI-drafted post measures habits on top of habits, and the labels no longer say
what is ground truth and what was already there. `corpus/fetch.py` downloads the
reference corpus: three Simon Willison posts, 2018 to 2021, hash-pinned and not
committed, because they carry no reuse licence.

The eval discounts whatever the detector already says about the untouched draft,
which matters even on clean source: the linter reports 56 findings on those 4,695
human-written words before anything is injected, 37 of them one-sentence
paragraphs. A detector is never credited for a habit that was there first.

**Word-borrowing is approximate.** `fragment` and `triad` take a noun from the
paragraph by looking for what an article points at, which is right most of the
time and occasionally picks a compound's modifier — "that finish line" yields
*finish*. The shape is still the habit; the word is sometimes odd.

## Prior art

Searched after building, which is the wrong order, and recorded that way because
the ordering is part of what happened. **The method is mutation testing**, pointed at a prose linter instead of a test
suite: inject known faults, count which ones the rules catch. That is standard for
evaluating static analysers and is decades old.

**[CheckList](https://aclanthology.org/2020.acl-main.442.pdf)** (Ribeiro et al.,
ACL 2020) is the closest analogue in NLP and has the same structure. Its
*Directional Expectation* test perturbs an input and expects the prediction to move
in a stated direction, and it reports per linguistic capability rather than as one
accuracy figure. Per-habit recall is that breakdown under another name.

**[APT-Eval](https://arxiv.org/pdf/2502.15666)** builds 14.7K samples by having
LLMs polish human-written text to varying degrees and measuring what detectors do.
Same design as this — start from human prose, add AI-ness, test detectors.

**What is different here** is span-level ground truth. Because the injection is a
deterministic template rather than a model, the label carries the line and the exact
words, which is what makes per-habit recall computable against a reviewer that
quotes. APT-Eval's polishing gives a document-level label and cannot say where.

Nothing found goes in this direction as a tool. The ecosystem removes tells —
[DeSlop](https://github.com/AUAggy/deslop),
[desloper](https://github.com/yurvon-screamo/desloper),
[DeleteSlop](https://www.deleteslop.com/) — and none of them injects any.

`slopify` is idea **#219** in [`IDEAS.md`](../../IDEAS.md). Design record:
[`docs/014_slopify.md`](../../docs/014_slopify.md).
