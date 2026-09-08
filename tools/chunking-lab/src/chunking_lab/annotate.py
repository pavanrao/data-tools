"""Manufacture gold spans from your own documents, and report how many survived.

Everything else in this tool needs questions with character-level answers, and
only two corpora in the world have them: the one Chroma published and the one this
repo generates. That is the gap this closes. Point it at your documents, pay a
model once, and the result is a `gold.jsonl` that `score --corpus-dir` reads --
after which every comparison is deterministic, offline and free (C8).

**The design is C9, and the whole thing turns on one refusal: never ask the model
for offsets.** Models are unreliable at counting characters, and an off-by-forty
gold span does not look wrong -- it silently scores every strategy against the
wrong text, which is worse than having no corpus. So the model is asked for the
answer *quoted verbatim*, the quote is located deterministically
(`chunking_lab.locate`), and **anything that cannot be found is discarded**.

That inverts the failure mode. A weaker model does not produce *wrong* ground
truth; it produces *less* of it. You get forty usable questions instead of ninety,
and the shortfall is a **yield** you can read off rather than a corruption you
cannot see. The reference implementation retries instead, so a weak model shows up
there as a longer run and a larger bill; reporting the yield is the point of the
decision.
"""

from __future__ import annotations

import json
import random
from collections.abc import Iterator
from dataclasses import dataclass, field

from chunking_lab.corpus import Corpus, Question
from chunking_lab.locate import locate

#: Characters of the document shown to the model at once. Chroma uses 4000, and
#: the size matters for a reason worth knowing: a window is also the *scope* of
#: the questions it can produce. Widen it and you get questions spanning more of
#: the document; narrow it and you get local factoids -- which is a thumb on the
#: scale for small chunks, since a ranking is only ever a ranking against a
#: question mix (C13).
WINDOW = 4000

#: Excerpts per question. More than a handful and the "answer" stops being an
#: answer and becomes a summary of the window.
MAX_EXCERPTS = 3

#: Generation options. **Temperature 0 is not a tuning preference here, it is a
#: correctness requirement.** The entire instruction is "copy this text character
#: for character"; sampling introduces variation into the one thing that must not
#: vary, and the variation is invisible in the reply -- a slightly reworded quote
#: reads perfectly well and simply fails to be found.
#:
#: This was found the expensive way. A first comparison ran at Ollama's default of
#: 0.8 and appeared to show a 14B model doing *worse* than a 7B, which looked like
#: a finding about model size and was an artefact of the sampling temperature --
#: hitting the larger model hardest, because it has more capacity to produce
#: plausible variations.
OPTIONS = {"temperature": 0.0}

PROMPT = """\
You are building an evaluation set for a document retrieval system.

Below is an excerpt from a document. Write ONE question that the excerpt answers,
and give the exact text that answers it.

Rules, all of which matter:
- The question must be answerable from this excerpt alone.
- The question must NOT refer to "the excerpt", "the passage", "the text", or
  "above" -- someone searching a large corpus would never phrase it that way.
- Quote the answer VERBATIM, copied character for character from the excerpt.
  Do not paraphrase, correct, reformat or shorten it. If the answer is a table
  row, quote the whole row including its pipes and spacing.
- Give between 1 and {max_excerpts} excerpts. Fewer is better.
- Prefer a specific, checkable fact over a general one.

Return only JSON, in exactly this shape:
{{"question": "...", "excerpts": ["...", "..."]}}

Document excerpt:
---
{window}
---
"""


