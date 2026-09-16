# 014 — `slopify`: ground truth you don't have to judge

Idea **#219**. The inverse of [`ai-sniffer`](012_ai-sniffer.md): it takes prose a
human wrote and injects the habits ai-sniffer looks for, recording where each one
went. Built after the first label review was applied and #218's scores were final,
because its whole purpose is to answer a question those scores cannot.

---

## 1. Why it exists

Every number in ai-sniffer's eval rests on 179 labels one person wrote. That is
enough to rank detectors overall, and not enough to say which *habits* a detector
is good at, because the hand labels are distributed by what the drafts happened to
contain: 34 antithesis labels against 2 restatement. A recall figure computed from
2 instances is not a figure.

Injection removes the labeller. If the tool put a hedge at line 19, a hedge is at
line 19 — there is no judgement in the label and no second labeller to recruit.
Ten seeds across three sources gives thirty instances of each habit, and every
detector in the comparison gets a per-habit recall number with nothing to argue
about. What the source text is still matters, which §2 is about.

## 2. What it is not

**Injected habits are what a template produces on demand, not what a model
produces when left alone.** This limit is the reason the numbers below are a
diagnostic and never the headline. A detector could match every template here by
memorising "Note that" and still miss every real draft; ai-sniffer's hand-labelled
held-out numbers remain the claim, and these sit underneath them explaining *which
habits* those numbers are made of.

**Source text matters.** Inject into prose no model wrote. Injecting into an
AI-drafted post measures habits on top of habits, and the labels stop saying which
is which.

The corpus is three posts by Simon Willison, published 2018 to 2021: a named
engineer arguing a technical case in public, which is the register ai-sniffer is
aimed at. 4,108 prose words across 120 paragraphs. They carry no reuse licence, so
`tools/slopify/corpus/fetch.py` downloads them and the repository holds the hashes
rather than the prose, following the precedent in
`tools/chunking-lab/benchmarks/fetch.py`. The hash is taken over the extracted
prose and not the HTML, because the page template carries a sponsor block that
changes weekly while the article does not. Provenance and the licence position are
recorded in `tools/slopify/corpus/SOURCE.md`.

One limit to carry: every habit is measured against one author's voice, so a
detector tuned to these numbers would be tuned to him. Widening the corpus to
several authors is the obvious next improvement.

> **Corrected 2026-09-16.** This section first claimed three posts from
> `pavanrao.github.io` as its human baseline, on the grounds that they were written
> in January 2026, *"eight months before any of this tooling existed"*, and cited
> their contraction rate and sentence-length variation as evidence: *"which is
> itself a small piece of evidence that they are the human baseline they are being
> used as."* Every post on that blog was written by a model to Pavan's
> instructions. Reading authorship out of style statistics is the mistake
> [docs/012](012_ai-sniffer.md) says this tool exists to avoid, and the statistics
> in question were ai-sniffer's own output. §5 now runs on the Willison corpus; the
> superseded table is kept there.

The measurement also subtracts a baseline, which is worth keeping even on clean
source, because human prose contains these habits too. Every finding the detector
makes on the untouched draft is counted first and then discounted, matched on habit
and text rather than line, since an injection moves everything below it. Counted,
not merely collected: the sources already contain the word *exactly*, so injecting
another has to register as a second instance rather than be cancelled by the first.

## 3. Design

One injector per habit in the catalogue, each a function of a paragraph and a
seeded `random.Random`. Each returns the rewritten paragraph and the exact words a
reader would quote as the habit, or `None`.

**Declining is the normal case.** A paragraph with no copula cannot be given an
antithesis without inventing a claim, and an invented claim would make the ground
truth a fiction. `--count` is therefore a ceiling and not a promise, and no
paragraph takes more than three injections, past which the prose stops resembling
a draft anyone would write — which would test a detector on the wrong thing.

**Only prose is eligible.** Front matter, fenced code, tables, HTML, lists,
headings and block quotes come through byte for byte. A habit injected into a code
fence is a habit no reader ever sees.

**Line numbers come from the rendered draft**, because injecting into an early
paragraph moves every line below it. A label whose line was read from the input
would point at the wrong place in the file the detector is given.

**Every quote is verified present in the final text before its label is written.**
A later injection can rewrite the sentence an earlier one landed in; a label nobody
can find would score every detector at zero against it, silently.

**Severity is always `high`.** A template instance is the strong form of its habit
by construction, and grading some of them "low" would put back the judgement the
tool exists to remove. ai-sniffer's scorer counts high and medium towards recall,
so every injected habit is countable.

## 4. What the injectors had to be taught

Each of these was found by reading the output, not by reasoning about it, and each
was the injector introducing a fault of its own instead of the habit it was asked
for. A detector that catches the injected text for being ungrammatical
has not caught the habit.

