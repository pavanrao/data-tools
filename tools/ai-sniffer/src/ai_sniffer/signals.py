"""The habits that can be counted without a model.

Each word list below is a closed list built by category — quantifier hedges, generic
plural groups, intensifiers, sentence-initial imperatives — not assembled from phrases
seen in the eval drafts, so the linter isn't scored on text it was tuned to (docs/012).

A finding is a place to look, never a verdict: "exactly" is sometimes the right word.
The report carries no score for the same reason.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import asdict, dataclass, field

from .document import CODE, Document, Paragraph, Sentence


@dataclass(frozen=True, slots=True)
class Finding:
    signal: str
    line: int
    quote: str
    sentence: str


@dataclass(frozen=True, slots=True)
class Closer:
    line: int
    section: str
    text: str


@dataclass(slots=True)
class Report:
    findings: list[Finding] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    closers: list[Closer] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "metrics": self.metrics,
            "findings": [asdict(f) for f in self.findings],
            "closers": [asdict(c) for c in self.closers],
        }


def _phrases(*alternatives: str) -> re.Pattern[str]:
    return re.compile(r"\b(?:" + "|".join(alternatives) + r")\b", re.IGNORECASE)


_QUANTIFIERS = r"every|everyone|everything|all|always|never|nothing|nobody|no one|any"
_GROUPS = (
    r"people|teams|developers|engineers|companies|organi[sz]ations|users|readers|writers"
    r"|projects|systems|tools|products|applications|apps"
)
HEDGES = _phrases(
    rf"(?:almost|nearly|virtually) (?:{_QUANTIFIERS})",
    rf"(?:most|many) (?:{_GROUPS})",
    r"plenty of",
    r"a great deal of",
    r"a lot of people",
    r"more often than not",
    r"by and large",
    r"for the most part",
    r"in (?:many|most) cases",
    r"to (?:some|a large) extent",
    r"as a rule",
    r"arguably",
    r"generally",
    r"typically",
    r"roughly",
    r"frequently",
    r"largely",
    r"tends? to",
)
EMPHASIS = _phrases(
    r"exactly",
    r"precisely",
    r"genuinely",
    r"truly",
    r"entirely",
    r"completely",
    r"totally",
    r"fundamentally",
    r"incredibly",
    r"absolutely",
    r"literally",
    r"crucially",
    r"essentially",
    r"perfectly",
    r"remarkably",
    r"profoundly",
    r"undeniably",
    r"undoubtedly",
    r"actually",
    r"deeply",
)
READER_ANYWHERE = _phrases(
    r"note that",
    r"notice (?:that|how)",
    r"keep in mind",
    r"bear in mind",
    r"it(?:'s| is) worth (?:noting|remembering|pausing)",
    r"worth noting",
    r"let that sink in",
    r"make no mistake",
    r"here's the thing",
    r"sit with (?:that|this)",
)
READER_OPENING = re.compile(
    r"^[\"“‘(]?(Consider|Imagine|Picture|Notice|Remember|Recall|Suppose|Think about|"
    r"Ask yourself|Look at)\b"
)

_WORD = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z]+)*(?:[-.][A-Za-z0-9]+)*")
_CONTRACTION_ENDINGS = ("n't", "'re", "'ve", "'ll", "'d", "'m")
_S_CONTRACTIONS = frozenset(
    [
        "it",
        "that",
        "there",
        "here",
        "what",
        "who",
        "where",
        "when",
        "why",
        "how",
        "let",
        "he",
        "she",
        "everyone",
        "nobody",
        "something",
        "nothing",
        "one",
    ]
)
_MONTHS = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|"
    r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
_DATE = re.compile(
    rf"\b(?:\d{{1,2}} {_MONTHS}(?: \d{{4}})?"  # 27 July 2026
    rf"|{_MONTHS} \d{{1,2}}(?:, \d{{4}})?"  # July 27, 2026
    r"|\d{4}-\d{2}-\d{2})\b"  # 2026-07-27
)
_NUMBER = re.compile(r"(?<![\w.])\d[\d,.]*(?![\w])")
_QUOTED = re.compile(r"\"[^\"]+\"|“[^”]+”")

# Closed-class words stay in a sentence's skeleton; everything else becomes a slot.
_FUNCTION_WORDS = frozenset(
    [
        "a",
        "an",
        "the",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
        "my",
        "your",
        "his",
        "its",
        "our",
        "their",
        "this",
        "that",
        "these",
        "those",
        "what",
        "which",
        "who",
        "whom",
        "whose",
        "be",
        "is",
        "are",
        "was",
        "were",
        "been",
        "being",
        "am",
        "do",
        "does",
        "did",
        "have",
        "has",
        "had",
        "will",
        "would",
        "shall",
        "should",
        "can",
        "could",
        "may",
        "might",
        "must",
        "not",
        "no",
        "never",
        "of",
        "in",
        "on",
        "at",
        "by",
        "for",
        "with",
        "from",
        "to",
        "into",
        "onto",
        "over",
        "under",
        "about",
        "as",
        "than",
        "like",
        "through",
        "between",
        "after",
        "before",
        "without",
        "and",
        "or",
        "but",
        "so",
        "yet",
        "if",
        "because",
        "while",
        "when",
        "where",
        "then",
        "there",
        "here",
        "it's",
        "that's",
        "isn't",
        "wasn't",
        "aren't",
        "weren't",
        "don't",
        "doesn't",
        "didn't",
        "can't",
        "won't",
        "there's",
        "what's",
    ]
)
EVEN_RUN = 4
EVEN_SPREAD = 3
SKELETON_WINDOW = 3
SKELETON_MIN_FUNCTION_WORDS = 3


def words(text: str) -> list[str]:
    return _WORD.findall(text)


def _is_contraction(word: str) -> bool:
    w = word.lower().replace("’", "'")
    if w.endswith(_CONTRACTION_ENDINGS):
        return True
    return w.endswith("'s") and w[:-2] in _S_CONTRACTIONS


def _skeleton(sentence: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for m in re.finditer(r"[A-Za-z0-9]+(?:['’][A-Za-z]+)*|[,;:?!.—-]", sentence):
        token = m.group(0).lower().replace("’", "'")
        if token in _FUNCTION_WORDS or not token[0].isalnum():
            tokens.append(token)
        elif not tokens or tokens[-1] != "_":
            tokens.append("_")
    return tuple(tokens)


def _word_list_findings(sentence: Sentence, out: list[Finding]) -> None:
    for signal, pattern in (("hedge", HEDGES), ("emphasis-word", EMPHASIS)):
        for m in pattern.finditer(sentence.text):
            out.append(Finding(signal, sentence.line, m.group(0), sentence.text))
    anywhere = list(READER_ANYWHERE.finditer(sentence.text))
    for m in anywhere:
        out.append(Finding("reader-instruction", sentence.line, m.group(0), sentence.text))
    opening = READER_OPENING.match(sentence.text)
    if opening and not any(m.start() <= opening.start(1) < m.end() for m in anywhere):
        out.append(Finding("reader-instruction", sentence.line, opening.group(1), sentence.text))


def _introduces_something(paragraph: Paragraph) -> bool:
    return paragraph.text.rstrip().endswith(":")


_ENDS_LIKE_A_SENTENCE = re.compile(r"[.!?][\"”’')\]]*$")


def check(doc: Document) -> Report:
    report = Report()
    findings = report.findings
    all_sentences = doc.sentences()
    all_words = [w for s in all_sentences for w in words(s.text)]

    for sentence in all_sentences:
        _word_list_findings(sentence, findings)

    for paragraph in doc.paragraphs():
        if (
            paragraph.kind == "prose"
            and len(paragraph.sentences) == 1
            and _ENDS_LIKE_A_SENTENCE.search(paragraph.text)
        ):
            (only,) = paragraph.sentences
            findings.append(Finding("one-sentence-paragraph", only.line, only.text, only.text))

    for section in doc.sections:
        prose = [s for p in section.paragraphs if p.kind == "prose" for s in p.sentences]
        lengths = [len(words(s.text)) for s in prose]
        start = 0
        while start < len(prose):
            end = start + 1
            while end < len(prose) and (
                max(lengths[start : end + 1]) - min(lengths[start : end + 1]) <= EVEN_SPREAD
            ):
                end += 1
            if end - start >= EVEN_RUN:
                first = prose[start]
                findings.append(Finding("even-rhythm", first.line, first.text, first.text))
            start = end

    prose_order = [s for p in doc.paragraphs() if p.kind == "prose" for s in p.sentences]
    skeletons = [_skeleton(s.text) for s in prose_order]
    for i, skeleton in enumerate(skeletons):
        function_words = sum(1 for t in skeleton if t != "_" and t[0].isalnum())
        if function_words < SKELETON_MIN_FUNCTION_WORDS:
            continue
        if skeleton in skeletons[max(0, i - SKELETON_WINDOW) : i]:
            s = prose_order[i]
            findings.append(Finding("repeated-skeleton", s.line, s.text, s.text))

    findings.sort(key=lambda f: f.line)

    contractions = sum(1 for w in all_words if _is_contraction(w))
    lengths = [len(words(s.text)) for s in all_sentences]
    mean = statistics.fmean(lengths) if lengths else 0.0
    cv = statistics.pstdev(lengths) / mean if mean else 0.0
    joined = " ".join(s.text for s in all_sentences)
    dates = len(_DATE.findall(joined))
    numbers = len(_NUMBER.findall(_DATE.sub(" ", joined)))
    quoted = len(_QUOTED.findall(joined))
    detail = numbers + dates + quoted + doc.code_spans
    per_100 = (lambda n: round(100 * n / len(all_words), 1)) if all_words else (lambda n: 0)
    report.metrics = {
        "words": len(all_words),
        "sentences": len(all_sentences),
        "paragraphs": len(doc.paragraphs()),
        "contractions": contractions,
        "contractions_per_100_words": per_100(contractions),
        "sentence_length": {"mean": round(mean, 1), "cv": round(cv, 2)},
        "detail": {
            "numbers": numbers,
            "dates": dates,
            "quoted": quoted,
            "code": doc.code_spans,
            "per_100_words": per_100(detail),
        },
    }

    for section in doc.sections:
        prose_paragraphs = [
            p for p in section.paragraphs if p.kind == "prose" and not _introduces_something(p)
        ]
        if prose_paragraphs and prose_paragraphs[-1].sentences:
            last = prose_paragraphs[-1].sentences[-1]
            report.closers.append(Closer(last.line, section.heading, last.text))
    return report


__all__ = ["CODE", "Closer", "Finding", "Report", "check", "words"]
