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
about.

## 2. What it is not

**Injected habits are what a template produces on demand, not what a model
produces when left alone.** This limit is the reason the numbers below are a
diagnostic and never the headline. A detector could match every template here by
memorising "Note that" and still miss every real draft; ai-sniffer's hand-labelled
held-out numbers remain the claim, and these sit underneath them explaining *which
habits* those numbers are made of.

**Source text matters.** Inject into prose no model wrote. Injecting into an
AI-drafted post measures habits on top of habits, and the labels stop saying which
is which. The measurement in §5 uses three posts from `pavanrao.github.io` written
in January 2026, eight months before any of this tooling existed. They carry 0.4
to 2.6 contractions per 100 words and sentence-length variation of 0.51 to 0.72,
against 0.1 and 1.04 for the posts drafted with Claude — which is itself a small
piece of evidence that they are the human baseline they are being used as.

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

## 5. The first measurement: what `ai-sniffer check` can and cannot see

280 single-habit injections — 11 habits × 3 human-written posts × 10 seeds, minus
the combinations that found no site — scored against `ai-sniffer check`, the
model-free linter. **Quoted** means the linter's own quote overlaps the injected
one. **On line** is the generous reading: any finding within one line of the
injection, which credits coincidence and is reported so the strict number can be
read against it.

| habit | injected | quoted | on line |
| --- | --- | --- | --- |
| reader-instruction | 30 | 30 | 30 |
| emphasis-word | 20 | 20 | 20 |
| dramatic-beat | 30 | 21 | 23 |
| hedge | 20 | 17 | 17 |
| cliche-emphasis | 30 | 14 | 16 |
| generic-detail | 10 | 7 | 10 |
| fragment | 30 | 1 | 3 |
| restatement | 30 | 1 | 1 |
| antithesis | 20 | 0 | 2 |
| closer | 30 | 0 | 3 |
| triad | 30 | 0 | 7 |
| **total** | **280** | **111** | **132** |

The line this draws is the one the tool was built to draw, and it is sharper than
the overall figure in [docs/012](012_ai-sniffer.md) §4 could ever be. The linter is
at or near perfect on the habits that are a word list — an opener it can match, an
intensifier, a softened universal — and at or near zero on every habit that is a
*shape*: antithesis, closer, triad. Those three are 0 of 80. `fragment` at 1 of 30
and `restatement` at 1 of 30 are the same story.

This is not a defect in the linter. It is the reason ai-sniffer ships a reviewer
prompt at all, and it now has a number attached per habit instead of an argument.
The same 280 drafts are what the model reviewers should be run against next, which
turns "Sonnet caught 35 to 41 of 62" into a statement about which habits those were.

Two counts are lower than 30 because the sources offered no site: `antithesis`
needs a copula with a subject that is a thing, and `generic-detail` needs a figure
with a noun after it. Those absences are visible in the table rather than hidden
in a percentage.

## 6. Where it fits

Before post 3 of the [#218 series](../IDEAS.md), whose comparison it strengthens:
the market comparison can now report per-habit recall for every tool in
[docs/013](013_ai-sniffer-linter-comparison.md) instead of one number each. The
demo it makes possible needs no model — one human paragraph, one slopped paragraph,
and the linter's output under each.

```bash
make demo-slopify SLOPIFY_DRAFT=path/to/your-own-writing.md
```

There is no default and no sample corpus, for the reason in §2: the repository
holds no prose that no model touched. Shipping a sample would invite the mistake
that section warns about, so the path is required and the target refuses without
it.

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
