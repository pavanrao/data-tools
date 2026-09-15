# ai-sniffer

Find the habits that make prose read as machine-written, and quote each one, so
whoever has the real details can fix them. It never says who wrote the text.

Two parts, split by what each is good at:

- **`ai-sniffer check`** counts what a pattern can find. It uses only the standard
  library, runs instantly, and gives the same answer every time.
- **The reviewer**, a prompt run by a model, looks at structure a pattern can't
  see: antithesis split across sentences, verbless fragments, section endings built
  to land a point. *(Not built yet; see [docs/012](../../docs/012_ai-sniffer.md).)*

## Install

```bash
uv sync --all-extras && uv run ai-sniffer check post.md
```

## `ai-sniffer check`

```bash
ai-sniffer check FILE [--json] [--strict]
```

Reads Markdown or HTML, chosen by extension. Front matter, code, tables and markup
are dropped, and inline code is counted as detail and then read as the word `CODE`.
Every finding carries the source line it starts on.

| Signal | Reported as |
| --- | --- |
| `hedge` | hedged universals from a closed list: "almost every", "most people", "plenty of" |
| `emphasis-word` | intensifiers from a closed list: "exactly", "precisely", "genuinely" |
| `reader-instruction` | "note that", "keep in mind", and imperatives opening a sentence: "Consider", "Imagine" |
| `one-sentence-paragraph` | a paragraph of one sentence, unless it introduces a list or code |
| `even-rhythm` | four or more sentences in a row within three words of each other's length |
| `repeated-skeleton` | a sentence with the same function-word shape as one of the three before it |

Metrics, not findings: contractions per 100 words, sentence length mean and
variation, and concrete detail (numbers, dates, quoted strings, code) per 100 words.
The last sentence of each section is listed for a reader to judge.

A finding is a place to look. "Exactly" is sometimes the right word, so there's no
score.

| Exit | Meaning |
| --- | --- |
| `0` | checked |
| `1` | `--strict`, and there was at least one finding |
| `2` | the file couldn't be read, or isn't `.md` or `.html` |

## Eval

What it's measured against, and how the labels are kept current:
[eval/README.md](eval/README.md).
