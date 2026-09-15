"""Run the reviewer prompt through a configured model.

The prompt is the agent file with its frontmatter stripped, so the Claude Code agent
and this command can't drift apart. The model comes from ``--model`` or
``DATA_TOOLS_CHAT_MODEL`` and runs through ``data_tools_core.llm``, which is only
installed with the ``llm`` extra. Nothing here falls back quietly: no model means no
review, and the command says how to get one.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import replace
from importlib import resources
from pathlib import Path
from typing import Any

_FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)
_JSON_FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.S)
_REQUIRED = ("line", "habit", "severity", "quote")
MAX_TOKENS = 16000

NO_MODEL = (
    "no model is configured for review. Either run the Claude Code agent "
    "(agent/ai-sniffer.md) on the draft, or set DATA_TOOLS_CHAT_MODEL to a LiteLLM "
    "model string, for example anthropic/claude-haiku-4-5-20251001 with a key in "
    "DATA_TOOLS_API_KEY, and install the llm extra."
)


class Unavailable(RuntimeError):
    """No model backend can run: the extra isn't installed, or the call failed."""


class ReplyError(ValueError):
    """The model's reply didn't contain the JSON block the prompt asks for."""


def _agent_file() -> Path:
    packaged = resources.files("ai_sniffer") / "agent" / "ai-sniffer.md"
    if packaged.is_file():
        return Path(str(packaged))
    return Path(__file__).resolve().parents[2] / "agent" / "ai-sniffer.md"


def load_prompt() -> str:
    return _FRONTMATTER.sub("", _agent_file().read_text(encoding="utf-8"), count=1).lstrip()


CHUNK_MIN_WORDS = 400


def chunk_ranges(path: Path, min_words: int = CHUNK_MIN_WORDS) -> list[tuple[int, int]]:
    """Line ranges, one per section, with sections under min_words merged into the next."""
    from .document import read
    from .signals import words

    total = len(path.read_text(encoding="utf-8").split("\n"))
    sections = []
    for section in read(path).sections:
        lines = [p.line for p in section.paragraphs]
        start = section.line if section.heading else (min(lines) if lines else section.line)
        count = sum(len(words(p.text)) for p in section.paragraphs)
        sections.append((start, count))
    starts: list[int] = []
    pending, pending_words = None, 0
    for start, count in sorted(sections):
        pending = start if pending is None else pending
        pending_words += count
        if pending_words >= min_words:
            starts.append(pending)
            pending, pending_words = None, 0
    if pending is not None and not starts:
        starts.append(pending)
    return [
        (a, (starts[i + 1] - 1) if i + 1 < len(starts) else total) for i, a in enumerate(starts)
    ]


def build_request(
    prompt: str,
    path: Path,
    linter_report: dict | None,
    lines: tuple[int, int] | None = None,
    part: tuple[int, int] | None = None,
) -> str:
    all_lines = path.read_text(encoding="utf-8").split("\n")
    width = len(str(len(all_lines)))
    first, last = lines or (1, len(all_lines))
    numbered = "\n".join(
        f"{n:>{width}} | {line}" for n, line in enumerate(all_lines, 1) if first <= n <= last
    )
    if linter_report is not None and lines is not None:
        linter_report = {
            **linter_report,
            **{
                key: [x for x in linter_report.get(key, []) if first <= x.get("line", 0) <= last]
                for key in ("findings", "closers")
            },
        }
    if linter_report is None:
        linter = "No linter report is included. Find the word-level habits yourself."
    else:
        linter = (
            "The linter has already run. Its report is below; use it for the word-level "
            "habits.\n\n```json\n"
            + json.dumps(linter_report, indent=2, ensure_ascii=False)
            + "\n```"
        )
    scope = ""
    if part is not None:
        scope = (
            f"This is part {part[0]} of {part[1]} of the draft, lines {first} to {last}. "
            "Review only these lines; the other parts are reviewed separately.\n\n"
        )
    return (
        f"{prompt.rstrip()}\n\n---\n\n"
        "You can't run commands for this review; everything you need is here.\n\n"
        f"{scope}{linter}\n\n"
        f"The draft is {path.name}. Each line starts with its line number and a bar, "
        "which aren't part of the text.\n\n"
        f"{numbered}\n"
    )


def parse_reply(reply: str) -> tuple[list[dict], list[Any], str]:
    match = _JSON_FENCE.search(reply)
    if not match:
        raise ReplyError("the reply has no ```json block")
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ReplyError(f"the json block doesn't parse: {exc}") from exc
    entries = data.get("findings") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise ReplyError("the json block has no findings list")
    findings, invalid = [], []
    for entry in entries:
        ok = isinstance(entry, dict) and all(k in entry for k in _REQUIRED)
        if ok and isinstance(entry["line"], int):
            findings.append(entry)
        else:
            invalid.append(entry)
    summary = (reply[: match.start()] + reply[match.end() :]).strip()
    return findings, invalid, summary


def resolve_model(flag: str | None) -> str | None:
    """--model, then DATA_TOOLS_CHAT_MODEL, then a non-default model in .env."""
    if flag:
        return flag
    if model := os.environ.get("DATA_TOOLS_CHAT_MODEL"):
        return model
    try:
        from data_tools_core.config import DEFAULT_CHAT_MODEL, get_settings
    except ImportError:
        return None
    configured = get_settings().chat_model
    return configured if configured != DEFAULT_CHAT_MODEL else None


def chat_provider(model: str):
    """The one lazy backend accessor; tests replace it with a fake."""
    try:
        from data_tools_core.config import get_settings
        from data_tools_core.llm import get_chat_provider
    except ImportError as exc:
        raise Unavailable(
            "the llm extra isn't installed: install data-tools-ai-sniffer[llm]"
        ) from exc
    return get_chat_provider(replace(get_settings(), chat_model=model))


def _ask(provider, request: str) -> tuple[list[dict], list[Any], str]:
    try:
        reply = provider.complete(request, max_tokens=MAX_TOKENS)
    except Exception as exc:  # a missing backend, auth, network: each provider raises its own
        raise Unavailable(f"the model call failed: {exc}") from exc
    try:
        return parse_reply(reply)
    except ReplyError as exc:
        exc.reply = reply
        raise


def run(path: Path, model: str, linter_report: dict | None, chunk: bool = False) -> dict:
    provider = chat_provider(model)
    prompt = load_prompt()
    result = {"path": str(path), "model": model, "linter": linter_report is not None}
    if not chunk:
        findings, invalid, summary = _ask(provider, build_request(prompt, path, linter_report))
        return result | {"findings": findings, "invalid": invalid, "summary": summary}
    ranges = chunk_ranges(path)
    findings, invalid, summaries = [], [], []
    for k, lines in enumerate(ranges, 1):
        request = build_request(prompt, path, linter_report, lines=lines, part=(k, len(ranges)))
        f, inv, summary = _ask(provider, request)
        findings += f
        invalid += inv
        summaries.append(f"Lines {lines[0]} to {lines[1]}: {summary}")
    return result | {
        "chunks": len(ranges),
        "findings": findings,
        "invalid": invalid,
        "summary": "\n\n".join(summaries),
    }
