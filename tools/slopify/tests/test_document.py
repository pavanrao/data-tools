"""The parser has one job: find the prose, and leave everything else byte-identical."""

from slopify.document import Block, parse, render


def blocks_of_kind(text: str, kind: str) -> list[Block]:
    return [b for b in parse(text) if b.kind == kind]


def test_a_plain_paragraph_is_prose():
    doc = parse("The retriever ranks the chunks it was given.\n")
    assert [b.kind for b in doc] == ["prose"]
    assert doc[0].text == "The retriever ranks the chunks it was given."
    assert doc[0].line == 1


def test_wrapped_lines_join_into_one_paragraph():
    text = "The retriever ranks the chunks\nit was given, in order.\n"
    (block,) = parse(text)
    assert block.kind == "prose"
    assert block.text == "The retriever ranks the chunks it was given, in order."


def test_a_blank_line_separates_paragraphs():
    doc = parse("First paragraph here.\n\nSecond paragraph here.\n")
    assert [b.kind for b in doc] == ["prose", "blank", "prose"]
    assert doc[2].line == 3


def test_headings_lists_and_quotes_are_not_prose():
    text = (
        "## A heading\n\n- a list item\n- another item\n\n> a quoted line\n\n1. a numbered item\n"
    )
    assert blocks_of_kind(text, "prose") == []


def test_fenced_code_is_left_alone_even_when_it_reads_like_prose():
    text = "```text\nThis line is an ordinary English sentence.\n```\n"
    assert blocks_of_kind(text, "prose") == []
    assert render(parse(text)) == text


def test_an_indented_line_inside_a_fence_does_not_end_it():
    text = "```python\ndef f():\n    return 1\n\n\nx = 2\n```\n\nAfter the fence.\n"
    prose = blocks_of_kind(text, "prose")
    assert [b.text for b in prose] == ["After the fence."]
    assert render(parse(text)) == text


def test_front_matter_is_preserved_and_never_prose():
    text = (
        '---\ntitle: "A Post"\nsummary: "A sentence that looks like prose."\n---\n\nReal prose.\n'
    )
    prose = blocks_of_kind(text, "prose")
    assert [b.text for b in prose] == ["Real prose."]
    assert render(parse(text)) == text


def test_html_blocks_and_tables_are_preserved():
    text = (
        "<figure>\n  <svg></svg>\n</figure>\n\n"
        "| a | b |\n| --- | --- |\n| 1 | 2 |\n\nProse after.\n"
    )
    prose = blocks_of_kind(text, "prose")
    assert [b.text for b in prose] == ["Prose after."]
    assert render(parse(text)) == text


def test_render_round_trips_a_document_it_did_not_change():
    text = (
        "# Title\n\n"
        "A first paragraph, wrapped\nover two lines.\n\n"
        "```\ncode\n```\n\n"
        "- item\n\n"
        "A closing paragraph.\n"
    )
    assert render(parse(text)) == text


def test_render_rewraps_only_the_paragraphs_that_changed():
    text = "A first paragraph, wrapped\nover two lines.\n\nUntouched paragraph.\n"
    doc = parse(text)
    doc[0].text = "A first paragraph, wrapped over two lines, and now longer than it was."
    out = render(doc)
    assert "Untouched paragraph.\n" in out
    assert "A first paragraph, wrapped over two lines, and now longer than it was." in out


def test_line_numbers_follow_the_rendered_document():
    text = "One.\n\nTwo.\n\nThree.\n"
    doc = parse(text)
    doc[0].text = "One.\nstill one."  # a paragraph that grows by a line
    render(doc)
    assert [b.line for b in doc if b.kind == "prose"] == [1, 4, 6]
