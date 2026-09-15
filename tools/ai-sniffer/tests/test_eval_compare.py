"""Other linters on our drafts: one input for every tool, and each tool's output read faithfully."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "compare"


@pytest.fixture
def compare(eval_script):
    return eval_script("compare/run_linters")


def text(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def quotes(findings):
    return [(f["line"], f["quote"]) for f in findings]


def test_slopless_quotes_come_from_the_character_range(compare):
    found = compare.ADAPTERS["slopless"](text("slopless.json"), text("sample.md"))

    assert quotes(found) == [(3, "tapestry")]
    assert found[0]["rule"] == "slopless/prohibited-words"


def test_wsc_reports_every_issue_category(compare):
    found = compare.ADAPTERS["wsc"](text("wsc.json"), text("sample.md"))

    assert quotes(found) == [(3, "delves"), (3, "rich tapestry")]
    assert {f["rule"] for f in found} == {"aiTells"}


def test_slop_uses_the_matched_text(compare):
    found = compare.ADAPTERS["slop"](text("slop.json"), text("sample.md"))

    assert (3, "not a bug, but a") in quotes(found)
    assert all(f["rule"] for f in found)


def test_vale_uses_each_alert_match(compare):
    found = compare.ADAPTERS["vale"](text("vale.json"), text("sample.md"))

    assert (3, "delves") in quotes(found) and (3, "rich tapestry") in quotes(found)


def test_slopscore_uses_evidence_spans_and_places_them_by_character(compare):
    found = compare.ADAPTERS["slopscore"](text("slopscore.json"), text("sample.md"))

    assert (3, "It didn't degrade.") in [(line, q.strip()) for line, q in quotes(found)]
    assert len(found) == len(json.loads(text("slopscore.json"))["evidence"])


def test_slop_lint_text_output_is_parsed_line_by_line(compare):
    found = compare.ADAPTERS["slop-lint"](text("slop-lint.txt"), text("sample.md"))

    assert (3, "delves") in quotes(found) and (3, "tapestry") in quotes(found)
    assert len(found) == 4


def test_the_markdown_view_keeps_each_paragraph_on_its_source_line_with_code_as_text(
    compare, tmp_path
):
    page = tmp_path / "post.html"
    page.write_text(
        "<html><head><style>p{}</style></head><body>\n"
        "<h2>Where it broke</h2>\n"
        "<p>It ran <code>uv sync</code>\nand stopped.</p>\n"
        "<p>Then it collapsed.</p>\n"
        "</body></html>\n"
    )

    lines = compare.markdown_view(page).split("\n")

    assert lines[1] == "## Where it broke"
    assert lines[2] == "It ran uv sync and stopped."
    assert lines[4] == "Then it collapsed."
    assert "style" not in "".join(lines)


def test_findings_are_written_as_a_reply_the_scorer_reads(compare, eval_script, tmp_path):
    out = tmp_path / "run-1.md"
    compare.write_run(out, [{"line": 3, "quote": "delves", "rule": "ai-tells.Vocab"}])

    findings, ok = eval_script("score").read_run(out)

    assert ok and findings[0]["quote"] == "delves" and findings[0]["line"] == 3


def test_wsc_categories_name_their_text_differently_and_long_sentences_are_sliced(compare):
    source = "Intro. Separate\nconnections matter more than they look here. Just that."
    output = json.dumps([{"file": "x.md", "issues": {
        "weaselWords": [{"word": "Just", "index": 61, "length": 4}],
        "passiveVoice": [{"phrase": "matter more", "index": 28, "length": 11}],
        "longSentences": [{"sentence": "Separate\\nconnections matter...", "wordCount": 35,
                           "index": 7, "length": 53}],
    }}])  # fmt: skip

    found = compare.ADAPTERS["wsc"](output, source)

    assert quotes(found) == [
        (2, "Just"),
        (2, "matter more"),
        (1, "Separate\nconnections matter more than they look here."),
    ]
