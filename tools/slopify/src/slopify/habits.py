"""One injector per habit in ai-sniffer's catalogue.

Each takes a paragraph and a seeded ``random.Random``, and returns the rewritten
paragraph together with the exact words a reader would quote as the habit — or
``None`` when the paragraph offers no site for it. Declining is the normal case
and not a failure: a paragraph with no copula cannot be given an antithesis
without inventing a claim, and inventing one would make the ground truth a
fiction.

The templates are deliberately plain. They are what a template produces on
demand, which is not the same thing as what a model produces when left alone, and
every number measured against them carries that limit.
"""

from __future__ import annotations

import random
import re
from collections.abc import Callable
from dataclasses import dataclass

_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[\"“'(\[]?[A-Z0-9])")

# Words too common to stand in as "a noun from this paragraph".
_STOPWORDS_TEXT = """a an and are as at be been but by can could did do does for from had has have
    he her him his how i if in into is it its me my no not of on or our out she so
    such than that the their them then there these they this those to too up us was
    we were what when where which who why will with would you your every all any"""
_STOPWORDS = frozenset(_STOPWORDS_TEXT.split())

#: Lowercasing the first word of a sentence is safe for these and wrong for a proper
#: noun: "Note that social Security..." is a tell the injector introduced, not the
#: habit it was asked for.
_LOWERABLE_TEXT = """a an the this that these those it its there here we you they he she his her
    their our some most many both one two three each every all no none such if when
    where while because although since after before what which who
    but and so yet or nor then though however"""
_LOWERABLE = frozenset(_LOWERABLE_TEXT.split())


@dataclass(frozen=True, slots=True)
class Injection:
    habit: str
    text: str
    quote: str


Injector = Callable[[str, random.Random], Injection | None]


def sentences(text: str) -> list[str]:
    return [s for s in _SENTENCE.split(text.strip()) if s]


#: A noun is whatever an article was pointing at. Without a part-of-speech tagger
#: this is the cheapest reliable way to avoid "two resides, both familiar" — a verb
#: pluralised as though it were a thing. Nonsense would test a detector on being
#: nonsense instead of on the habit.
_ARTICLE_PHRASE = re.compile(
    r"\b(?:the|a|an|its|this|that|their|our|your|each|every)\s+"
    r"([a-z][a-z-]{2,})(?:\s+([a-z][a-z-]{2,}))?"
)
# "ent", "ant" and "al" were here and cost more than they saved: they exclude
# agent, component, document, signal and proposal, which are exactly the nouns
# these templates want.
_ADJECTIVE_SUFFIX = ("ive", "ous", "able", "ible", "ful", "ing", "ed", "ian")
_ADJECTIVES_TEXT = """simple major minor primary real whole same other new old single main top
    best worst first second third last next only own full high low long short small
    large good bad common general specific particular certain actual entire
    private public default secure modern standard local remote personal official"""
_ADJECTIVES = frozenset(_ADJECTIVES_TEXT.split())


def _adjectival(word: str) -> bool:
    return word in _ADJECTIVES or word.endswith(_ADJECTIVE_SUFFIX)


def _content_words(text: str) -> list[str]:
    """Head nouns this paragraph is about, in the order they appear.

    An article names a noun a word or two later. When the first word after the
    article looks like an adjective, the one after it is taken instead.
    """
    out: list[str] = []
    for first, second in _ARTICLE_PHRASE.findall(text.lower()):
        word = second if (second and _adjectival(first)) else first
        if (
            len(word) >= 4
            and word not in _STOPWORDS
            and not word.endswith("ly")
            and not word.endswith("s")
            and not _adjectival(word)
        ):
            out.append(word)
    return out


def _lower_first(sentence: str) -> str:
    """Lowercase the opening word only when it is not a name."""
    first = re.match(r"[A-Za-z']+", sentence)
    if first and first[0].lower() in _LOWERABLE:
        return sentence[0].lower() + sentence[1:]
    return sentence


