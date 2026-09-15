# 012 — `ai-sniffer` (#218): the habits in agent-written prose

**Status:** built; eval scored against unreviewed labels · **Date:** 2026-09-14, results 2026-09-15

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
The core's default model, `ollama/llama3.1`, doesn't count as configured, so a machine
without Ollama gets that message rather than a failed connection. A reply without a
parseable JSON block exits `3` and prints the start of the reply. The prompt ships
inside the wheel as well, so an install outside the repo reads the same file.
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
writer, which is the open question the eval exists to answer. The linter's word lists
were written after the held-out labels existed, by the same person who wrote the
labels; each list is built by category (quantifier hedges, generic plurals,
sentence-initial imperatives) rather than from remembered phrases, but the linter's
held-out recall on word-level habits is still likely to be optimistic.

**A side effect worth having.** The two held-out posts are the ones due for a rewrite.
Their findings drive that rewrite, and the rewritten versions become clean drafts for
the next run of this eval.

## 4a · Results (2026-09-15, provisional)

**Provisional.** Scored against the labels at `7562e47`, before Pavan's review. Every
unmarked label counts as keep. These numbers get rescored from the saved runs once the
review is done, and both versions will be reported.

**What ran.** Prompt `5e3bb93`, labels `7562e47`, scoring `6123579`. Four model setups
ran three times each on six drafts as Claude Code subagents: 72 runs, with Haiku and
Sonnet requested by alias (see `eval/runs/manifest.json` for the caveat on exact
versions). All 72 replies parsed. Each run read neutral copies named `draft-1` to
`draft-6`. An audit of all 72 transcripts found 281 tool calls, every one a Read or
Write on that run's own listed files. The linter-alone setup is deterministic and ran
once.

**Recall and false alarms**, as the lowest and highest of three runs:

| Setup | Held-out, of 63 | Development, of 57 | Clean residuals, of 13 | False alarms on clean drafts |
| --- | --- | --- | --- | --- |
| Linter alone | 10 | 10 | 1 | 15 |
| Haiku | 7–10 | 19–23 | 3–6 | 5–8 |
| Haiku + linter report | 7–12 | 14–20 | 4–5 | 6–14 |
| Sonnet | 36–43 | 37–39 | 10–13 | 15–22 |
| Sonnet + linter report | 33–41 | 35–39 | 9–11 | 12–16 |

**Per held-out draft**, caught in each of the three runs:

| Setup | *Double-Entry*, of 38 | *Where the Cut Falls*, five sections, of 25 |
| --- | --- | --- |
| Linter alone | 8 | 2 |
| Haiku | 7, 7, 8 | 2, 0, 2 |
| Haiku + linter report | 6, 10, 9 | 1, 2, 1 |
| Sonnet | 26, 25, 31 | 15, 11, 12 |
| Sonnet + linter report | 30, 24, 32 | 8, 9, 9 |

**What the runs show.**

- Haiku reported few findings, 2 to 24 per draft. On held-out text it caught 7 to 10
  without the linter's report and 7 to 12 with it, against 10 for the linter alone. On *Where the Cut Falls* most of its findings fell outside
  the five scored sections (20, 18 and 6 set aside), so it caught 0 to 2 of the 25
  labelled habits there. The Haiku default in the agent file isn't supported by these
  runs.
- Sonnet caught 36 to 43 of the 63 held-out habits. Its development recall, 37 to 39
  of 57, is close to that, so the examples quoted from development drafts don't show
  up as a visible advantage.
- Giving Sonnet the linter's report didn't help. It caught fewer on *Where the Cut
  Falls* with the report (8 or 9) than without (11 to 15), and about the same on
  *Double-Entry*.
- Sonnet's false alarms, 15 to 22 across the two clean drafts, need reading before
  they're believed. *Which Protocol*'s rewrite has no counted labels, so every finding
  there is a false alarm by construction, and some will be habits the labels missed.
  They're on the review page as candidates.
- Model quotes were nearly always exact: 9 quotes across all 72 runs couldn't be found
  in their draft. The linter's "not in draft" counts come from its `CODE` placeholder
  for inline code, not from misquoting.
- Habit names agreed with the label on most catches (for Sonnet on *Double-Entry*, 20
  to 25 of 25 to 31 caught), which suggests the catalogue's names mean the same thing
  to the model and the labeller more often than not.

