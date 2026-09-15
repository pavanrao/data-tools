# 012 — `ai-sniffer` (#218): the habits in agent-written prose

**Status:** plan · **Date:** 2026-09-14

## Purpose

> More of what people read is now drafted by agents, and it carries habits readers
> learn to recognise, like recurring sentence shapes and paragraphs that end on a
> neat line. Once readers notice them they start skimming, and a well-researched
> piece gets skimmed along with everything else. This finds those habits in a draft
> and quotes each one, so whoever has the real details can fix them. Deciding who
> wrote the text is out of scope.

## Why a linter and an agent

Checking the MCP protocol post on 2026-09-14 settled this. The word-level check —
contraction rate, hedges, reader instructions, sentence-length variation — passed the
first draft, and the draft still read as generated. What it missed lived in structure:
antithesis split across two sentences, verbless fragments in threes, one-line
dramatic beats, section endings built to land a point. A pattern that reads one
sentence at a time can't see any of those.

So the work splits by what each part is good at. The **linter** counts what can be
counted, is free, and gives the same answer every time. The **reviewer**, a prompt
run by a model, gets the text and the linter's report and spends its judgement on
structure. Neither ever issues a verdict about authorship.

## Scope

**In:** the linter as a CLI; the reviewer prompt, usable as a Claude Code agent and
through the repo's model layer; an eval measuring what each catches; installation at
account level; a write-up.

**Out:** model-based surprisal scoring and the human-versus-generated corpus
comparison #218 first described, both possible later phases; automatic triggering
through hooks; any rewriting of the text by the reviewer.

## 1 · The linter: `ai-sniffer check`

Standard library only, so the base install has no dependencies at all.

**Input.** Markdown or HTML, chosen by extension. Code fences, tables, front matter
and HTML tags are removed before analysis, and inline code becomes a placeholder
token. Every finding keeps the line number from the original file.

| Signal | What it reports |
| --- | --- |
| Contraction rate | contractions per 100 words |
| Hedges | each hedge from a closed list, with its line |
| Emphasis words | each from a closed list such as `exactly`, `precisely` and `genuinely`, with its line |
| Reader instructions | each from a closed list such as `note that` and `keep in mind`, with its line |
| Sentence rhythm | mean length, coefficient of variation, and runs of similar-length sentences |
| One-sentence paragraphs | each, with its line |
| Repeated skeletons | sentences that reduce to the same closed-class skeleton once content words are removed |
| Concrete detail | digits, dates, quoted strings and code tokens per 100 words |
| Section closers | the last sentence of every section, extracted for the reviewer rather than judged |

**Output.** Findings with line, quoted text and signal name, plus the metrics and the
extracted closers. No score. `--json` for machines. Exit `0`; `--strict` exits `1`
when there's any finding, for CI; `2` when the input can't be read.

## 2 · The reviewer

One file, `tools/ai-sniffer/agent/ai-sniffer.md`. YAML frontmatter makes it a Claude
Code agent (`model: haiku`, tools `Read`, `Grep`, `Bash`); the body is the prompt.

The prompt carries the purpose statement, then a **catalogue of habits**. Each entry
has a definition and a real example quoted from one of our own drafts. For the
word-level habits the prompt says to use the linter's report when one is supplied, and
to check them itself when it isn't. The structural ones are always the reviewer's job:

- antithesis across two sentences ("It wasn't X. It was Y.")
- verbless parallel fragments ("Both A, both B, opposite C.")
- a short paragraph used as a dramatic beat
- a section ending built to land a point
- the same point made twice in adjacent sentences
- clichés, and emphasis like "the whole point"
- generic detail standing in for a real one ("the evidence looked solid")
- triads used as a habit rather than because there were three things

**Rules the prompt states.** Quote the exact text with its line. Give each finding a
severity: high, medium or low. A single natural use isn't a finding. Never write
replacement text. For generic detail, say the passage needs a real specific from the
author, and never propose one. Never comment on who wrote it.

**Output.** A JSON list of findings — line, habit, quote, severity, why — followed by
a short plain summary.

## 3 · The optional model path: `ai-sniffer review`

Runs the linter, then sends the same prompt, the report and the text through
`data_tools_core.llm`'s `ChatProvider`, behind the `llm` extra. The model comes from
`DATA_TOOLS_CHAT_MODEL`, so a hosted model such as
`anthropic/claude-haiku-4-5-20251001` uses a key from `DATA_TOOLS_API_KEY` or the
provider's own variable, and a local Ollama model needs no key.

Without the extra or a configured model it exits `2` and names both ways to get a
review — the Claude Code agent, or configuring a model. It never quietly falls back.
Output records which model ran (CONVENTIONS rule 2). The prompt is read from the
agent file with its frontmatter stripped, so there's one copy.

Tests inject a fake `ChatProvider`; nothing touches a network.

## 4 · The eval

**Three roles, kept apart.** The catalogue quotes real habits from our own drafts, so
scoring the reviewer only on those drafts would let it succeed by recognising the
quotes. The drafts are therefore split by what each is allowed to measure.