def _pick_sentence(text: str, rng: random.Random, minimum_words: int = 5) -> int | None:
    parts = sentences(text)
    eligible = [i for i, s in enumerate(parts) if len(s.split()) >= minimum_words]
    return rng.choice(eligible) if eligible else None


def _rejoin(parts: list[str]) -> str:
    return " ".join(parts)


# ---- the injectors -------------------------------------------------------------------------

_NOT_THINGS = ("a detail", "an accident", "a matter of taste", "a technicality")
_PEOPLE_TEXT = "i we you he she they who someone anyone everyone nobody"
_PEOPLE = frozenset(_PEOPLE_TEXT.split())


def antithesis(text: str, rng: random.Random) -> Injection | None:
    """Split a claim into the catalogue's "It isn't X. It's Y." shape."""
    parts = sentences(text)
    for i, part in enumerate(parts):
        match = re.match(r"(.{4,}?)\s+(is|was)\s+(.+?)([.!?])$", part)
        if not match:
            continue
        subject, copula, predicate, stop = match.groups()
        # "We measured 472 questions and the score was 17.7" has the copula
        # belonging to "the score", not to the whole clause before it. Keep the
        # part before the last joiner as a prefix and rewrite only the subject.
        prefix = ""
        for joiner in (" and ", " but ", ", "):
            if joiner in subject:
                head, _, subject = subject.rpartition(joiner)
                prefix = head + joiner
                break
        # The foils below are things, so a person cannot be one.
        if not subject or subject.split()[-1].lower() in _PEOPLE:
            continue
        foil = rng.choice(_NOT_THINGS)
        contraction = "isn't" if copula == "is" else "wasn't"
        quote = f"{subject} {contraction} {foil}. It {copula} {predicate}{stop}"
        parts[i] = prefix + quote
        return Injection("antithesis", _rejoin(parts), quote)
    return None


_FRAGMENTS = ("A matter of {w}.", "All of it, in one {w}.", "Two {p}, both familiar.")


def plural(word: str) -> str:
    """Enough English to avoid "two countrys"."""
    if word.endswith("y") and word[-2:-1] not in "aeiou":
        return word[:-1] + "ies"
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    return word + "s"


def fragment(text: str, rng: random.Random) -> Injection | None:
    """Append a verbless phrase standing in for a sentence."""
    words = _content_words(text)
    if not words:
        return None
    word = rng.choice(words)
    quote = rng.choice(_FRAGMENTS).format(w=word, p=plural(word))
    return Injection("fragment", f"{text.rstrip()} {quote}", quote)


def triad(text: str, rng: random.Random) -> Injection | None:
    """Add a sentence whose only shape is three of something."""
    words = _content_words(text)
    if len(set(words)) < 3:
        return None
    a, b, c = rng.sample(sorted(set(words)), 3)
    quote = f"Three things follow: {a}, {b} and {c}."
    return Injection("triad", f"{text.rstrip()} {quote}", quote)


_HEDGES = {
    "every": "almost every",
    "all": "most",
    "always": "nearly always",
    "never": "hardly ever",
    "each": "most",
}


def hedge(text: str, rng: random.Random) -> Injection | None:
    """Soften a universal so the claim can no longer be checked."""
    pattern = re.compile(r"\b(" + "|".join(_HEDGES) + r")\b(\s+\S+)", re.IGNORECASE)
    matches = list(pattern.finditer(text))
    if not matches:
        return None
    match = rng.choice(matches)
    quote = _HEDGES[match[1].lower()] + match[2]
    return Injection("hedge", text[: match.start()] + quote + text[match.end() :], quote)


_INSTRUCTIONS = ("Note that ", "Consider that ", "Keep in mind that ")


def reader_instruction(text: str, rng: random.Random) -> Injection | None:
    """Tell the reader how to take the sentence that follows."""
    index = _pick_sentence(text, rng)
    if index is None:
        return None
    parts = sentences(text)
    opener = rng.choice(_INSTRUCTIONS)
    body = _lower_first(parts[index])
    parts[index] = opener + body
    quote = opener + " ".join(body.split()[:6])
    return Injection("reader-instruction", _rejoin(parts), quote)