**Candidates.** 115 groups of unmatched findings from the model runs, including clean-
draft false alarms: 25 on *Double-Entry*, 6 on *Where the Cut Falls*, 27 on the
development drafts and 57 on the clean drafts. Accepted ones become labels with
`source: model`, and recall is reported with and without them.

**Not yet shown.** Whether a different prompt would lift Haiku, since only one prompt
was tested. Whether any of this holds for writers other than the two posts' author and
the model that helped draft them.

## 5 · Keeping the labels current

*Added 2026-09-15.* The labels will change after the first eval: Pavan's marks from the
review page, drafts added later, and habits a model finds that nobody labelled. Each
of those needs a way back into the labels that can't quietly damage the eval. Each is
one script under `tools/ai-sniffer/eval/`, with no framework around them.

**Stable ids.** A label's id is stored with it and never computed from its position. A
new label takes the next unused number for its draft, so a label added at line 40
can be `heldout-double-entry-48`. A dropped label's id is retired, never reused. The
page stores marks by id, so this is what keeps a mark on the quote it was made on.
The label table moves from Python tuples in `build_labels.py` to
`eval/labels.jsonl`, one label per line, so a script can edit it. The 165 existing ids
don't change, so marks already made stay attached.

**The review page lives in the repo.** `eval/review/build_page.py` renders the page from
`labels.json` and the pinned drafts, and it's republished to the same URL. Marks made
on earlier versions carry over, because they're keyed by id.

**Applying marks.** Claude saves the page's database as JSON (`read_db` with an output
directory) and `eval/apply_marks.py` applies it to `labels.jsonl`:

| Mark | What happens to the label |
| --- | --- |
| keep | marked reviewed |
| change | new habit or severity; the old values stay on the label under `was` |
| drop | stays in the file as `dropped`, excluded from scoring |
| no mark | left as it is, and counts as keep |
| missed habit | becomes a new label with the next id, once its quote is found exactly once |

Notes are kept on the label. A quote a note says is too long or too short is fixed by
hand, keeping the id. Then `labels.json` is rebuilt and scores are recomputed from the
saved findings, with no new model runs.

**Adding a draft.** Copy it into `eval/drafts/` with its role as the filename prefix,
and add it to `eval/drafts.json` with the commit it came from. A held-out draft is
labelled before any model sees it. The build fails for a draft with no role, and for a
label outside a draft's scored sections. Then the page is rebuilt and republished.

**Refreshing the prompt.** Only development drafts can change the reviewer prompt.
`eval/check_prompt.py`, run as a test, fails if an example isn't in a development draft,
if a phrase the prompt quotes appears in a held-out or clean draft, or if the catalogue's
habit names differ from the labels'. A single quoted word is exempt, since words like
"exactly" are in every draft and the emphasis-word entry has to name them. The check
sees whole quoted phrases only. A shorter phrase inside a development example can still
appear in scored text: the cliche-emphasis example ends in "the whole point", which
also occurs in *Where the Cut Falls*. On its first run the check caught three phrases
in habit definitions that occurred in held-out drafts, and they were reworded. Label changes on held-out drafts never reach the prompt; a held-out draft
that's wanted as prompt material moves to development, and a new held-out draft is
labelled to replace it. A prompt change means new model runs. A label change only
means rescoring.

**Candidate labels.** Scoring already lists findings on development and held-out drafts
that match no label. `eval/candidates.py` puts them on the review page as candidates,
with the setups that raised them, for Pavan to accept or reject. An accepted candidate
becomes a label with `source` set to `model`, and a hand-written one has `source` set
to `hand`. Recall is reported with and without model-sourced labels, since a label
that came from a model's finding flatters that model.

## 6 · Where it lives

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
   the rest, see Labels above.)*
2. Stable ids, and the label table moved to `labels.jsonl`. *(Steps 2–4 added
   2026-09-15.)*
3. The review page builder, in the repo.
4. `apply_marks.py`, and the procedure for adding a draft.
5. Linter, test-first.
6. Reviewer prompt, with examples quoted from the development drafts only, and the
   check that enforces it.
7. `review` command, test-first against a fake provider.
8. Eval runs and scoring, then candidate labels.
9. Design record, evidence card, #218 built.
10. The two `CLAUDE.md` changes.
11. Account-level install, **after a yes**.
12. The post. If data-tools is still private when it's ready, ai-sniffer moves to its
    own public repository first, so the post can link to its code.

The branch stacks on `worktree-discover-probe` (PR #25), since it continues that
branch's doc and iteration numbering. It rebases onto `main` once #25 merges.
