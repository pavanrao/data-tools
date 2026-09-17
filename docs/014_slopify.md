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

The corpus is six posts by four authors — Simon Willison, Haki Benita, Daniel Abadi
and Andy Pavlo — published 2018 to 2022. 12,268 words of prose that no model wrote.
Provenance, licence position and the one caveat are in
`tools/slopify/corpus/SOURCE.md`.

### 5a. What it says about human prose, before anything is injected

The model-free linter reports **100 findings** across that corpus:

| source | words | findings | per 1,000 words |
| --- | --- | --- | --- |
| willison-2018-datasette-ideas | 2,690 | 34 | 12.6 |
| willison-2021-standing-out | 489 | 6 | 12.3 |
| willison-2018-docker-images | 1,516 | 16 | 10.6 |
| benita-2021-hash-indexes | 2,208 | 18 | 8.2 |
| starburst-2021-data-mesh | 2,335 | 16 | 6.9 |
| pavlo-2022-databases-review | 3,030 | 10 | 3.3 |
| **total** | **12,268** | **100** | **8.2** |

Those 100 split by habit as one-sentence-paragraph 56, emphasis-word 23, hedge 17,
reader-instruction 2 and even-rhythm 2. This is the *break it on purpose* step [#218](../IDEAS.md) asked for, and it is the
strongest argument in this repository for why ai-sniffer has no verdict mode. More
than half the findings are one-sentence paragraphs, which in Willison's hands are a
house style: he writes them deliberately and often, and his rate is nearly four
times Pavlo's. A threshold tuned on this corpus would rank four working engineers
by how much they resemble a machine, and would put the one with the most distinctive
voice at the top.

That spread is also why the figure has to be read per author rather than as one
number. The same linter, on the same kind of writing, varies by 4x depending on who
is writing.

Which is why every recall figure below discounts it. A detector cannot be credited
for finding a habit that was in the prose before slopify touched it.

**The model reviewer was run over the same six untouched posts**, and reports 65
findings against the linter's 100. The totals are the least interesting part, because
per post the two disagree in both directions:

| post | linter | model |
| --- | --- | --- |
| willison-2018-datasette-ideas | 34 | 16 |
| benita-2021-hash-indexes | 18 | 7 |
| willison-2018-docker-images | 16 | 2 |
| starburst-2021-data-mesh | 16 | 19 |
| pavlo-2022-databases-review | 10 | 9 |
| willison-2021-standing-out | 6 | 12 |
| **total** | **100** | **65** |

They are not reading the same text the same way. The linter's findings are
one-sentence paragraphs and intensifiers; the model's are triads, closers and hedges,
which the linter cannot see. On the docker post the linter fires sixteen times at a
paragraph shape this author uses on purpose and the model finds two things; on the
data-mesh piece the model finds nineteen rhetorical figures in an academic's
argumentative prose. Their false positives on human writing barely overlap, which is
the same shape as the recall result in §5c.

### 5b. Per-habit recall

650 single-habit injections — 11 habits × 6 posts × 10 seeds, minus combinations
that found no site. **Quoted** means the linter's own quote overlaps the injected
one. **On line** is the looser reading: any finding within one line of the
injection. Both discount the baseline in §5a.

| habit | injected | quoted | on line |
| --- | --- | --- | --- |
| reader-instruction | 60 | 60 | 48 |
| emphasis-word | 60 | 60 | 48 |
| dramatic-beat | 60 | 44 | 25 |
| hedge | 60 | 30 | 30 |
| cliche-emphasis | 60 | 13 | 14 |
| generic-detail | 50 | 12 | 16 |
| fragment | 60 | 7 | 5 |
| restatement | 60 | 3 | 3 |
| triad | 60 | 1 | 0 |
| antithesis | 60 | 0 | 0 |
| closer | 60 | 0 | 0 |
| **total** | **650** | **230** | **189** |

The line this draws is the one the tool was built to draw, and it is sharper than
the overall figure in [docs/012](012_ai-sniffer.md) §4 could ever be. The linter is
perfect on the two habits that are a closed word list it can match — an opener, an
intensifier — good on a paragraph shape it can count, and at or near zero on every
habit that is a *rhetorical* shape. Antithesis, closer, triad and restatement are
**4 of 240** between them.

That is not a defect in the linter; it is the reason ai-sniffer ships a reviewer
prompt at all, and it now has a number per habit instead of an argument. The same
650 drafts are what the model reviewers should be run against next, which turns
"Sonnet caught 35 to 41 of 62" into a statement about which habits those were.

`generic-detail` is 50 rather than 60 because one post contains no figure with a
noun after it for the injector to replace. That absence is visible in the table
instead of hidden in a percentage.

> **Superseded twice, 2026-09-16.** The first run used three posts from
> `pavanrao.github.io` before Pavan confirmed they were model-written (§2): 280
> injections, 111 quoted, falling to 107 once the baseline subtraction was added.
> The second used three Willison posts only: 320 injections, 129 quoted, with a
> 56-finding baseline over 4,695 words. Widening to four authors changed the
> proportions — `hedge` fell from 21/30 to 30/60 and `dramatic-beat` rose from 21/30
> to 44/60 — and left the conclusion where it was: the rhetorical shapes stay at or
> near zero.

### 5c. The same drafts, reviewed by a model

The point of §5b is not that the linter is weak. It is that the habits split into two
kinds, and the second kind needs a reader. So the same injected drafts went to the
Sonnet reviewer that ai-sniffer ships, run as a Claude Code subagent because
`ai-sniffer review` needs an API key and this account has no credits.

26 drafts, 283 injections, plus a separate review of each untouched post whose
findings are discounted as in §5a. Counts differ from §5b because a session limit
ended the run with four drafts unreviewed.

| habit | injected | model caught | model named | linter, for comparison |
| --- | --- | --- | --- | --- |
| triad | 28 | **28** | 28 | 1 of 60 |
| restatement | 26 | **26** | 26 | 3 of 60 |
| fragment | 26 | **26** | 24 | 7 of 60 |
| closer | 26 | **25** | 21 | 0 of 60 |
| reader-instruction | 26 | 25 | 25 | 60 of 60 |
| emphasis-word | 28 | 25 | 25 | 60 of 60 |
| cliche-emphasis | 26 | 24 | 24 | 13 of 60 |
| antithesis | 25 | **23** | 21 | 0 of 60 |
| generic-detail | 21 | 13 | 4 | 12 of 50 |
| dramatic-beat | 25 | **5** | 3 | 44 of 60 |
| hedge | 26 | **4** | 4 | 30 of 60 |
| **total** | **283** | **224** | **205** | |

**The two detectors are close to complementary.** The four habits the linter cannot
see at all — antithesis, closer, triad, restatement — the model catches 102 times out
of 105. The two the linter is best at, hedge and dramatic-beat, the model catches 9
times out of 51. Neither is a better version of the other, and a tool that
reported one number from both would be adding two unrelated error sources.

**Caught is not the same as named.** `generic-detail` is quoted 13 times and called
`generic-detail` only 4 of them; the model finds the vague passage and files it under
another habit. A per-habit claim therefore has to say which column it means.

### 5d. Three things wrong with the run above

**One reviewer used the linter.** The prompt did not forbid it, and the agent handling
five drafts said it ran `ai-sniffer check --json` first "as a hint" for the
linter-countable habits. That breaks the independence the comparison rests on. The
re-run without it was killed by the session limit, so the effect was measured by
dropping those five drafts instead: 185 of 228 against 224 of 283, and every
linter-countable habit within a few points — hedge 14% against 15%, emphasis-word 87%
against 89%, reader-instruction 95% against 96%. The contamination is real and its
effect is not detectable at this sample size. The prompt now forbids it.

**The injected habits are conspicuous.** Two reviewers, unprompted, described them as
nonsensical or ungrammatical: a triad whose three items are an odd word list, a
verbless "Two Ns, both familiar" tag, insertions that "often made ungrammatical by the
insertion", which is why one rated them all high severity. So part of what the model
is detecting is *damage*, not *habit*, and the recall figures above overstate what it
would do against the same habits written fluently. This is §2's limit arriving with
evidence: a template on demand is not a model left alone. It does not rescue the
linter, which scores near zero on those same conspicuous insertions.

**Four drafts are missing**, two Starburst and two Pavlo, because the run hit the
session limit. Per-habit counts of 25 to 28 rather than a flat 30 are that, not a
property of the corpus.

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
