"""Manufacturing gold spans, and refusing the ones that cannot be verified.

Every test injects a fake chat provider. The suite needs no model and no network
(CONVENTIONS rule 6), and more usefully: with a scripted reply, "should this
question survive?" has a right answer, which is the only way to test a discard
path deliberately.
"""

from __future__ import annotations

import json

import pytest
from chunking_lab.annotate import MAX_EXCERPTS, PROMPT, Yield, annotate

DOC = (
    "# Escalation Policy\n\n"
    "Incidents are triaged by the on-call engineer within fifteen minutes.\n\n"
    "An incident is escalated when it has been open for four hours.\n\n"
    "Escalation is approved by the duty director, and by nobody else.\n"
)


class Scripted:
    """A chat provider that replies from a list, so each reply is a test case."""

    def __init__(self, *replies: str) -> None:
        self.replies = list(replies)
        self.prompts: list[str] = []

    def complete(self, prompt: str, **_: object) -> str:
        self.prompts.append(prompt)
        return self.replies[(len(self.prompts) - 1) % len(self.replies)]


def _reply(question: str, *excerpts: str) -> str:
    return json.dumps({"question": question, "excerpts": list(excerpts)})


# --------------------------------------------------------------- the happy path


def test_a_verifiable_question_is_kept_with_exact_offsets():
    provider = Scripted(_reply("When is an incident escalated?", "open for four hours"))
    corpus, produced = annotate("policy.md", DOC, provider, count=1)

    (question,) = corpus.questions
    (start, end) = question.gold[0]
    assert DOC[start:end] == "open for four hours"
    assert produced.kept == 1 and produced.asked == 1


def test_several_excerpts_become_several_spans():
    provider = Scripted(
        _reply("Who approves and when?", "open for four hours", "approved by the duty director")
    )
    corpus, _ = annotate("policy.md", DOC, provider, count=1)
    (question,) = corpus.questions
    assert len(question.gold) == 2
    assert all(DOC[a:b].strip() for a, b in question.gold)


def test_the_prompt_forbids_referring_to_the_excerpt():
    """A question phrased as "what does the passage say" is useless in a corpus --
    nobody searching a document collection writes that."""
    provider = Scripted(_reply("q", "open for four hours"))
    annotate("policy.md", DOC, provider, count=1)
    assert "would never phrase it that way" in provider.prompts[0]
    assert "VERBATIM" in provider.prompts[0]


# ------------------------------------------------------------ the discard paths


def test_an_invented_quote_is_discarded_not_approximated():
    """The whole design: no gold span beats a wrong one.

    A wrong span scores every strategy against the wrong text, and nothing
    downstream can detect it.
    """
    provider = Scripted(_reply("What is the SLA?", "resolved within three business days"))
    corpus, produced = annotate("policy.md", DOC, provider, count=1)

    assert corpus.questions == ()
    assert produced.kept == 0 and produced.unlocatable == 1


def test_one_bad_excerpt_discards_the_whole_question():
    """Partial ground truth is still wrong ground truth."""
    provider = Scripted(_reply("q", "open for four hours", "a fact that is not in the document"))
    _, produced = annotate("policy.md", DOC, provider, count=1)
    assert produced.kept == 0 and produced.unlocatable == 1


def test_unreadable_json_is_discarded():
    _, produced = annotate("policy.md", DOC, Scripted("I'm afraid I can't do that."), count=1)
    assert produced.kept == 0 and produced.malformed == 1


def test_json_wrapped_in_a_code_fence_is_still_read():
    """Models fence their JSON constantly; refusing that would discard good work."""
    body = _reply("When is it escalated?", "open for four hours")
    provider = Scripted(f"```json\n{body}\n```")
    _, produced = annotate("policy.md", DOC, provider, count=1)
    assert produced.kept == 1


def test_a_reply_missing_its_excerpts_is_discarded():
    provider = Scripted(json.dumps({"question": "What is the threshold?"}))
    _, produced = annotate("policy.md", DOC, provider, count=1)
    assert produced.kept == 0 and produced.malformed == 1


def test_a_provider_that_raises_costs_one_question_not_the_run():
    class Broken:
        def complete(self, prompt, **_):
            raise RuntimeError("connection reset")

    _, produced = annotate("policy.md", DOC, Broken(), count=3)
    assert produced.asked == 3 and produced.kept == 0


def test_excerpts_beyond_the_cap_are_dropped():
    provider = Scripted(_reply("q", *["open for four hours"] * (MAX_EXCERPTS + 2)))
    corpus, _ = annotate("policy.md", DOC, provider, count=1)
    assert len(corpus.questions[0].gold) <= MAX_EXCERPTS


# ------------------------------------------------------------------- the yield


def test_a_weak_model_produces_less_ground_truth_not_wrong_ground_truth():
    """C9's inversion, stated as a test.

    Two of four replies quote text that is not there. The survivors are still
    exactly right; the loss shows up as a yield.
    """
    good = _reply("When is an incident escalated?", "open for four hours")
    bad = _reply("What is the SLA?", "resolved within three business days")
    corpus, produced = annotate("policy.md", DOC, Scripted(good, bad), count=4)

    assert produced.asked == 4
    assert produced.kept == 2
    assert produced.rate == pytest.approx(0.5)
    for question in corpus.questions:
        for start, end in question.gold:
            assert DOC[start:end] == "open for four hours"


