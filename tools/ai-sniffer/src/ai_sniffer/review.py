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


def build_request(prompt: str, path: Path, linter_report: dict | None) -> str:
    lines = path.read_text(encoding="utf-8").split("\n")
    width = len(str(len(lines)))
    numbered = "\n".join(f"{n:>{width}} | {line}" for n, line in enumerate(lines, 1))
    if linter_report is None:
        linter = "No linter report is included. Find the word-level habits yourself."
    else:
        linter = (
            "The linter has already run. Its report is below; use it for the word-level "
            "habits.\n\n```json\n"
            + json.dumps(linter_report, indent=2, ensure_ascii=False)
            + "\n```"
        )
    return (
        f"{prompt.rstrip()}\n\n---\n\n"
        "You can't run commands for this review; everything you need is here.\n\n"
        f"{linter}\n\n"
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


def run(path: Path, model: str, linter_report: dict | None) -> dict:
    provider = chat_provider(model)
    request = build_request(load_prompt(), path, linter_report)
    try:
        reply = provider.complete(request, max_tokens=MAX_TOKENS)
    except Exception as exc:  # a missing backend, auth, network: each provider raises its own
        raise Unavailable(f"the model call failed: {exc}") from exc
    try:
        findings, invalid, summary = parse_reply(reply)
    except ReplyError as exc:
        exc.reply = reply
        raise
    return {
        "path": str(path),
        "model": model,
        "linter": linter_report is not None,
        "findings": findings,
        "invalid": invalid,
        "summary": summary,
    }