def dramatic_beat(text: str, rng: random.Random) -> Injection | None:
    """Break the last sentence out as a one-line paragraph."""
    parts = sentences(text)
    if len(parts) < 2:
        return None
    beat = parts.pop()
    return Injection("dramatic-beat", _rejoin(parts) + "\n\n" + beat, beat)


_CLOSERS = (
    "That is the whole of it.",
    "Which is the entire argument, in one line.",
    "That is what the measurement was for.",
)


def closer(text: str, rng: random.Random) -> Injection | None:
    """Land the paragraph on a line that says what it all meant.

    Needs a paragraph with something to sum up: appended to a single short
    sentence the closer is half the paragraph, which is a different shape.
    """
    if len(sentences(text)) < 2:
        return None
    quote = rng.choice(_CLOSERS)
    return Injection("closer", f"{text.rstrip()} {quote}", quote)


def restatement(text: str, rng: random.Random) -> Injection | None:
    """Say the previous sentence again, adding nothing."""
    index = _pick_sentence(text, rng)
    if index is None:
        return None
    parts = sentences(text)
    if parts[index].rstrip().endswith(":"):
        return None  # it introduces a list; restating it gives "...purposes:."
    said = parts[index].rstrip(" .!?—–-:;")
    if not said:
        return None
    quote = f"Put another way, {_lower_first(said)}."
    parts.insert(index + 1, quote)
    return Injection("restatement", _rejoin(parts), quote)


_CLICHES = ("The key insight is that ", "The crucial point is that ", "What matters here is that ")


def cliche_emphasis(text: str, rng: random.Random) -> Injection | None:
    """Announce importance instead of showing it."""
    index = _pick_sentence(text, rng)
    if index is None:
        return None
    parts = sentences(text)
    body = _lower_first(parts[index])
    opener = rng.choice(_CLICHES)
    parts[index] = opener + body
    quote = opener + " ".join(body.split()[:6])
    return Injection("cliche-emphasis", _rejoin(parts), quote)


#: Forms that stand in for "6" directly in front of a noun. "a surprising number
#: credits" needs an "of" and reads as a typo, which is a different fault from the
#: one being injected.
_VAGUE = ("a good few", "quite a few", "a fair number of")


def generic_detail(text: str, rng: random.Random) -> Injection | None:
    """Put a vague phrase where a real figure stands."""
    # Only a figure that counts something: a bare number at the end of a clause
    # ("the score was 17.7") has no noun for these forms to quantify.
    matches = list(re.finditer(r"\b\d[\d.,]*\b(?=\s+[A-Za-z])", text))
    if not matches:
        return None
    match = rng.choice(matches)
    quote = rng.choice(_VAGUE)
    return Injection("generic-detail", text[: match.start()] + quote + text[match.end() :], quote)


_INTENSIFIERS = ("exactly", "precisely", "actually")


def emphasis_word(text: str, rng: random.Random) -> Injection | None:
    """Add stress and no information."""
    # Two following words, so the quote is long enough to locate in the draft.
    matches = list(re.finditer(r"\b(is|was|are|were|does|did)\s+(\S+\s+\S+)", text))
    if not matches:
        return None
    match = rng.choice(matches)
    word = rng.choice(_INTENSIFIERS)
    quote = f"{match[1]} {word} {match[2]}"
    return Injection("emphasis-word", text[: match.start()] + quote + text[match.end() :], quote)


INJECTORS: dict[str, Injector] = {
    "antithesis": antithesis,
    "cliche-emphasis": cliche_emphasis,
    "closer": closer,
    "dramatic-beat": dramatic_beat,
    "emphasis-word": emphasis_word,
    "fragment": fragment,
    "generic-detail": generic_detail,
    "hedge": hedge,
    "reader-instruction": reader_instruction,
    "restatement": restatement,
    "triad": triad,
}
