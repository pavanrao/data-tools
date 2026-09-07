#!/usr/bin/env python3
"""Generate the hostile corpus: documents built so specific strategies provably fail.

Every fixture here is a document that a chunker processes *successfully* and gets
wrong. It is the same idea as `ingest-ledger`'s hostile corpus, moved one stage
down the pipeline: there the failure was a file that read as empty, here it is a
boundary that lands where it must not.

**Gold spans are known by construction.** The generator writes the answer text,
so it knows exactly which characters it occupies -- no annotation pass, no model,
no fuzzy matching. That is what makes this the default ground truth (README C11)
and what CI can run with nothing installed.

Generated rather than committed, so each document's defect is described in code
instead of folklore.

    uv run python tools/chunking-lab/corpus/generate.py corpus/hostile
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Document:
    """A document under construction, tracking where the answers land.

    ``add`` appends plain text. ``answer`` appends text *and* records its
    character range, which is the whole trick: the span is exact because the
    generator wrote it.
    """

    name: str
    defect: str
    #: The strategy family this document is built to defeat.
    defeats: str
    parts: list[str] = field(default_factory=list)
    gold: list[tuple[int, int]] = field(default_factory=list)
    question: str = ""

    @property
    def text(self) -> str:
        return "".join(self.parts)

    def add(self, text: str) -> Document:
        self.parts.append(text)
        return self

    def answer(self, text: str) -> Document:
        start = len(self.text)
        self.parts.append(text)
        self.gold.append((start, start + len(text)))
        return self

    def asks(self, question: str) -> Document:
        self.question = question
        return self


def heading_carries_the_subject() -> Document:
    """The subject appears only in the heading, so a size-based cut orphans the fact.

    Defeats fixed-size and anything else that ignores structure: the chunk holding
    the number does not contain the word "Northeast" anywhere.
    """
    doc = Document(
        name="heading_subject.md",
        defect="the fact's subject is in the heading; a size-based cut separates them",
        defeats="fixed-size",
    ).asks("When does the Northeast region file?")
    doc.add("# Regional Filing Calendar\n\n")
    doc.add(
        "Filing obligations differ by region. The consolidated calendar below is "
        "maintained by the finance team and is reviewed once a year, ordinarily in "
        "January, ahead of the first quarterly close.\n\n"
    )
    doc.add("## Northeast\n\n")
    doc.add(
        "This region was brought into the group in 2019 and its reporting was never "
        "harmonised with the federal calendar, for reasons that are historical rather "
        "than deliberate. "
    )
    doc.answer("Returns are filed annually, on 31 March.")
    doc.add(
        " Managers should request the figures separately rather than waiting for them "
        "to appear in the quarterly consolidation.\n"
    )
    return doc


def table_split_mid_row() -> Document:
    """A table whose rows only mean anything next to the header.

    Defeats everything except a structure-aware splitter: cut between the header
    and a row and the row becomes four numbers with no column names.
    """
    doc = Document(
        name="rate_table.md",
        defect="a table row is meaningless once separated from its header row",
        defeats="every size-based strategy",
    ).asks("What is the Q2 rate for the Southern region?")
    doc.add("# Rate Card\n\n")
    doc.add(
        "Rates are set quarterly and published here. They apply from the first day of "
        "the quarter and are not backdated under any circumstances.\n\n"
    )
    doc.add("| Region   | Q1   | Q2   | Q3   |\n")
    doc.add("|----------|------|------|------|\n")
    doc.add("| Northern | 12.0 | 19.5 | 18.0 |\n")
    doc.answer("| Southern |  7.5 |  4.25 | 11.0 |")
    doc.add("\n| Western  |  9.0 | 14.0 | 13.5 |\n\n")
    doc.add("Rates exclude surcharges, which are billed separately.\n")
    return doc


def answer_straddles_a_paragraph_break() -> Document:
    """The answer begins in one paragraph and finishes in the next.

    Defeats recursive separator splitting, which treats a blank line as the
    highest-priority place to cut -- exactly where this answer is.
    """
    doc = Document(
        name="straddle.md",
        defect="the answer spans a paragraph break, the first place a recursive splitter cuts",
        defeats="recursive separator splitting",
    ).asks("What is the escalation threshold and who approves it?")
    doc.add("# Escalation Policy\n\n")
    doc.add(
        "Incidents are triaged by the on-call engineer within fifteen minutes of the "
        "page. Most are resolved at that level and never escalate.\n\n"
    )
    doc.answer(
        "An incident is escalated when it has been open for four hours, or when it "
        "affects more than five percent of active accounts.\n\n"
        "Escalation is approved by the duty director, and by nobody else."
    )
    doc.add("\n\nThe approval is recorded in the incident log at the time it is given.\n")
    return doc


def code_block_with_blank_lines() -> Document:
    """A fenced code block containing blank lines.

    Defeats paragraph-greedy splitting, which sees the blank lines inside the fence
    as paragraph boundaries and cuts the example into unrunnable fragments.
    """
    doc = Document(
        name="code_fence.md",
        defect="blank lines inside a code fence look like paragraph breaks",
        defeats="paragraph-greedy splitting",
    ).asks("How is the retry delay calculated?")
    doc.add("# Client Configuration\n\n")
    doc.add("Retries use exponential backoff with jitter:\n\n")
    doc.answer(
        "```python\n"
        "def delay(attempt: int) -> float:\n"
        "\n"
        '    """Seconds to wait before retry `attempt`."""\n'
        "\n"
        "    base = 0.5 * (2 ** attempt)\n"
        "\n"
        "    return min(base, 30.0) * random.uniform(0.5, 1.5)\n"
        "```"
    )
    doc.add("\n\nThe cap is thirty seconds regardless of attempt count.\n")
    return doc


def orphaned_back_reference() -> Document:
    """The answer refers to a subject named only in the preceding paragraph.

    The family-6 case: no boundary placement fixes it, because the chunk holding
    the answer is *correct* and still unusable alone. Only a strategy that widens
    what is returned, or augments what is indexed, recovers the subject.
    """
    doc = Document(
        name="back_reference.md",
        defect=(
            "the answer's subject is only in the previous paragraph; "
            "the chunk is correct and still unusable"
        ),
        defeats="every boundary-placing strategy; needs context augmentation",
    ).asks("What is the retention period for the audit log?")
    doc.add("# Data Retention\n\n")
    doc.add(
        "The audit log records every administrative action taken against a tenant, "
        "including reads. It is written append-only and is never edited in place.\n\n"
    )
    doc.answer("As described above, it is retained for seven years and then destroyed.")
    doc.add(
        "\n\nOther logs follow the standard ninety-day schedule and are not covered "
        "by this section.\n"
    )
    return doc


BUILDERS = (
    heading_carries_the_subject,
    table_split_mid_row,
    answer_straddles_a_paragraph_break,
    code_block_with_blank_lines,
    orphaned_back_reference,
)


def build() -> list[Document]:
    """Every hostile document, in a stable order."""
    return [builder() for builder in BUILDERS]


def write(destination: Path) -> Path:
    """Write the documents and their gold spans. Returns the gold file's path."""
    destination.mkdir(parents=True, exist_ok=True)
    gold_path = destination / "gold.jsonl"
    with gold_path.open("w", encoding="utf-8") as handle:
        for i, doc in enumerate(build()):
            (destination / doc.name).write_text(doc.text, encoding="utf-8")
            handle.write(
                json.dumps(
                    {
                        "question_id": f"h{i:02d}",
                        "question": doc.question,
                        "corpus": doc.name,
                        "gold": [list(span) for span in doc.gold],
                        "defect": doc.defect,
                        "defeats": doc.defeats,
                    }
                )
                + "\n"
            )
    return gold_path


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "corpus/hostile")
    gold = write(target)
    documents = build()
    print(f"wrote {len(documents)} documents and {gold.name} to {target}\n")
    for doc in documents:
        print(f"  {doc.name:<22} defeats {doc.defeats}")
        print(f"  {'':<22} {doc.defect}")
