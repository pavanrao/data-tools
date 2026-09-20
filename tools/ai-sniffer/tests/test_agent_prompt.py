"""The reviewer prompt: its catalogue matches the labels, and it never quotes scored text."""

from __future__ import annotations

import pytest


@pytest.fixture
def prompt_check(eval_script):
    return eval_script("check_prompt")


def test_the_catalogue_names_exactly_the_label_habits(prompt_check, eval_script):
    habits = eval_script("build_labels").HABITS

    assert prompt_check.catalogue_habits(prompt_check.AGENT.read_text(encoding="utf-8")) == set(
        habits
    )


def test_the_committed_prompt_passes_the_check(prompt_check):
    assert prompt_check.problems(prompt_check.AGENT.read_text(encoding="utf-8")) == []


def test_an_example_from_a_held_out_draft_is_refused(prompt_check, tmp_path):
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "dev-a.md").write_text("It wasn't slow. It was stuck.\n")
    (drafts / "heldout-b.md").write_text("The two are not big and small here.\n")
    meta = {"dev-a.md": {"role": "development"}, "heldout-b.md": {"role": "held-out"}}
    prompt = (
        "### antithesis\n\n"
        'Example: "It wasn\'t slow. It was stuck."\n'
        'Example: "The two are not big and small here."\n'
    )

    found = prompt_check.problems(prompt, meta=meta, drafts_dir=drafts, habits={"antithesis"})

    assert found == [
        "example isn't in any development draft: 'The two are not big and small here.'",
        "quoted text appears in heldout-b.md: 'The two are not big and small here.'",
    ]


def test_quoted_text_outside_examples_is_checked_too(prompt_check, tmp_path):
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "clean-c.md").write_text("Same idea, different engine.\n")
    meta = {"clean-c.md": {"role": "clean"}}
    prompt = '### fragment\n\nPhrases like "same idea, different engine" are the habit.\n'

    found = prompt_check.problems(prompt, meta=meta, drafts_dir=drafts, habits={"fragment"})

    assert found == ["quoted text appears in clean-c.md: 'same idea, different engine'"]


def test_a_missing_or_extra_catalogue_entry_is_a_problem(prompt_check, tmp_path):
    found = prompt_check.problems(
        "### antithesis\n### vibes\n", meta={}, drafts_dir=tmp_path, habits={"antithesis", "hedge"}
    )

    assert found == [
        "catalogue has no entry for: hedge",
        "catalogue entry isn't a label habit: vibes",
    ]


def test_a_single_quoted_word_is_vocabulary_but_any_quoted_phrase_is_checked(
    prompt_check, tmp_path
):
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "heldout-b.md").write_text("It was exactly right, note that.\n")
    meta = {"heldout-b.md": {"role": "held-out"}}
    prompt = '### emphasis-word\n\nWords like "exactly". Phrases like "note that".\n'

    found = prompt_check.problems(prompt, meta=meta, drafts_dir=drafts, habits={"emphasis-word"})

    assert found == ["quoted text appears in heldout-b.md: 'note that'"]


def test_a_quoted_phrase_wrapped_across_lines_is_checked(prompt_check, tmp_path):
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "clean-c.md").write_text("It was the key insight all along.\n")
    meta = {"clean-c.md": {"role": "clean"}}
    prompt = '### cliche-emphasis\n\nPhrases like "the key\ninsight" or "a short shelf life".\n'

    found = prompt_check.problems(prompt, meta=meta, drafts_dir=drafts, habits={"cliche-emphasis"})

    assert found == ["quoted text appears in clean-c.md: 'the key insight'"]