| Role | Draft | Commit | Used for |
| --- | --- | --- | --- |
| Development | *Let the Database Say No*, before rewrite | data-tools `372bb84` | catalogue examples; optimistic recall |
| Development | *Which Protocol Is Your MCP Server Speaking?*, before rewrite | site `cfa59de` | catalogue examples; optimistic recall |
| Held out | *Double-Entry for Documents* | data-tools `b265882` | honest recall; never quoted in the prompt |
| Held out | *Where the Cut Falls* | data-tools `b265882` | honest recall; the length test |
| Clean | *Let the Database Say No*, after rewrite | data-tools `138a26c` | false alarms |
| Clean | *Which Protocol Is Your MCP Server Speaking?*, after rewrite | site `2e91d3d` | false alarms |

The protocol post's later commit `901cbc9` is excluded, since it also removed a
section. Development and held-out recall are reported separately, and only the
held-out number is quoted as the result.

**Labels.** Every habit in all six drafts, by line, habit, severity and quote, in
`tools/ai-sniffer/eval/labels.json`, generated by `build_labels.py`, which fails unless
each quote occurs exactly once in its draft. `LABELS.md` is the same list rendered for
reading. The clean drafts get labels too: a rewrite can leave habits behind or add new
ones ("Same idea, different engine." first appears in the rewrite), and a flag on one of
those isn't a false alarm. *Where
the Cut Falls* runs to about 5,600 words and sixteen sections, so the models get the
whole post, which is what makes it a length test, but only sections 1, 4, 7, 10 and 13
are labelled and scored. Those were chosen here, before any run, and spread through
the post rather than taken from the start, where habits may cluster. Held-out labels
are written before any model sees either post. ~~**Pavan reviews all labels before
anything is scored**; until then they're one reader's judgement.~~ *(Changed
2026-09-15: the review runs alongside the build instead of blocking it.)* Pavan marks
each label keep, change or drop on a review page, and the marks are applied to
`build_labels.py` when he's done. Until then every unmarked label counts as keep, and
any score is reported as provisional against the labels at `bb882e0`. Model findings
are saved to disk, so applying the marks means rescoring, not rerunning. Both scores
get reported, along with whether he'd seen any findings before finishing his review,
since corrections made after seeing what a model caught can drift toward the model.

**Setups.** The linter alone; Haiku without the linter's report; Haiku with it; Sonnet
without; Sonnet with. Model setups run as subagents from a Claude Code session with the
model set per run, reading the prompt and draft from disk so the text never passes
through the orchestrating context. This measures the prompt, not whether Claude Code
loads the agent file; that's checked separately at install. Each model setup runs
**three times per draft**, since output varies between runs: four model setups, six
drafts, three runs, 72 in total.

**Severity.** `high` and `medium` labels count toward recall. `low` marks a use that
could be defended either way, so it's neutral: flagging it neither earns a catch nor
counts as a false alarm.

**Scoring.** A deterministic script. A finding matches a label when both are in the
same draft and, after whitespace and case are normalised, their quotes share a run of
at least 20 characters — or one contains the other, when a quote is shorter than that.
The habit name is compared separately, since categories blur. Unmatched findings on a
clean draft count as false alarms, and findings matching a `low` label are left out of
both counts. Unmatched findings elsewhere are listed for review,
because some will be real habits the labels missed. On *Where the Cut Falls*, findings
outside the five labelled sections are set aside, not scored.

**Reported as counts**, per LEARNINGS 8b: labelled habits caught out of the total, and
false alarms, as the lowest and highest across three runs, for each role. The result
goes in `evidence/ai-sniffer.jsonl`.

**Limits, stated in the write-up.** Four posts, two of them development text. One
labeller, who also did the two rewrites. A reviewer from the same model family as the
writer, which is the open question the eval exists to answer.

**A side effect worth having.** The two held-out posts are the ones due for a rewrite.
Their findings drive that rewrite, and the rewritten versions become clean drafts for
the next run of this eval.

## 5 · Where it lives

**In the repo:** `tools/ai-sniffer/` (linter, reviewer file, `review` command, eval),
this record, #218 marked built.

**At account level:** `uv tool install --editable tools/ai-sniffer`, so the command
works from any project and tracks the checkout; a symlink from `~/.claude/agents/`
to the reviewer file. Two things to verify first: that an editable tool install works
from inside the workspace, and that Claude Code loads an agent through a symlink. Both
change the machine's setup, so they happen only after a yes at that point.

**Conventions:** the writing table in `data-tools/CLAUDE.md` is replaced by a pointer
to the reviewer's catalogue, so there's a single definition. The site repo gets a
short `CLAUDE.md` saying to run ai-sniffer on posts before publishing.

**Write-up:** one post on the site, written last, and reviewed by ai-sniffer before
it's published.

## Build order

1. Labels, ~~then **stop for Pavan's review**~~. *(Moved first on 2026-09-14, was step 4:
   labelling the held-out posts before writing the prompt keeps the prompt from being
   shaped around them. The stop was lifted on 2026-09-15; the review runs alongside
   steps 2–5, see Labels above.)*
2. Linter, test-first.
3. Reviewer prompt, with examples quoted from the development drafts only.
4. `review` command, test-first against a fake provider.
5. Eval runs and scoring.
6. Design record, evidence card, #218 built.
7. The two `CLAUDE.md` changes.
8. Account-level install, **after a yes**.
9. The post.

The branch stacks on `worktree-discover-probe` (PR #25), since it continues that
branch's doc and iteration numbering. It rebases onto `main` once #25 merges.
