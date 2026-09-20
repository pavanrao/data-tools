"""The driver's contract: the labels it writes must be findable in the text it wrote."""

import json

from slopify.document import parse, render
from slopify.inject import Label, flatten, slop

DRAFT = """# A heading

The retriever ranks every chunk against the question and returns the top few of
them. It is a simple component and it never changes between runs of the tool.

```text
this fenced line is not prose and must come through untouched
```

We measured 472 questions on the corpus and the score was 17.7 for that run. The
boundaries were fixed before the retriever ever saw them, so nothing it does can
move one.

| a | b |
| --- | --- |
| 1 | 2 |
"""


def test_every_label_quote_is_present_in_the_slopped_text():
    text, labels = slop(DRAFT, seed=11, count=4)
    assert labels
    flat = flatten(text)
    for label in labels:
        # normalised, because wrapping can put a line break inside a quote
        assert flatten(label.quote) in flat, f"{label.habit}: quote not in output"


def test_every_label_line_points_at_the_line_holding_the_quote():
    text, labels = slop(DRAFT, seed=5, count=4)
    lines = text.split("\n")
    for label in labels:
        window = flatten(" ".join(lines[label.line - 1 : label.line + 3]))
        head = " ".join(flatten(label.quote).split()[:4])
        assert head in window, f"{label.habit}: line {label.line} does not hold {head!r}"


def test_the_same_seed_gives_the_same_document():
    assert slop(DRAFT, seed=3, count=3) == slop(DRAFT, seed=3, count=3)


def test_a_different_seed_gives_a_different_document():
    assert slop(DRAFT, seed=3, count=3)[0] != slop(DRAFT, seed=4, count=3)[0]


def test_code_fences_and_tables_are_untouched():
    text, _ = slop(DRAFT, seed=9, count=6)
    assert "this fenced line is not prose and must come through untouched" in text
    assert "| --- | --- |" in text


def test_only_the_requested_habits_are_injected():
    _, labels = slop(DRAFT, seed=2, count=5, habits=["hedge"])
    assert {label.habit for label in labels} == {"hedge"}


def test_count_is_a_ceiling_not_a_promise():
    """One paragraph cannot absorb twenty habits and still read like a draft."""
    _, labels = slop("One short line of prose here, and nothing else at all.\n", seed=1, count=20)
    assert len(labels) <= 3


def test_labels_carry_the_seed_that_produced_them():
    _, labels = slop(DRAFT, seed=31, count=2)
    assert all(label.seed == 31 for label in labels)


def test_a_label_serialises_in_the_shape_the_eval_reads():
    _, labels = slop(DRAFT, seed=7, count=1)
    record = json.loads(labels[0].as_json("sample.md"))
    assert set(record) == {"id", "draft", "habit", "severity", "quote", "source", "seed", "line"}
    assert record["source"] == "injected"
    assert record["draft"] == "sample.md"
    assert record["id"].startswith("sample-")


def test_ids_are_unique_within_a_run():
    _, labels = slop(DRAFT, seed=13, count=5)
    ids = [json.loads(label.as_json("d.md"))["id"] for label in labels]
    assert len(set(ids)) == len(ids)


def test_an_unchanged_document_round_trips_when_nothing_is_injected():
    text, labels = slop(DRAFT, seed=1, count=0)
    assert labels == []
    assert text == render(parse(DRAFT))


def test_injections_are_spread_across_paragraphs_before_doubling_up():
    _, labels = slop(DRAFT, seed=17, count=2)
    assert len({label.paragraph for label in labels}) == 2


def test_label_is_hashable_and_comparable():
    a = Label("hedge", "almost every", 3, 0, 1)
    b = Label("hedge", "almost every", 3, 0, 1)
    assert a == b


def test_habits_are_spread_evenly_rather_than_picked_at_random():
    """Uneven cells make a per-habit score meaningless, so every habit takes a turn."""
    from collections import Counter

    long_draft = "\n\n".join(
        f"The retriever ranks every chunk against question {n} and returns the top few. "
        f"It is a simple component and it never changes between runs of the tool. "
        f"We measured 472 questions on the corpus and the score was 17.7 for that run."
        for n in range(12)
    )
    _, labels = slop(long_draft, seed=5, count=22)
    counts = Counter(label.habit for label in labels)
    assert len(counts) >= 8, f"only {len(counts)} habits used: {counts}"
    assert max(counts.values()) - min(counts.values()) <= 2, counts
