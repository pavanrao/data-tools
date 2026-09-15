"""The optional model path: one prompt, a fake provider, and a clear exit without a model."""

from __future__ import annotations

import json

import pytest
from ai_sniffer import review
from ai_sniffer.cli import main

DRAFT = "It didn't degrade. It collapsed.\n\nNote that this matters.\n"
REPLY = """```json
{"findings": [
  {"line": 1, "habit": "antithesis", "severity": "high", "quote": "It didn't degrade. It collapsed.",
   "why": "sets one idea up to knock it down"},
  {"line": 3, "habit": "reader-instruction", "severity": "medium", "quote": "Note that", "why": "tells the reader"},
  {"habit": "fragment", "quote": "no line"}
]}
```

Antithesis and reader instructions, both near the top.
"""  # noqa: E501


class FakeChat:
    def __init__(self, reply=REPLY):
        self.reply = reply
        self.prompts = []

    def complete(self, prompt, **opts):
        self.prompts.append(prompt)
        return self.reply


@pytest.fixture
def draft(tmp_path):
    path = tmp_path / "post.md"
    path.write_text(DRAFT)
    return path


@pytest.fixture
def fake(monkeypatch):
    chat = FakeChat()
    monkeypatch.setattr(review, "chat_provider", lambda model: chat)
    return chat


def test_the_prompt_is_the_agent_file_without_its_frontmatter():
    prompt = review.load_prompt()

    assert not prompt.startswith("---")
    assert "name: ai-sniffer" not in prompt
    assert prompt.startswith("More of what people read")
    assert "### antithesis" in prompt


def test_the_request_numbers_every_line_and_includes_the_linter_report(draft):
    request = review.build_request(review.load_prompt(), draft, linter_report={"findings": []})

    assert request.startswith(review.load_prompt())
    assert "1 | It didn't degrade. It collapsed." in request
    assert "3 | Note that this matters." in request
    assert '"findings": []' in request


def test_without_a_linter_report_the_request_says_so(draft):
    request = review.build_request(review.load_prompt(), draft, linter_report=None)

    assert "No linter report" in request


def test_the_reply_is_split_into_findings_invalid_entries_and_summary():
    findings, invalid, summary = review.parse_reply(REPLY)

    assert [(f["line"], f["habit"]) for f in findings] == [
        (1, "antithesis"),
        (3, "reader-instruction"),
    ]
    assert invalid == [{"habit": "fragment", "quote": "no line"}]
    assert summary == "Antithesis and reader instructions, both near the top."


def test_a_reply_without_json_is_an_error():
    with pytest.raises(review.ReplyError):
        review.parse_reply("I found some habits but won't say which.")


def test_review_prints_json_that_records_the_model(draft, fake, capsys):
    code = main(["review", "--json", "--model", "test/fake-1", str(draft)])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["model"] == "test/fake-1"
    assert payload["linter"] is True
    assert [f["habit"] for f in payload["findings"]] == ["antithesis", "reader-instruction"]
    assert payload["invalid"] == [{"habit": "fragment", "quote": "no line"}]
    assert payload["summary"].startswith("Antithesis")


def test_no_linter_sends_no_report(draft, fake):
    main(["review", "--no-linter", "--model", "test/fake-1", str(draft)])

    (prompt,) = fake.prompts
    assert "No linter report" in prompt
    assert '"contractions_per_100_words"' not in prompt


def test_with_the_linter_the_report_is_sent(draft, fake):
    main(["review", "--model", "test/fake-1", str(draft)])

    (prompt,) = fake.prompts
    assert '"contractions_per_100_words"' in prompt


def test_no_configured_model_exits_two_and_names_both_ways_to_get_a_review(
    draft, monkeypatch, tmp_path, capsys
):
    monkeypatch.delenv("DATA_TOOLS_CHAT_MODEL", raising=False)
    monkeypatch.chdir(tmp_path)  # no .env here

    code = main(["review", str(draft)])

    err = capsys.readouterr().err
    assert code == 2
    assert "DATA_TOOLS_CHAT_MODEL" in err
    assert "Claude Code agent" in err


def test_the_environment_variable_configures_the_model(draft, fake, monkeypatch, capsys):
    monkeypatch.setenv("DATA_TOOLS_CHAT_MODEL", "test/from-env")

    main(["review", "--json", str(draft)])

    assert json.loads(capsys.readouterr().out)["model"] == "test/from-env"


def test_a_backend_that_is_not_installed_exits_two(draft, monkeypatch, capsys):
    def unavailable(model):
        raise review.Unavailable("the llm extra isn't installed")

    monkeypatch.setattr(review, "chat_provider", unavailable)

    assert main(["review", "--model", "test/fake-1", str(draft)]) == 2
    assert "llm extra" in capsys.readouterr().err


def test_an_unparseable_reply_exits_three_and_shows_the_start_of_it(draft, monkeypatch, capsys):
    monkeypatch.setattr(review, "chat_provider", lambda model: FakeChat("no json here"))

    assert main(["review", "--model", "test/fake-1", str(draft)]) == 3
    assert "no json here" in capsys.readouterr().err


def test_the_text_report_lists_findings_by_line(draft, fake, capsys):
    main(["review", "--model", "test/fake-1", str(draft)])

    out = capsys.readouterr().out
    assert "model test/fake-1" in out
    assert "1  high  antithesis  It didn't degrade. It collapsed." in out


def test_an_unsupported_file_exits_two_before_any_model_call(tmp_path, fake):
    draft = tmp_path / "post.docx"
    draft.write_text("x")

    assert main(["review", "--no-linter", "--model", "test/fake-1", str(draft)]) == 2
    assert fake.prompts == []
