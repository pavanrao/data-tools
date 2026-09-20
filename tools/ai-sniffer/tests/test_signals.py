"""The countable habits: each signal on text that has it, and on text that doesn't."""

from __future__ import annotations

from ai_sniffer.document import parse_markdown
from ai_sniffer.signals import check


def findings(text, signal):
    return [(f.line, f.quote) for f in check(parse_markdown(text)).findings if f.signal == signal]


# ---- contractions -------------------------------------------------------------------------


def test_contraction_rate_is_per_hundred_words():
    report = check(
        parse_markdown("It's fine and we don't mind. The cat's bowl is here, isn't it.\n")
    )

    # it's, don't, isn't count; the possessive "cat's" does not. 13 words.
    assert report.metrics["contractions"] == 3
    assert report.metrics["contractions_per_100_words"] == round(100 * 3 / 13, 1)


def test_curly_apostrophes_count_as_contractions():
    report = check(parse_markdown("That’s what we’d expect.\n"))

    assert report.metrics["contractions"] == 2


def test_no_words_gives_a_zero_rate_not_an_error():
    assert check(parse_markdown("```\ncode only\n```\n")).metrics["contractions_per_100_words"] == 0


# ---- word lists ---------------------------------------------------------------------------


def test_hedged_universals_are_found_with_their_line():
    text = "Intro.\n\nAlmost every server does this. Plenty of teams agree.\n"

    assert findings(text, "hedge") == [(3, "Almost every"), (3, "Plenty of")]


def test_most_is_a_hedge_only_before_a_generic_group():
    text = "Most people skip it. The most important part is here.\n"

    assert findings(text, "hedge") == [(1, "Most people")]


def test_emphasis_words_match_whole_words_only():
    text = "It does exactly that. The exactness was precisely the problem.\n"

    assert findings(text, "emphasis-word") == [(1, "exactly"), (1, "precisely")]


def test_reader_instructions_anywhere_and_imperatives_only_at_sentence_start():
    text = "Note that it failed. Consider what it handles. I considered it. We might consider it.\n"

    assert findings(text, "reader-instruction") == [(1, "Note that"), (1, "Consider")]


# ---- paragraphs and rhythm ----------------------------------------------------------------


def test_one_sentence_paragraphs_are_findings_unless_they_introduce_something():
    text = (
        "A first paragraph with two sentences. Here is the second.\n\n"
        "It didn't degrade.\n\n"
        "The command looks like this:\n\n"
        "- a list item is one sentence and that is normal\n"
    )

    assert findings(text, "one-sentence-paragraph") == [(3, "It didn't degrade.")]


def test_sentence_length_mean_and_variation():
    report = check(parse_markdown("One two three four. One two. One two three four five six.\n"))

    lengths = [4, 2, 6]
    mean = sum(lengths) / 3
    sd = (sum((x - mean) ** 2 for x in lengths) / 3) ** 0.5
    assert report.metrics["sentence_length"] == {"mean": round(mean, 1), "cv": round(sd / mean, 2)}


def test_a_run_of_four_sentences_of_near_equal_length_is_a_finding():
    text = (
        "This sentence has six words total. That sentence also has six words. "
        "Here are seven words in this one. Six words again in this line. "
        "Then a much longer sentence arrives, with a clause, and it runs on for a while.\n"
    )

    assert findings(text, "even-rhythm") == [(1, "This sentence has six words total.")]


def test_three_similar_sentences_are_not_a_run():
    text = "Six words are in this sentence. Also six words in this one. Six again in this one.\n"

    assert findings(text, "even-rhythm") == []


# ---- skeletons ----------------------------------------------------------------------------


def test_nearby_sentences_with_the_same_function_word_skeleton():
    text = "It is not a confession. It is not a checksum.\n\nSomething else entirely.\n"

    assert findings(text, "repeated-skeleton") == [(1, "It is not a checksum.")]


def test_short_skeletons_do_not_count():
    # "Yes." and "No." reduce to the same one-slot skeleton, which says nothing.
    assert findings("Yes. No. Maybe.\n", "repeated-skeleton") == []


def test_distant_repeats_do_not_count():
    filler = (
        "Servers came up slowly. Probes ran in order. Logs filled quickly. "
        "Timeouts stayed short. Retries helped once. Results varied widely."
    )
    text = f"It is not a confession. {filler} It is not a checksum.\n"

    assert findings(text, "repeated-skeleton") == []


# ---- detail and closers -------------------------------------------------------------------


def test_concrete_detail_counts_numbers_dates_quotes_and_code():
    report = check(
        parse_markdown('On 27 July it took 40 ms and printed "ok" from `probe.py` twice.\n')
    )

    detail = report.metrics["detail"]
    assert (detail["numbers"], detail["dates"], detail["quoted"], detail["code"]) == (1, 1, 1, 1)
    assert detail["per_100_words"] == round(100 * 4 / report.metrics["words"], 1)


def test_the_last_prose_sentence_of_each_section_is_extracted():
    text = (
        "Opening paragraph. It ends here.\n\n"
        "## Section\n\nBody text. The closing line lands.\n\n- a trailing list item\n\n"
        "## Empty\n\n```\ncode\n```\n"
    )

    closers = [(c.line, c.section, c.text) for c in check(parse_markdown(text)).closers]
    assert closers == [(1, "", "It ends here."), (5, "Section", "The closing line lands.")]


def test_clean_prose_has_no_findings():
    text = (
        "I ran the probe against twelve servers on 14 September. Three of the five vendor "
        "servers answered discovery, and none of the six reference servers did.\n\n"
        "The one surprise was dbt-mcp, which timed out once and answered on every run after "
        "that. I added a single retry.\n"
    )

    assert check(parse_markdown(text)).findings == []


def test_a_one_sentence_paragraph_must_end_like_a_sentence():
    text = "By Pavan · 5 min read\n\nIt collapsed.\n"

    assert findings(text, "one-sentence-paragraph") == [(3, "It collapsed.")]


def test_word_lists_still_read_layout_blocks_but_paragraph_signals_do_not():
    from ai_sniffer.document import parse_html

    report = check(
        parse_html('<div class="card">It is exactly a write.</div><p>Two here. And more.</p>')
    )

    assert [(f.signal, f.quote) for f in report.findings] == [("emphasis-word", "exactly")]
