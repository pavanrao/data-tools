# ai-sniffer eval

What the reviewer is scored against, and the scripts that keep it current. The design
and the reasons behind these rules are in [docs/012](../../../docs/012_ai-sniffer.md).

| File | What it is |
| --- | --- |
| `drafts/` | pinned copies of the drafts, named by role: `dev-`, `heldout-`, `clean-` |
| `drafts.json` | each draft's role, the commit it came from, and any scored line ranges |
| `labels.jsonl` | the labels, one per line; the only label file edited by hand |
| `labels.json`, `LABELS.md` | generated from the two above by `build_labels.py` and `render_labels.py` |
| `review/build_page.py` | builds the review page from `labels.json` |
| `apply_marks.py` | applies marks from the review page to `labels.jsonl` |

All commands run from the repo root.

## Rebuilding after an edit

```bash
uv run python tools/ai-sniffer/eval/build_labels.py
uv run python tools/ai-sniffer/eval/render_labels.py
```

`build_labels.py` fails, and names the label, if a quote isn't found exactly once in
its draft, an id is reused or doesn't match its draft, a habit or severity isn't one
of the catalogue's, or a draft has no role.

## Reviewing labels

The page is published at <https://claude.ai/artifact/RtkkEpC5zUerUnktqtBihg>. Marks are
stored by label id in the page's own database.

1. `uv run python tools/ai-sniffer/eval/review/build_page.py`, then republish
   `review/label-proof.html` to the same URL. Marks already made carry over.
2. Mark labels on the page: keep, change, or drop, plus habits nobody labelled.
3. Ask Claude to save the page's `decisions` and `missed` collections with `read_db`
   into one directory.
4. `uv run python tools/ai-sniffer/eval/apply_marks.py DIR --dry-run` to see what would
   change, then again without `--dry-run`. Rerunning with a later export is safe;
   marks already applied don't apply twice.
5. Fix by hand anything it lists as skipped, and any quote a note says is the wrong
   length. Keep the label's id when you do.
6. Rebuild the page and republish.

A label change only means rescoring from the saved findings. It never means rerunning
a model.

## Adding a draft

1. Copy the draft into `drafts/` as `<role>-<name>.md` or `.html`, from a commit you
   can name.
2. Add it to `drafts.json` with its role (`development`, `held-out` or `clean`) and
   source, for example `"data-tools 372bb84"`.
3. Label it in `labels.jsonl`, numbering ids from `<role>-<name>-01`. A held-out draft
   is labelled before any model has seen it.
4. Rebuild the labels and the page, and republish.

## Rules that keep the numbers honest

- An id is never reused. A dropped label stays in `labels.jsonl` with
  `"status": "dropped"`, so its number stays taken.
- The reviewer prompt quotes examples from development drafts only. A held-out draft
  that's wanted as prompt material becomes a development draft, and a new held-out
  draft replaces it.
- Changing the prompt means new model runs. Changing labels means rescoring.
- A label accepted from a model's finding has `"source": "model"`, and recall is
  reported with and without those labels.
