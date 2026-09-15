# ruff: noqa: E501 -- the label table's quotes are exact draft text; wrapping them would risk changing them.
"""Build and verify eval/labels.json from the hand-written label table below.

Every quote must occur exactly once in its draft after normalisation, or the build
fails. Line numbers are computed from the draft rather than typed, so they can't
drift from the text they point at.

Severity decides how a label is scored:
  high, medium  counted in recall; a reviewer that misses one loses a point
  low           neutral; flagging it neither earns nor costs anything

Held-out labels were written before any model had been shown either held-out post.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
DRAFTS = HERE / "drafts"

DRAFT_META = {
    "dev-database-before.html": {"role": "development", "source": "data-tools 372bb84"},
    "dev-protocol-before.md": {"role": "development", "source": "pavanrao.github.io cfa59de"},
    "heldout-double-entry.html": {"role": "held-out", "source": "data-tools b265882"},
    "heldout-where-the-cut-falls.html": {
        "role": "held-out",
        "source": "data-tools b265882",
        # Sections 1, 4, 7, 10 and 13, chosen in docs/012 before any run.
        "scored_line_ranges": [[268, 301], [384, 461], [617, 677], [751, 781], [1072, 1177]],
    },
    "clean-database-after.html": {"role": "clean", "source": "data-tools 138a26c"},
    "clean-protocol-after.md": {"role": "clean", "source": "pavanrao.github.io 2e91d3d"},
}

# (draft, habit, severity, quote)
LABELS: list[tuple[str, str, str, str]] = [
    # ---- development: Let the Database Say No, before its rewrite ----------------------------
    (
        "dev-database-before.html",
        "hedge",
        "medium",
        "Almost every SQL-over-MCP server decides whether a query is safe",
    ),
    (
        "dev-database-before.html",
        "closer",
        "medium",
        "the database has been offering it for twenty years",
    ),
    (
        "dev-database-before.html",
        "fragment",
        "high",
        "Three tools, a row cap, done in an afternoon.",
    ),
    (
        "dev-database-before.html",
        "closer",
        "medium",
        "The interesting part turned out not to be the protocol at all.",
    ),
    ("dev-database-before.html", "dramatic-beat", "high", "It was this question."),
    (
        "dev-database-before.html",
        "hedge",
        "medium",
        "Most published examples do some version of this",
    ),
    (
        "dev-database-before.html",
        "reader-instruction",
        "high",
        "Consider what it must already handle correctly.",
    ),
    (
        "dev-database-before.html",
        "antithesis",
        "high",
        "You can fix each of these. You cannot fix the category.",
    ),
    (
        "dev-database-before.html",
        "antithesis",
        "medium",
        "is owned by whoever maintains the SQL dialect, not by you",
    ),
    (
        "dev-database-before.html",
        "fragment",
        "high",
        "Two mechanisms, both older than the problem.",
    ),
    (
        "dev-database-before.html",
        "antithesis",
        "high",
        "Not a flag your code checks. The file is opened in a mode where writing is not a thing that can happen.",
    ),
    ("dev-database-before.html", "dramatic-beat", "high", "That is the whole guard."),
    (
        "dev-database-before.html",
        "fragment",
        "high",
        "Four for four, and not because I thought about any of them.",
    ),
    (
        "dev-database-before.html",
        "closer",
        "high",
        "It is an allowlist in the engine, so it is wrong only in the safe direction.",
    ),
    (
        "dev-database-before.html",
        "antithesis",
        "high",
        "The lesson survives the change of engine; the regex does not.",
    ),
    (
        "dev-database-before.html",
        "cliche-emphasis",
        "medium",
        "It failed on my own code first, which is the point",
    ),
    ("dev-database-before.html", "dramatic-beat", "medium", "table_info. It was refused."),
    ("dev-database-before.html", "dramatic-beat", "medium", "This was the guard working."),
    ("dev-database-before.html", "reader-instruction", "high", "Sit with that for a second."),
    (
        "dev-database-before.html",
        "triad",
        "medium",
        "Deny-by-default failed loudly, in development, on the safe side.",
    ),
    (
        "dev-database-before.html",
        "closer",
        "high",
        "That is the entire argument for it in one incident.",
    ),
    (
        "dev-database-before.html",
        "emphasis-word",
        "low",
        "The protocol has a perfectly good error channel.",
    ),
    ("dev-database-before.html", "dramatic-beat", "high", "It is the wrong channel."),
    ("dev-database-before.html", "emphasis-word", "low", "The server worked exactly as designed."),
    (
        "dev-database-before.html",
        "antithesis",
        "high",
        "What the model needs to know is not that it failed, but what to do differently.",
    ),
    ("dev-database-before.html", "fragment", "high", "Two fields, two audiences."),
    ("dev-database-before.html", "dramatic-beat", "high", "eats the entire context window. Fine."),
    (
        "dev-database-before.html",
        "cliche-emphasis",
        "medium",
        "Honest answer, for the case you are probably imagining",
    ),
    ("dev-database-before.html", "emphasis-word", "low", "A server there is pure overhead"),
    ("dev-database-before.html", "triad", "medium", "It changes when one of three things is true."),
    (
        "dev-database-before.html",
        "reader-instruction",
        "high",
        "Note that none of those three is about the protocol.",
    ),
    (
        "dev-database-before.html",
        "antithesis",
        "medium",
        "The protocol's contribution is narrower and still real",
    ),
    ("dev-database-before.html", "antithesis", "medium", "Build a server, not a client."),
    ("dev-database-before.html", "dramatic-beat", "medium", "They are the product."),
    # ---- development: Which Protocol Is Your MCP Server Speaking?, before its rewrite ---------
    (
        "dev-protocol-before.md",
        "hedge",
        "medium",
        "Plenty of older clients and servers are still around",
    ),
    (
        "dev-protocol-before.md",
        "generic-detail",
        "high",
        "which turned out to be harder to ask than I expected",
    ),
    (
        "dev-protocol-before.md",
        "antithesis",
        "high",
        "For a client that just needs a session, that's the right design. For working out what a server is, it throws the answer away.",
    ),
    (
        "dev-protocol-before.md",
        "emphasis-word",
        "low",
        "does exactly the negotiation you're trying to observe",
    ),
    (
        "dev-protocol-before.md",
        "generic-detail",
        "medium",
        "Separate connections matter more than they look",
    ),
    ("dev-protocol-before.md", "fragment", "high", "Each path ends one of three ways. It worked."),
    (
        "dev-protocol-before.md",
        "cliche-emphasis",
        "high",
        "The difference between those last two is the whole point",
    ),
    ("dev-protocol-before.md", "emphasis-word", "low", "companies whose tools people actually run"),
    (
        "dev-protocol-before.md",
        "fragment",
        "medium",
        "All at their latest versions, all started locally with npx or uvx, no credentials",
    ),
    ("dev-protocol-before.md", "emphasis-word", "low", "checks that the listings actually work"),
    (
        "dev-protocol-before.md",
        "fragment",
        "high",
        "Both npm packages, both reasonably recent, opposite answers.",
    ),
    (
        "dev-protocol-before.md",
        "closer",
        "high",
        "Which protocol a server speaks, on this sample, is a dependency decision nobody on the project necessarily made on purpose.",
    ),
    (
        "dev-protocol-before.md",
        "restatement",
        "high",
        "Every server that listed a capability could back it up. Nothing advertised tools and then failed to list them.",
    ),
    ("dev-protocol-before.md", "dramatic-beat", "high", "The reference servers stand out."),
    ("dev-protocol-before.md", "dramatic-beat", "high", "This part I got wrong first."),
    ("dev-protocol-before.md", "generic-detail", "medium", "The evidence looked solid."),
    (
        "dev-protocol-before.md",
        "antithesis",
        "high",
        "wasn't released as a new major of the package everyone already had. It went out on 27 July as separate packages",
    ),
    (
        "dev-protocol-before.md",
        "dramatic-beat",
        "medium",
        "That's a trap for anyone maintaining a TypeScript server.",
    ),
    ("dev-protocol-before.md", "emphasis-word", "low", "Dependabot will happily keep bumping"),
    (
        "dev-protocol-before.md",
        "closer",
        "high",
        "It just requires someone to take the major bump.",
    ),
    (
        "dev-protocol-before.md",
        "closer",
        "medium",
        "which looks a lot more reasonable with this table in front of you.",
    ),
    (
        "dev-protocol-before.md",
        "dramatic-beat",
        "high",
        "It had bugs I'd never have found against test servers.",
    ),
    ("dev-protocol-before.md", "dramatic-beat", "high", "It hadn't answered anything."),
    (
        "dev-protocol-before.md",
        "emphasis-word",
        "medium",
        "which is precisely where that one explanatory line went",
    ),
    (
        "dev-protocol-before.md",
        "emphasis-word",
        "low",
        "A server that genuinely never answers times out twice.",
    ),
    (
        "dev-protocol-before.md",
        "fragment",
        "medium",
        "And one mistake that wasn't in the probe at all.",
    ),
    ("dev-protocol-before.md", "emphasis-word", "low", "which matches the code exactly"),
    (
        "dev-protocol-before.md",
        "antithesis",
        "high",
        "since that's a fact about the server rather than a lie it told",
    ),
    ("dev-protocol-before.md", "hedge", "medium", "plenty of hosted servers only offer HTTP"),
    (
        "dev-protocol-before.md",
        "antithesis",
        "high",
        "That's a decision about sending requests to other people's endpoints, not a technical gap",
    ),
    (
        "dev-protocol-before.md",
        "closer",
        "high",
        "So the SDK settled which protocols a server speaks, and what each server claims within them came down to how it was written.",
    ),
    ("dev-protocol-before.md", "cliche-emphasis", "high", "These numbers have a short shelf life."),
    # ---- clean: Let the Database Say No, after its rewrite (habits it left or introduced) -----
    (
        "clean-database-after.html",
        "dramatic-beat",
        "medium",
        "I assumed the time would go on the protocol. It didn't.",
    ),
    (
        "clean-database-after.html",
        "generic-detail",
        "medium",
        "one question that turned out to be harder than it looks",
    ),
    ("clean-database-after.html", "cliche-emphasis", "low", "and that's sort of the problem"),
    ("clean-database-after.html", "antithesis", "medium", "Not a flag your code consults later"),
    (
        "clean-database-after.html",
        "fragment",
        "low",
        "All four, and I didn't reason about any of them.",
    ),
    (
        "clean-database-after.html",
        "closer",
        "medium",
        "it can be wrong, but only by refusing something it should have allowed",
    ),
    ("clean-database-after.html", "fragment", "high", "Same idea, different engine."),
    (
        "clean-database-after.html",
        "closer",
        "medium",
        "which is the cheapest place for it to break",
    ),
    (
        "clean-database-after.html",
        "emphasis-word",
        "low",
        "the protocol has a perfectly good error channel",
    ),
    ("clean-database-after.html", "dramatic-beat", "medium", "to try again. But nothing broke."),
    (
        "clean-database-after.html",
        "emphasis-word",
        "low",
        "The server did exactly what it was built to do.",
    ),
    (
        "clean-database-after.html",
        "antithesis",
        "medium",
        "The model doesn't need to know that the call failed; it needs to know what to do differently.",
    ),
    (
        "clean-database-after.html",
        "antithesis",
        "medium",
        "The cap isn't the interesting bit. What matters is",
    ),
    (
        "clean-database-after.html",
        "antithesis",
        "low",
        "On SQLite that's a rounding error and the field is nearly pointless. On Snowflake it's the whole bill",
    ),
    ("clean-database-after.html", "generic-detail", "medium", "by more than people expect"),
    (
        "clean-database-after.html",
        "antithesis",
        "medium",
        "None of those is really about MCP. They're about who's asking and how often.",
    ),
    (
        "clean-database-after.html",
        "emphasis-word",
        "medium",
        "which is genuinely the problem it exists to solve",
    ),
    (
        "clean-database-after.html",
        "fragment",
        "low",
        "Two things I'd tell someone doing this next.",
    ),
    (
        "clean-database-after.html",
        "antithesis",
        "low",
        "a database qualifies, a folder of text files doesn't",
    ),
    ("clean-database-after.html", "fragment", "low", "Nothing errors, nothing warns"),
    (
        "clean-database-after.html",
        "closer",
        "medium",
        "There's a lab in the backlog to measure it. I haven't run it.",
    ),
    # ---- clean: Which Protocol Is Your MCP Server Speaking?, after its rewrite ----------------
    (
        "clean-protocol-after.md",
        "emphasis-word",
        "low",
        "does exactly the negotiation you're trying to observe",
    ),
    (
        "clean-protocol-after.md",
        "emphasis-word",
        "low",
        "companies whose tools people actually run",
    ),
    # ---- held out: Double-Entry for Documents, whole post -------------------------------------
    (
        "heldout-double-entry.html",
        "triad",
        "high",
        "Nothing crashes, nothing warns you, and the answers keep coming.",
    ),
    ("heldout-double-entry.html", "cliche-emphasis", "high", "That difference is the entire idea."),
    (
        "heldout-double-entry.html",
        "antithesis",
        "high",
        "One number can only ever be a system grading its own homework. Two numbers, counted independently, can disagree.",
    ),
    (
        "heldout-double-entry.html",
        "dramatic-beat",
        "medium",
        "Your files go in. Some of them don't arrive.",
    ),
    ("heldout-double-entry.html", "dramatic-beat", "low", "Start from nothing."),
    ("heldout-double-entry.html", "dramatic-beat", "low", "This is a good design."),
    ("heldout-double-entry.html", "hedge", "medium", "product works roughly this way."),
    (
        "heldout-double-entry.html",
        "dramatic-beat",
        "high",
        "The trouble is entirely in step one, and it is invisible from step four.",
    ),
    ("heldout-double-entry.html", "antithesis", "high", "Not an error - an empty string."),
    ("heldout-double-entry.html", "hedge", "medium", "A great deal of extraction code opens a"),
    (
        "heldout-double-entry.html",
        "generic-detail",
        "medium",
        "The most popular way to read one walks the body and stops.",
    ),
    (
        "heldout-double-entry.html",
        "hedge",
        "low",
        "frequently the sentence that changes the meaning",
    ),
    ("heldout-double-entry.html", "emphasis-word", "low", "is simply not in the corpus"),
    ("heldout-double-entry.html", "antithesis", "high", "This is not hallucination."),
    ("heldout-double-entry.html", "closer", "high", "It is the missing passages that lie."),
    ("heldout-double-entry.html", "fragment", "low", "Because none of these raise an exception."),
    (
        "heldout-double-entry.html",
        "antithesis",
        "high",
        "What's needed is not a confession. It's a checksum.",
    ),
    (
        "heldout-double-entry.html",
        "triad",
        "low",
        "Count it twice, on purpose, by different routes",
    ),
    (
        "heldout-double-entry.html",
        "triad",
        "medium",
        "records every transaction twice, in two places, by two routes that must agree",
    ),
    (
        "heldout-double-entry.html",
        "antithesis",
        "high",
        "Not because the second entry is more accurate - because a single entry has nothing to be checked against.",
    ),
    (
        "heldout-double-entry.html",
        "closer",
        "high",
        "An error in one column is invisible; the same error in one of two columns is a mismatch.",
    ),
    ("heldout-double-entry.html", "cliche-emphasis", "low", "and more importantly it is"),
    (
        "heldout-double-entry.html",
        "cliche-emphasis",
        "high",
        "The independence is the whole mechanism.",
    ),
    ("heldout-double-entry.html", "fragment", "high", "A detail that matters more than it looks."),
    (
        "heldout-double-entry.html",
        "emphasis-word",
        "medium",
        "because they genuinely are a sequence",
    ),
    (
        "heldout-double-entry.html",
        "antithesis",
        "high",
        "This is not for speed. It is so that a parse killed",
    ),
    (
        "heldout-double-entry.html",
        "dramatic-beat",
        "medium",
        "Here is the trap that ordinary retrieval falls into.",
    ),
    ("heldout-double-entry.html", "emphasis-word", "medium", "there is literally nothing to rank"),
    (
        "heldout-double-entry.html",
        "antithesis",
        "high",
        "The system doesn't ignore it; it never knew it existed.",
    ),
    (
        "heldout-double-entry.html",
        "triad",
        "high",
        "You still have its name. You have the tab that came back empty, and that tab has a name. You have the error.",
    ),
    (
        "heldout-double-entry.html",
        "emphasis-word",
        "medium",
        "startlingly often the exact vocabulary",
    ),
    (
        "heldout-double-entry.html",
        "closer",
        "medium",
        "Pages and nodes are not interchangeable quantities.",
    ),
    ("heldout-double-entry.html", "reader-instruction", "high", "Note that it says ok on all"),
    (
        "heldout-double-entry.html",
        "closer",
        "high",
        "That is the whole problem, rendered as a column.",
    ),
    ("heldout-double-entry.html", "fragment", "high", "Same corpus, same index, two questions."),
    ("heldout-double-entry.html", "dramatic-beat", "medium", "coverage 1.00. That is correct."),
    (
        "heldout-double-entry.html",
        "emphasis-word",
        "low",
        "which is exactly the hole an index would inherit",
    ),
    (
        "heldout-double-entry.html",
        "fragment",
        "high",
        "Two different questions, both worth asking.",
    ),
    (
        "heldout-double-entry.html",
        "closer",
        "medium",
        "Stated plainly, because a tool about honest reporting that oversold itself would be a poor joke.",
    ),
    (
        "heldout-double-entry.html",
        "antithesis",
        "medium",
        "This catches wholesale loss, not quality degradation.",
    ),
    (
        "heldout-double-entry.html",
        "antithesis",
        "high",
        "an honest gap rather than a silent one - but a gap all the same",
    ),
    ("heldout-double-entry.html", "closer", "low", "This is the most valuable next thing."),
    ("heldout-double-entry.html", "restatement", "medium", "The point, restated"),
    ("heldout-double-entry.html", "hedge", "medium", "Almost nothing checks that promise"),
    ("heldout-double-entry.html", "triad", "medium", "no crash, no warning, plausible output"),
    (
        "heldout-double-entry.html",
        "closer",
        "high",
        "one number cannot be wrong, it can only be the number",
    ),
    (
        "heldout-double-entry.html",
        "fragment",
        "high",
        "MIT-adjacent in spirit, deterministic in the core, model-free where it counts.",
    ),
    # ---- held out: Where the Cut Falls, sections 1, 4, 7, 10 and 13 only ----------------------
    (
        "heldout-where-the-cut-falls.html",
        "hedge",
        "medium",
        "Most systems default to something arbitrary",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "closer",
        "medium",
        "And that works fine, right up until a cut lands in the middle of the sentence that holds the answer.",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "cliche-emphasis",
        "high",
        "That third cut is the whole problem.",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "cliche-emphasis",
        "high",
        "which is worse than useless, because it looks like an answer",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "antithesis",
        "high",
        "Counting characters is free. Asking a language model to read the document and decide is not.",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "hedge",
        "medium",
        "That last row is the one most write-ups get wrong",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "dramatic-beat",
        "high",
        "as though it were another way to cut. It is not.",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "fragment",
        "medium",
        "Which means any honest score has to say which of the two it measured.",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "antithesis",
        "low",
        "treating as one problem and which is really two",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "antithesis",
        "medium",
        "treated as the fixture having drifted, not as an improvement",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "triad",
        "medium",
        "no questions, no marked answers and no model at all",
    ),
    ("heldout-where-the-cut-falls.html", "fragment", "high", "The limit worth stating."),
    (
        "heldout-where-the-cut-falls.html",
        "antithesis",
        "high",
        "These can tell you a configuration is broken. They cannot tell you which of two reasonable configurations is better",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "closer",
        "medium",
        "Anything claiming a universal chunk-quality score without queries is overselling.",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "dramatic-beat",
        "high",
        "but not for the reason we expected. Next section.",
    ),
    ("heldout-where-the-cut-falls.html", "fragment", "high", "Fair challenge."),
    (
        "heldout-where-the-cut-falls.html",
        "cliche-emphasis",
        "low",
        "this whole piece is advice about the wrong knob",
    ),
    ("heldout-where-the-cut-falls.html", "dramatic-beat", "medium", "So we measured both."),
    (
        "heldout-where-the-cut-falls.html",
        "antithesis",
        "medium",
        "Never both at once - that measures neither.",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "antithesis",
        "high",
        'Read the middle column and the answer is "chunking, obviously." Read the last two together and it changes.',
    ),
    ("heldout-where-the-cut-falls.html", "dramatic-beat", "medium", "What differs is how often."),
    (
        "heldout-where-the-cut-falls.html",
        "antithesis",
        "high",
        "The two are not big and small. They are frequent and rare.",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "fragment",
        "low",
        'Which is a more useful thing to know than "chunking matters more"',
    ),
    (
        "heldout-where-the-cut-falls.html",
        "closer",
        "medium",
        "when it goes wrong it doesn't go slightly wrong",
    ),
    ("heldout-where-the-cut-falls.html", "emphasis-word", "low", "simply lost the answer"),
    ("heldout-where-the-cut-falls.html", "antithesis", "high", "It didn't degrade. It collapsed."),
    (
        "heldout-where-the-cut-falls.html",
        "fragment",
        "medium",
        "One tempting explanation that turned out to be wrong.",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "triad",
        "medium",
        "It reads well, it fits the two worst cases, and it is not true",
    ),
    (
        "heldout-where-the-cut-falls.html",
        "closer",
        "medium",
        "Worth saying out loud, because that paragraph very nearly got written the other way.",
    ),
]

HABITS = {
    "antithesis",
    "fragment",
    "triad",
    "dramatic-beat",
    "closer",
    "restatement",
    "cliche-emphasis",
    "generic-detail",
    "reader-instruction",
    "hedge",
    "emphasis-word",
}
SEVERITIES = {"high", "medium", "low"}


def normalise(text: str) -> str:
    """The comparison form shared by labels, drafts and reviewer findings."""
    text = html.unescape(text)
    # Inline tags vanish without leaving a space, so "<code>x</code>." stays "x.".
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # markdown links
    text = text.replace("`", "").replace("*", "")
    text = re.sub(r"[‘’]", "'", text)
    text = re.sub(r"[“”]", '"', text)
    text = re.sub(r"\s*[—–]\s*", " - ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text.strip().lower()


def prose_lines(path: Path) -> list[tuple[int, str]]:
    """(line number, normalised text) for prose lines, skipping code, style and svg."""
    out: list[tuple[int, str]] = []
    in_block = False
    front_matter = 0
    for number, raw in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if path.suffix == ".md":
            if raw.strip() == "---" and front_matter < 2:
                front_matter += 1
                continue
            if front_matter < 2:
                continue
            if raw.strip().startswith("```"):
                in_block = not in_block
                continue
            if in_block:
                continue
        else:
            if re.search(r"<(style|pre|script|svg)\b", raw):
                in_block = True
            if in_block:
                if re.search(r"</(style|pre|script|svg)>", raw):
                    in_block = False
                continue
        text = normalise(raw)
        if text:
            out.append((number, text))
    return out


def locate(lines: list[tuple[int, str]], quote: str) -> list[int]:
    """Every line on which the normalised quote begins."""
    joined, starts = "", []
    for number, text in lines:
        starts.append((len(joined), number))
        joined += text + " "
    needle = normalise(quote)
    hits, i = [], joined.find(needle)
    while i != -1:
        hits.append(max(n for offset, n in starts if offset <= i))
        i = joined.find(needle, i + 1)
    return hits


def build() -> dict:
    cache = {name: prose_lines(DRAFTS / name) for name in DRAFT_META}
    labels, problems = [], []
    counters: dict[str, int] = {}
    for draft, habit, severity, quote in LABELS:
        assert habit in HABITS, habit
        assert severity in SEVERITIES, severity
        hits = locate(cache[draft], quote)
        if len(hits) != 1:
            problems.append(f"{draft}: {len(hits)} matches for {quote!r}")
            continue
        line = hits[0]
        ranges = DRAFT_META[draft].get("scored_line_ranges")
        if ranges and not any(lo <= line <= hi for lo, hi in ranges):
            problems.append(f"{draft}: line {line} is outside the scored sections: {quote!r}")
        counters[draft] = counters.get(draft, 0) + 1
        prefix = draft.split(".")[0]
        labels.append(
            {
                "id": f"{prefix}-{counters[draft]:02d}",
                "draft": draft,
                "line": line,
                "habit": habit,
                "severity": severity,
                "quote": quote,
            }
        )
    if problems:
        raise SystemExit("label problems:\n  " + "\n  ".join(problems))
    return {
        "drafts": DRAFT_META,
        "scoring": {
            "match": "same draft; normalised quotes share a run of at least 20 characters, "
            "or one contains the other when a quote is shorter than 20",
            "recall_counts": ["high", "medium"],
            "neutral": ["low"],
        },
        "labels": labels,
    }


if __name__ == "__main__":
    data = build()
    (HERE / "labels.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    by_draft: dict[str, dict[str, int]] = {}
    for label in data["labels"]:
        d = by_draft.setdefault(label["draft"], {"high": 0, "medium": 0, "low": 0})
        d[label["severity"]] += 1
    print(f"{len(data['labels'])} labels, every quote found exactly once")
    for draft, counts in by_draft.items():
        print(
            f"  {draft:<36} high {counts['high']:>2}  medium {counts['medium']:>2}  low {counts['low']:>2}"
        )