def test_the_yield_says_why_not_only_how_much():
    provider = Scripted("not json at all")
    _, produced = annotate("policy.md", DOC, provider, count=2)
    assert "not usable JSON" in produced.report()


def test_a_low_yield_is_called_out_explicitly():
    good = _reply("q", "open for four hours")
    bad = _reply("q", "text that does not appear")
    _, produced = annotate("policy.md", DOC, Scripted(bad, bad, bad, good), count=4)
    assert produced.rate < 0.5
    assert "under half survived" in produced.report()
    assert "still verified" in produced.report(), "must not imply the kept ones are suspect"


def test_the_yield_records_how_each_excerpt_was_located():
    """A corpus built mostly from fuzzy matches is less trustworthy, and says so."""
    provider = Scripted(_reply("q", "open for four hours"))
    _, produced = annotate("policy.md", DOC, provider, count=1)
    assert produced.by_stage == {"exact": 1}


def test_an_empty_run_reports_a_zero_rate_rather_than_dividing_by_zero():
    assert Yield().rate == 0.0


# ------------------------------------------------------------------ determinism


def test_the_same_seed_samples_the_same_windows():
    long_doc = DOC * 200
    a = Scripted(_reply("q", "open for four hours"))
    b = Scripted(_reply("q", "open for four hours"))
    annotate("d.md", long_doc, a, count=3, seed=7)
    annotate("d.md", long_doc, b, count=3, seed=7)
    assert a.prompts == b.prompts


def test_a_different_seed_samples_different_windows():
    long_doc = DOC * 200
    a = Scripted(_reply("q", "open for four hours"))
    b = Scripted(_reply("q", "open for four hours"))
    annotate("d.md", long_doc, a, count=3, seed=1)
    annotate("d.md", long_doc, b, count=3, seed=2)
    assert a.prompts != b.prompts


def test_quotes_are_located_against_the_whole_document_not_the_window():
    """The offsets must address the document that will actually be chunked."""
    long_doc = ("filler paragraph. " * 400) + "\nThe retention period is seven years.\n"
    provider = Scripted(_reply("How long is data kept?", "The retention period is seven years."))
    corpus, produced = annotate("d.md", long_doc, provider, count=1, seed=0)
    if produced.kept:
        (start, end) = corpus.questions[0].gold[0]
        # A trailing full stop is stripped before locating, as the reference does.
        assert long_doc[start:end] == "The retention period is seven years"
        assert start > 1000, "located in the window rather than in the document"


def test_the_prompt_names_the_excerpt_cap_it_enforces():
    assert f"1 and {MAX_EXCERPTS}" in PROMPT.format(window="x", max_excerpts=MAX_EXCERPTS)


# ------------------------------------------------------- comparing models


def test_comparing_models_asks_every_model_the_same_questions(monkeypatch, tmp_path, capsys):
    """The comparison only means something if the windows are identical.

    Same seed, same documents, so the only thing varying is the model. If each
    model were asked about different passages, a yield difference could just be
    one model getting easier text.
    """
    from chunking_lab import cli

    document = tmp_path / "policy.md"
    document.write_text(DOC * 60)  # long enough that windows are sampled, not whole

    seen: dict[str, list[str]] = {}

    def fake_provider(model):
        provider = Scripted(_reply("q", "open for four hours"))
        seen[model] = provider.prompts
        return provider, model

    monkeypatch.setattr(cli, "_chat_provider", fake_provider)
    exit_code = cli.main(
        [
            "annotate",
            str(tmp_path),
            "--out",
            str(tmp_path / "out"),
            "--per-document",
            "3",
            "--seed",
            "11",
            "--model",
            "ollama/a",
            "--model",
            "ollama/b",
        ]
    )
    assert exit_code == 0
    assert seen["ollama/a"] == seen["ollama/b"], "models were asked about different windows"

    out = capsys.readouterr().out
    assert "ollama/a" in out and "ollama/b" in out
    assert "paraphrased" in out, "the dominant failure mode must be broken out"


def test_comparing_models_writes_nothing(monkeypatch, tmp_path):
    """It answers 'which model should I annotate with', not 'here is a corpus'."""
    from chunking_lab import cli

    (tmp_path / "policy.md").write_text(DOC)
    out_dir = tmp_path / "out"

    monkeypatch.setattr(
        cli, "_chat_provider", lambda m: (Scripted(_reply("q", "open for four hours")), m)
    )
    cli.main(
        [
            "annotate",
            str(tmp_path),
            "--out",
            str(out_dir),
            "--per-document",
            "1",
            "--model",
            "ollama/a",
            "--model",
            "ollama/b",
        ]
    )
    assert not out_dir.exists()


def test_a_single_model_still_writes_a_corpus(monkeypatch, tmp_path):
    from chunking_lab import cli

    (tmp_path / "policy.md").write_text(DOC)
    out_dir = tmp_path / "out"

    monkeypatch.setattr(
        cli, "_chat_provider", lambda m: (Scripted(_reply("q", "open for four hours")), m)
    )
    assert cli.main(["annotate", str(tmp_path), "--out", str(out_dir), "--per-document", "1"]) == 0
    assert (out_dir / "gold.jsonl").exists()
