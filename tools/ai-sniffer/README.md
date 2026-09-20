# ai-sniffer

Find the habits that make prose read as machine-written, and quote each one, so
whoever has the real details can fix them. It never says who wrote the text.

Two parts, split by what each is good at:

- **`ai-sniffer check`** counts what a pattern can find. It uses only the standard
  library, runs instantly, and gives the same answer every time.
- **The reviewer**, a prompt run by a model, looks at structure a pattern can't
  see: antithesis split across sentences, verbless fragments, section endings built
  to land a point. The prompt is [agent/ai-sniffer.md](agent/ai-sniffer.md), which
  is also a Claude Code agent file, and `ai-sniffer review` runs the same file through
  any model you configure.

## Install

In the repo:

```bash
uv sync --all-extras && uv run ai-sniffer check post.md
```

Account level, so `ai-sniffer` works from any directory and tracks this checkout:

```bash
# the linter alone, no dependencies
uv tool install --editable tools/ai-sniffer

# with the model layer, so `review` can call a model
uv tool install --force --editable tools/ai-sniffer \
  --with "data-tools-core[llm] @ file://$PWD/shared/data-tools-core"

# the agent, for Claude Code
ln -sf "$PWD/tools/ai-sniffer/agent/ai-sniffer.md" ~/.claude/agents/ai-sniffer.md
```

`--with` names the shared library by path because `uv tool install` can't follow the
workspace source; without it the install fails with "URL dependencies must be expressed
as direct requirements". The symlink points at this checkout, so move it if the
directory does. Whether Claude Code loads an agent through a symlink is unverified:
check that `ai-sniffer` appears in a new session, and copy the file instead if it
doesn't.

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

## `ai-sniffer review`

```bash
DATA_TOOLS_CHAT_MODEL=anthropic/claude-haiku-4-5-20251001 DATA_TOOLS_API_KEY=... \
  ai-sniffer review FILE [--json] [--model MODEL] [--no-linter]
```

Runs the linter, then sends the reviewer prompt, the linter's report and the numbered
draft to the model. Needs the `llm` extra (`uv sync --all-extras` in the repo). A local
model such as `ollama/llama3.1` needs no key. `--no-linter` leaves the report out, and
the model finds the word-level habits itself.

Output lists each finding with its line, severity, habit and quote, followed by the
model's short summary. It also records which model ran. It never contains rewritten
text.

| Exit | Meaning |
| --- | --- |
| `0` | reviewed |
| `2` | no model configured, the `llm` extra missing, the call failed, or the file couldn't be read |
| `3` | the model's reply had no usable JSON; the start of the reply is printed |

Without a configured model it doesn't fall back to a default: it exits `2` and names
both ways to get a review.

In Claude Code, the agent file does the same job with no key: copy
`agent/ai-sniffer.md` into `~/.claude/agents/` and ask for an ai-sniffer review.
Other agent tools can use the same prompt without its frontmatter; see
[docs/012](../../docs/012_ai-sniffer.md) §6 for what carries over.

## Eval

What it's measured against, and how the labels are kept current:
[eval/README.md](eval/README.md).
