"""Reading a draft: what counts as prose, where it splits, and which line it came from."""

from __future__ import annotations

from ai_sniffer.document import parse_html, parse_markdown, split_sentences


def sentences(doc):
    return [s for section in doc.sections for p in section.paragraphs for s in p.sentences]


def test_markdown_front_matter_code_and_tables_are_not_prose():
    doc = parse_markdown(
        "---\ntitle: A post\n---\n\nFirst line of prose.\n\n```python\nx = 1. Not prose.\n```\n\n"
        "| a | b |\n| --- | --- |\n| Not. | Prose. |\n\nLast line of prose.\n"
    )

    assert [s.text for s in sentences(doc)] == ["First line of prose.", "Last line of prose."]


def test_every_sentence_keeps_the_line_it_starts_on():
    doc = parse_markdown(
        "One sentence here. Another\nruns onto the next line.\n\nThird paragraph.\n"
    )

    assert [(s.line, s.text) for s in sentences(doc)] == [
        (1, "One sentence here."),
        (1, "Another runs onto the next line."),
        (4, "Third paragraph."),
    ]


def test_a_sentence_starting_after_a_line_break_gets_the_later_line():
    doc = parse_markdown("The first ends here.\nThe second starts here.\n")

    assert [s.line for s in sentences(doc)] == [1, 2]


def test_markdown_headings_start_sections():
    doc = parse_markdown("Intro.\n\n## Middle\n\nBody.\n\n## End\n\nOutro.\n")

    assert [s.heading for s in doc.sections] == ["", "Middle", "End"]
    assert [len(s.paragraphs) for s in doc.sections] == [1, 1, 1]


def test_markdown_inline_markup_is_stripped_and_code_becomes_a_placeholder():
    doc = parse_markdown("Run `uv sync` with **care**, see [the docs](https://x.y/z).\n")

    (sentence,) = sentences(doc)
    assert sentence.text == "Run CODE with care, see the docs."
    assert doc.code_spans == 1


def test_markdown_list_items_are_paragraphs_marked_as_list_items():
    doc = parse_markdown("Before the list.\n\n- first item\n- second item\n")

    kinds = [p.kind for p in doc.sections[0].paragraphs]
    assert kinds == ["prose", "item", "item"]


def test_html_skips_head_style_script_svg_pre_and_tables():
    doc = parse_html(
        "<html><head><title>Not prose.</title><style>p{}</style></head><body>\n"
        "<p>Kept.</p>\n<pre>Not. Prose.</pre>\n<svg><text>No.</text></svg>\n"
        "<table><tr><td>No.</td></tr></table>\n<script>var a = 'no.';</script>\n"
        "<p>Also kept.</p></body></html>\n"
    )

    assert [s.text for s in sentences(doc)] == ["Kept.", "Also kept."]


def test_html_line_numbers_come_from_the_source():
    doc = parse_html("<body>\n<h2>Heading</h2>\n<p>First\nsentence. Second\nsentence.</p>\n</body>")

    assert doc.sections[-1].heading == "Heading"
    assert [(s.line, s.text) for s in sentences(doc)] == [
        (3, "First sentence."),
        (4, "Second sentence."),
    ]


def test_html_entities_inline_tags_and_code():
    doc = parse_html("<p>It&rsquo;s <b>bold</b> and <code>a.b()</code> &mdash; fine.</p>")

    (sentence,) = sentences(doc)
    assert sentence.text == "It’s bold and CODE — fine."
    assert doc.code_spans == 1


def test_html_text_in_a_div_is_its_own_paragraph():
    doc = parse_html('<div class="note"><b>A limit.</b> Stated here.</div><p>Next.</p>')

    assert [[s.text for s in p.sentences] for p in doc.sections[0].paragraphs] == [
        ["A limit.", "Stated here."],
        ["Next."],
    ]


def test_splitting_leaves_abbreviations_and_decimals_alone():
    assert split_sentences("It took 3.5 s, e.g. on a laptop. Then it stopped.") == [
        (0, "It took 3.5 s, e.g. on a laptop."),
        (33, "Then it stopped."),
    ]


def test_an_abbreviation_before_a_capital_does_not_end_the_sentence():
    assert [
        t for _, t in split_sentences("Some formatters, e.g. Ruff, are fast. Others aren't.")
    ] == [
        "Some formatters, e.g. Ruff, are fast.",
        "Others aren't.",
    ]


def test_splitting_handles_closing_quotes_and_question_marks():
    assert [t for _, t in split_sentences('He asked "why?" Then left. Did it work? Yes.')] == [
        'He asked "why?"',
        "Then left.",
        "Did it work?",
        "Yes.",
    ]


def test_detects_format_by_extension(tmp_path):
    from ai_sniffer.document import read

    md = tmp_path / "a.md"
    md.write_text("Prose.\n")
    page = tmp_path / "a.html"
    page.write_text("<p>Prose.</p>")

    assert read(md).format == "markdown"
    assert read(page).format == "html"


def test_an_html_title_outside_head_is_not_prose():
    doc = parse_html("<title>Let the Title Say No</title>\n<p>Kept.</p>")

    assert [s.text for s in sentences(doc)] == ["Kept."]


def test_html_text_outside_a_p_is_a_block_not_an_author_paragraph():
    doc = parse_html('<div class="card">It is a write.</div><p>It collapsed.</p><li>An item.</li>')

    assert [p.kind for p in doc.sections[0].paragraphs] == ["block", "prose", "item"]
