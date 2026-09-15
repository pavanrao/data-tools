"""The review page builder: every label shown in its own paragraph, and nothing escapes the page."""

from __future__ import annotations

import json

import pytest


@pytest.fixture
def page_script(eval_script):
    return eval_script("review/build_page")


def data(labels):
    roles = {"heldout-a.md": "held-out", "dev-b.html": "development"}
    drafts = {x["draft"]: {"role": roles[x["draft"]], "source": "t"} for x in labels}
    return {"drafts": drafts, "labels": labels}


def label(id, draft, quote, line):
    return {
        "id": id,
        "draft": draft,
        "line": line,
        "habit": "fragment",
        "severity": "high",
        "quote": quote,
        "source": "hand",
    }


def test_each_label_gets_its_paragraph_split_around_the_quote(page_script, workspace):
    out = page_script.with_context(
        data([label("heldout-a-01", "heldout-a.md", "It collapsed.", 5)]), workspace / "drafts"
    )

    (entry,) = out["labels"]
    assert (entry["before"], entry["match"], entry["after"]) == (
        "It didn't degrade. ",
        "It collapsed.",
        "",
    )


def test_quotes_in_headings_and_bare_divs_are_found(page_script, tmp_path):
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "dev-b.html").write_text(
        "<h2>It failed on my code first, which is the point</h2>\n"
        '<div class="note"><b>The limit worth stating.</b> These can tell you.</div>\n'
    )
    labels = [
        label("dev-b-01", "dev-b.html", "which is the point", 1),
        label("dev-b-02", "dev-b.html", "The limit worth stating.", 2),
    ]

    out = page_script.with_context(data(labels), drafts)

    assert [x["match"] for x in out["labels"]] == ["which is the point", "The limit worth stating."]
    assert out["labels"][1]["after"] == " These can tell you."


def test_the_section_heading_is_attached(page_script, tmp_path):
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "heldout-a.md").write_text("## Where it broke\n\nIt didn't degrade. It collapsed.\n")

    out = page_script.with_context(
        data([label("heldout-a-01", "heldout-a.md", "It collapsed.", 3)]), drafts
    )

    assert out["labels"][0]["heading"] == "Where it broke"


def test_a_quote_that_cannot_be_highlighted_fails_the_build(page_script, workspace):
    with pytest.raises(SystemExit, match="heldout-a-01"):
        page_script.with_context(
            data([label("heldout-a-01", "heldout-a.md", "Not there at all.", 5)]),
            workspace / "drafts",
        )


def test_the_page_embeds_the_data_without_breaking_out_of_its_script_tag(page_script):
    template = '<title>t</title><p>__COMMIT__</p><script type="application/json">__DATA__</script>'
    payload = {"labels": [{"quote": "</script><b>x</b>"}]}

    html = page_script.render(template, payload, commit="abc1234")

    assert "<p>abc1234</p>" in html
    assert html.count("</script>") == 1
    embedded = html.split('application/json">', 1)[1].rsplit("</script>", 1)[0]
    assert json.loads(embedded) == payload


def test_the_committed_template_has_both_placeholders(page_script):
    template = page_script.TEMPLATE.read_text(encoding="utf-8")

    assert "__DATA__" in template and "__COMMIT__" in template
    assert template.lstrip().startswith("<title>")