@dataclass(frozen=True, slots=True)
class Yield:
    """How much usable ground truth a run actually produced.

    The number to publish alongside any corpus built this way. A low yield does not
    mean the questions you kept are bad -- it means the model produced a lot you
    could not verify, and you are looking at the verified remainder.
    """

    asked: int = 0
    kept: int = 0
    #: Discard reasons, so a bad run says *why* rather than only *how much*. Named
    #: for what actually happened: `call_failed` is the provider raising,
    #: `malformed` is a reply that could not be read as the expected JSON, and
    #: `unlocatable` is the interesting one -- a well-formed answer whose quote is
    #: not in the document.
    call_failed: int = 0
    malformed: int = 0
    unlocatable: int = 0
    #: How each surviving excerpt was found: exact, whitespace, or fuzzy. A corpus
    #: built mostly from fuzzy matches is less trustworthy and this is where that
    #: shows.
    by_stage: dict[str, int] = field(default_factory=dict)

    @property
    def rate(self) -> float:
        return self.kept / self.asked if self.asked else 0.0

    def report(self) -> str:
        lines = [
            f"yield: {self.kept}/{self.asked} questions usable ({self.rate:.0%})",
        ]
        for label, count in (
            ("the model call failed", self.call_failed),
            ("reply was not usable JSON", self.malformed),
            ("quote not found in the document", self.unlocatable),
        ):
            if count:
                lines.append(f"  discarded, {label}: {count}")
        if self.by_stage:
            found = ", ".join(f"{k} {v}" for k, v in sorted(self.by_stage.items()))
            lines.append(f"  excerpts located by: {found}")
        if self.rate < 0.5 and self.asked:
            lines.append(
                "  NOTE: under half survived. The kept questions are still verified -- "
                "every one was found in the document -- but a weak model produced a lot "
                "you could not use. Consider a stronger one before enlarging the set."
            )
        return "\n".join(lines)


def _windows(text: str, count: int, rng: random.Random) -> Iterator[str]:
    """Sample windows of the document, deterministically for a given seed."""
    if len(text) <= WINDOW:
        for _ in range(count):
            yield text
        return
    for _ in range(count):
        start = rng.randint(0, len(text) - WINDOW)
        yield text[start : start + WINDOW]


def _parse(raw: str) -> tuple[str, list[str]] | None:
    """Read the model's reply, tolerating the fences it usually wraps JSON in."""
    body = raw.strip()
    if body.startswith("```"):
        body = body.split("\n", 1)[-1].rsplit("```", 1)[0]
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return None
    question = payload.get("question")
    excerpts = payload.get("excerpts")
    if not isinstance(question, str) or not isinstance(excerpts, list):
        return None
    quotes = [e for e in excerpts if isinstance(e, str) and e.strip()][:MAX_EXCERPTS]
    return (question.strip(), quotes) if question.strip() and quotes else None


def annotate(
    name: str,
    text: str,
    provider,
    *,
    count: int = 5,
    seed: int = 0,
) -> tuple[Corpus, Yield]:
    """Generate up to ``count`` verified questions for one document.

    ``provider`` is anything with ``complete(prompt) -> str``; the caller decides
    whether that is a local model or a hosted one, and this never learns which.

    Returns the corpus and the yield. Questions that could not be verified are not
    in the corpus and *are* in the yield -- which is the entire design.
    """
    rng = random.Random(seed)
    questions: list[Question] = []
    asked = call_failed = malformed = unlocatable = 0
    stages: dict[str, int] = {}

    for window in _windows(text, count, rng):
        asked += 1
        try:
            raw = provider.complete(
                PROMPT.format(window=window, max_excerpts=MAX_EXCERPTS), **OPTIONS
            )
        except Exception:  # noqa: BLE001 - a failed call is a discarded question, not a crash
            call_failed += 1
            continue

        parsed = _parse(raw)
        if parsed is None:
            malformed += 1
            continue

        question_text, quotes = parsed
        # Locate against the WHOLE document, not the window: the model may quote
        # text that also appears outside it, and the offsets must address the
        # document that will actually be chunked.
        located = [locate(text, quote) for quote in quotes]
        if any(hit is None for hit in located):
            unlocatable += 1
            continue

        for hit in located:
            stages[hit.how] = stages.get(hit.how, 0) + 1
        questions.append(
            Question(
                question_id=f"{name}:{len(questions):03d}",
                text=question_text,
                corpus=name,
                gold=tuple(hit.span for hit in located),
                kind="generated",
                about=f"located by {'+'.join(sorted({h.how for h in located}))}",
            )
        )

    from chunking_lab.corpus import provenance_for

    corpus = Corpus(
        name=name, text=text, provenance=provenance_for(name, text), questions=tuple(questions)
    )
    return corpus, Yield(
        asked=asked,
        kept=len(questions),
        call_failed=call_failed,
        malformed=malformed,
        unlocatable=unlocatable,
        by_stage=stages,
    )