| what came out | why | what fixed it |
| --- | --- | --- |
| `Two currentlys, both familiar.` | the word-borrowing templates took any word | borrow the head noun an article points at |
| `Two countrys, both familiar.` | naive pluralisation | `-y` → `-ies`, `-s/-x/-ch/-sh` → `-es` |
| `Note that social Security...` | lowercasing the first word of every prefixed sentence | lowercase only function words, never a name |
| `It serves two primary purposes:.` | restating a sentence that introduces a list | refuse sentences ending in `:` |
| `at least quite a lot U.S. credits` | a vague phrase that needs an "of" | use forms that work as quantifiers, and only where a noun follows |
| `I wasn't a technicality.` | the antithesis foils are things, and the subject was a person | refuse a personal subject; split a compound subject at its last joiner |

The remaining imprecision is stated rather than fixed: borrowing a noun by looking
for what an article points at is right most of the time and occasionally picks a
compound's modifier, so `that finish line` yields *finish*. The shape is still the
habit; the word is sometimes odd.

## 5. What `ai-sniffer check` can and cannot see

### 5a. What it says about human prose, before anything is injected

The corpus is 4,695 words of technical blogging that no model wrote. The
model-free linter reports **56 findings** in it:

| habit | findings |
| --- | --- |
| one-sentence-paragraph | 37 |
| emphasis-word | 13 |
| hedge | 4 |
| reader-instruction | 1 |
| even-rhythm | 1 |
| **total** | **56** |

This is the *break it on purpose* step [#218](../IDEAS.md) asked for, and it is the
strongest argument in this repository for why ai-sniffer has no verdict mode. Two
thirds of those findings are one-sentence paragraphs, which in this author's hands
are a house style rather than a tell: he writes them deliberately and often. A
threshold over this corpus would call a working engineer's blog machine-written.

Which is also why every recall figure below discounts them. A detector cannot be
credited for finding a habit that was in the prose before slopify touched it.

### 5b. Per-habit recall

320 single-habit injections — 11 habits × 3 posts × 10 seeds, minus combinations
that found no site. **Quoted** means the linter's own quote overlaps the injected
one. **On line** is the looser reading: any finding within one line of the
injection. Both discount the baseline in §5a.

| habit | injected | quoted | on line |
| --- | --- | --- | --- |
| reader-instruction | 30 | 30 | 30 |
| emphasis-word | 30 | 30 | 25 |
| hedge | 30 | 21 | 21 |
| dramatic-beat | 30 | 21 | 11 |
| generic-detail | 20 | 11 | 11 |
| cliche-emphasis | 30 | 8 | 8 |
| fragment | 30 | 5 | 3 |
| restatement | 30 | 2 | 2 |
| triad | 30 | 1 | 0 |
| antithesis | 30 | 0 | 0 |
| closer | 30 | 0 | 0 |
| **total** | **320** | **129** | **106** |

The line this draws is the one the tool was built to draw, and it is sharper than
the overall figure in [docs/012](012_ai-sniffer.md) §4 could ever be. The linter is
perfect on the two habits that are a closed word list it can match — an opener, an
intensifier — good on a third, and at or near zero on every habit that is a
*shape*. Antithesis, closer, triad and restatement are **3 of 120** between them.

That is not a defect in the linter; it is the reason ai-sniffer ships a reviewer
prompt at all, and it now has a number per habit instead of an argument. The same
320 drafts are what the model reviewers should be run against next, which turns
"Sonnet caught 35 to 41 of 62" into a statement about which habits those were.

`generic-detail` is 20 rather than 30 because one post contains no figure with a
noun after it for the injector to replace. That absence is visible in the table
instead of hidden in a percentage.

> **Superseded 2026-09-16.** The first version of this section ran on three posts
> from `pavanrao.github.io`, before Pavan confirmed they were model-written (§2).
> Over 280 injections it read 111 quoted and 132 on line; adding the baseline
> subtraction brought it to 107 and 111. Those numbers described a detector scored
> against contaminated source, and the fault they carried was the source, not the
> arithmetic — the shape habits were already at or near zero there too.

## 6. Where it fits

Before post 3 of the [#218 series](../IDEAS.md), whose comparison it strengthens:
the market comparison can now report per-habit recall for every tool in
[docs/013](013_ai-sniffer-linter-comparison.md) instead of one number each. The
demo it makes possible needs no model — one human paragraph, one slopped paragraph,
and the linter's output under each.

```bash
make demo-slopify SLOPIFY_DRAFT=path/to/your-own-writing.md
```

There is no default and no sample corpus, for the reason in §2: neither this
repository nor the blog holds prose that no model touched. Shipping a sample would
invite the mistake that section warns about, so the path is required and the target
refuses without it.

## 7. What is deliberately not here

**No scoring.** `slopify` writes text and labels; ai-sniffer's eval scores them.
Scoring inside the injector would let the tool that creates the answer also mark
the paper.

**No model path.** Every injector is string surgery, so the tool has no `llm`
extra and nothing to degrade to. A model-written injection would be a better test
of a detector, and it would also put back the thing being measured.

**Not merged into `labels.jsonl`.** Injected labels are written to their own file.
`source: "injected"` is recorded on every record so that a future merge is possible
and an accidental one is visible.
