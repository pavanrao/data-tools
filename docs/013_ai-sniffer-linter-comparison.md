# 013 — `ai-sniffer check` against other prose linters

**Status:** first run, on unreviewed labels · **Date:** 2026-09-15 · Post 1 of the
series planned under #218

## Question

Six open-source tools and `ai-sniffer check` find LLM-style habits in prose without a
model. Which of them catch the habits labelled in our six drafts, and at what cost in
false alarms?

## Setup

**Tools**, at the versions recorded in `tools/ai-sniffer/eval/runs/compare-manifest.json`:

| Tool | Version | Output read |
| --- | --- | --- |
| [slopless](https://github.com/berelevant-ai/slopless) | npm 0.2.38 | JSON, character range per finding |
| [wsc](https://github.com/theserverlessdev/wsc) | npm `wsc-lint` 1.3.0 | JSON by category: weasel words, passive voice, long sentences, nominalizations, hedging, adverbs, AI tells |
| [slop](https://github.com/bheijden/slop) | GitHub commit `9a6864e` | JSON, matched text |
| [vale-ai-tells](https://github.com/tbhb/vale-ai-tells) | v1.37.0 on Vale 3.21.0 | JSON, matched text |
| [slopscore](https://github.com/jman4162/slopscore) | pip `slopscore-lint` 0.14.0, rule-based core only | JSON evidence spans |
| [slop-lint](https://github.com/eric-sabe/slop-lint) | npm 0.8.0 | text, one line per finding |
| [sloplint](https://github.com/benjaminjackson/sloplint) | gem 0.7.0 on Homebrew Ruby 4.0.7 | JSON notes, matched excerpt |
| `ai-sniffer check` | this repo | its own JSON |

sloplint needs Ruby 3.3 or later, which macOS doesn't ship, so it ran later the same day
on Homebrew's Ruby, installed with Pavan's go-ahead.

**Input.** Markdown drafts as they are. HTML drafts as a Markdown view: each prose block
on the line it starts on in the source, headings as `##`, inline code kept as text, and
style, script, SVG and tables left out. `ai-sniffer check` scored the same on the
views as on the original files (10, 10 and 1 labels caught, 15 false alarms, 129
findings), so the views didn't change what a linter sees.

**Scoring.** `eval/score.py` unchanged, with one rule added before any of these tools
were scored: a quote contained in a label counts only if it has at least 4 characters
(`MIN_CONTAINED`). Without it a lone em dash, which several tools report, matched every
label containing a dash. Rescoring all earlier runs with the rule changed no count. Each
finding's quote is the text the tool matched, never the surrounding line or sentence;
wsc's long-sentence findings are the exception, since the tool matches the whole
sentence.

## Results

Labels are unreviewed, as in docs/012 §4a. Counts are high and medium labels caught;
each tool is deterministic and ran once.

| Tool | Held-out, of 63 | Development, of 57 | Clean residuals, of 13 | False alarms on clean drafts | Findings, all drafts |
| --- | --- | --- | --- | --- | --- |
| vale-ai-tells | 18 | 12 | 4 | 52 | 339 |
| wsc | 14 | 17 | 3 | 66 | 383 |
| slop | 13 | 8 | 1 | 24 | 177 |
| `ai-sniffer check` | 10 | 10 | 1 | 15 | 129 |
| slopless | 8 | 6 | 0 | 2 | 76 |
| slopscore | 2 | 4 | 1 | 7 | 44 |
| sloplint | 6 | 2 | 0 | 14 | 135 |
| slop-lint | 0 | 0 | 0 | 19 | 137 |
| *Sonnet reviewer, for reference* | *36–43* | *37–39* | *10–13* | *15–22* | |

**Which rules made the catches**, across all six drafts:

- **vale-ai-tells:** structural rules. Verb tricolons (5), parallel staccato (4),
  cataphoric forecasting (3) and contrastive formulas (3) caught antithesis, cliché
  emphasis, fragments, triads and closers.
- **wsc:** mostly its general style checks, not its AI tells. Weasel words (17), passive
  voice (6), long sentences (6) and adverbs (6). A long-sentence finding catches any label
  inside that sentence.
- **slop:** vocabulary and "is the whole / is the entire" rules, catching antithesis,
  cliché emphasis and closers.
- **`ai-sniffer check`:** hedges (7), one-sentence paragraphs (5), emphasis words (5)
  and reader instructions (4). It caught nothing structural, which is the job docs/012
  gives the reviewer.
- **slopless:** its negation-reframe rule (4) caught 8 antitheses, with 2 false alarms
  across both clean drafts, the fewest of any tool.
- **slopscore:** "generic sentence" evidence (6) and "X, not Y" (2). It abstains from
  scoring texts under about 300 words, and flags every sentence with no name or number.
- **sloplint:** structural rules only. "Is the whole X" (3), "no X, no Y" (2), "isn't X,
  it's Y" (2) and "sit with that" (1).
- **slop-lint:** 95 of its 137 findings are em dashes. The rest are double hyphens, curly
  quotes, "ecosystem" and "showcase". None of those are habits in our labels.

## What this does and doesn't show

- **No deterministic tool came close to the Sonnet reviewer.** The best, vale-ai-tells,
  caught 18 of 63 held-out habits.
- **Recall and false alarms trade off.** The two tools with the most catches also have
  the most false alarms (vale 52, wsc 66). slopless has the fewest false alarms, 2, for 8
  held-out catches.
- **Our labels are our home ground.** One labeller wrote them in ai-sniffer's categories,
  on drafts written by one author with Claude. Tools that flag em dashes, curly quotes or
  passive voice score zero for things we never labelled, whether or not readers would
  notice them. `ai-sniffer check` also had its word lists written by the person who wrote
  the labels (docs/012 §4). Post 3 of the series adds other writers' drafts and another
  labeller before any tool is called better.
- **False alarms on clean drafts overstate the noise.** Both clean drafts were rewritten
  to remove habits, and some flagged text will be habits the labels missed.

## Reproduce

Install the tools outside the repo (see `tools/ai-sniffer/eval/README.md`), then:

```bash
uv run python tools/ai-sniffer/eval/compare/run_linters.py --tools-dir DIR
uv run python tools/ai-sniffer/eval/score.py
```
