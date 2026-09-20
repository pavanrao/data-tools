"""Every injector must change the text, and must be able to say it cannot.

The quote it returns is the contract with the eval: a detector is credited when it
quotes these words, so a quote that isn't in the output text is a bug that would
silently score every detector at zero.
"""

import random

import pytest
from slopify.habits import INJECTORS, Injection

PROSE = (
    "The retriever ranks every chunk against the question and returns the top few. "
    "It is a simple component and it never changes between runs. "
    "We measured 472 questions on the corpus and the score was 17.7 for the run."
)


def run(name: str, text: str = PROSE, seed: int = 7) -> Injection | None:
    return INJECTORS[name](text, random.Random(seed))


@pytest.mark.parametrize("name", sorted(INJECTORS))
def test_every_injector_changes_the_text_and_quotes_itself(name):
    result = run(name)
    assert result is not None, f"{name} found no site in the sample paragraph"
    assert result.text != PROSE
    assert result.quote in result.text, f"{name} quoted words that are not in its output"
    assert result.habit == name


@pytest.mark.parametrize("name", sorted(INJECTORS))
def test_every_injector_is_deterministic_for_a_seed(name):
    assert run(name, seed=3) == run(name, seed=3)


@pytest.mark.parametrize("name", sorted(INJECTORS))
def test_every_injector_declines_on_text_with_no_site(name):
    assert run(name, text="Go.") is None


def test_hedge_softens_a_universal():
    result = run("hedge", "The chunker drops every trailing paragraph it is given.")
    assert "almost every" in result.text
    assert result.quote == "almost every trailing"


def test_reader_instruction_prefixes_a_sentence():
    result = run("reader-instruction", "The boundaries are fixed before the question arrives.")
    assert result.text.startswith("Note that the boundaries")
    assert result.quote.startswith("Note that")


def test_emphasis_word_lands_after_a_copula():
    result = run("emphasis-word", "The ceiling is a property of the cuts.")
    assert " is exactly a" in result.text or " is precisely a" in result.text


def test_generic_detail_replaces_a_real_number():
    result = run("generic-detail", "We measured 472 questions and scored 17.7 on the corpus.")
    assert "472" not in result.text or "17.7" not in result.text
    assert result.quote in result.text


def test_antithesis_needs_a_copula_and_splits_the_claim():
    result = run("antithesis", "Precision omega is a ceiling on what any retriever could do.")
    assert result.text.count(".") > 1
    assert "isn't" in result.text or "is not" in result.text


def test_dramatic_beat_returns_a_paragraph_break():
    result = run("dramatic-beat", "One sentence here. And a second sentence after it.")
    assert "\n" in result.text


def test_closer_appends_to_the_end():
    result = run(
        "closer", "The boundaries are fixed before the question arrives. Nothing moves them."
    )
    assert result.text.startswith("The boundaries are fixed")
    assert result.text.endswith(result.quote)


def test_closer_declines_a_single_sentence_paragraph():
    """Appended to one short sentence it would be half the paragraph, a different shape."""
    assert run("closer", "The boundaries are fixed before the question arrives.") is None


def test_restatement_adds_a_second_saying_of_the_same_thing():
    result = run("restatement", "The retriever never changes between runs of the tool.")
    assert result.text.count("retriever") >= 1
    assert result.quote in result.text


def test_triad_produces_three_items():
    result = run("triad", PROSE)
    assert result.quote.count(",") >= 1
    assert " and " in result.quote


def test_fragment_has_no_verb_of_its_own():
    result = run("fragment", PROSE)
    assert result.quote.endswith(".")


def test_cliche_emphasis_announces_importance():
    result = run("cliche-emphasis", "The ceiling is decided by the cuts alone.")
    assert result.quote in result.text


def test_the_catalogue_is_covered():
    """Every habit ai-sniffer looks for has an injector, or the eval has a blind spot."""
    assert sorted(INJECTORS) == sorted(
        [
            "antithesis",
            "cliche-emphasis",
            "closer",
            "dramatic-beat",
            "emphasis-word",
            "fragment",
            "generic-detail",
            "hedge",
            "reader-instruction",
            "restatement",
            "triad",
        ]
    )


# ---- the injected text has to read like prose --------------------------------------------

MARKED_UP = "The **Totalization Agreement** is a bilateral treaty. It serves two purposes:"


def test_a_proper_noun_keeps_its_capital_when_a_sentence_is_prefixed():
    text = "Social Security is administered by two countries under the treaty."
    result = run("cliche-emphasis", text)
    assert "social Security" not in result.text


def test_a_sentence_introducing_a_list_is_not_restated():
    """ "It serves two purposes:" restated becomes "...two purposes:." — punctuation nonsense."""
    result = run("restatement", MARKED_UP)
    assert result is None or ":." not in result.text


def test_restatement_does_not_leave_a_dangling_dash():
    result = run("restatement", 'The "10-year rule" is the concern— and it is widely misread.')
    assert result is None or "—." not in result.text


def test_word_borrowing_templates_do_not_pluralise_adverbs():
    """ "Two currentlys" is not English, and nonsense tests a detector on the wrong thing."""
    text = "The rule currently applies and it generally works fairly quickly for everyone."
    for name in ("fragment", "triad"):
        result = run(name, text)
        if result is not None:
            assert "currentlys" not in result.text
            assert "generallys" not in result.text


def test_plural_handles_the_irregular_endings_it_will_meet():
    from slopify.habits import plural

    assert plural("country") == "countries"
    assert plural("box") == "boxes"
    assert plural("match") == "matches"
    assert plural("day") == "days"
    assert plural("chunk") == "chunks"


def test_generic_detail_reads_as_a_quantity_not_a_typo():
    """ "a surprising number credits" is a missing "of", which is a different fault."""
    result = run("generic-detail", "You must have earned at least 6 U.S. credits under the system.")
    assert result is not None
    assert "6" not in result.text
    words = result.text.split()
    assert "credits" in words


def test_generic_detail_declines_a_number_with_nothing_to_count():
    assert run("generic-detail", "The final score for that whole run was 17.7.") is None


def test_antithesis_does_not_call_a_person_a_technicality():
    text = "Having worked in the US before moving to Canada, I was unsure how it applied."
    result = run("antithesis", text)
    assert result is None or "I wasn't a" not in result.text


def test_a_sentence_opening_on_a_conjunction_is_lowercased_when_prefixed():
    """ "Note that But as a candidate..." kept a capital that belongs to no name."""
    result = run("reader-instruction", "But as a candidate, this gives you a real advantage.")
    assert result is not None
    assert "that But" not in result.text
