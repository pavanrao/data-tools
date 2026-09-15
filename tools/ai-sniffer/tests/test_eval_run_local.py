"""Local model runs: the same request as `ai-sniffer review`, with the cost of each run recorded."""

from __future__ import annotations

import json

import pytest

REPLY = '```json\n{"findings": []}\n```\n\nNothing found.'


@pytest.fixture
def local(eval_script):
    return eval_script("run_local")


class FakeOllama:
    def __init__(self, prompt_tokens=900, reply=REPLY):
        self.calls = []
        self.prompt_tokens = prompt_tokens
        self.reply = reply

    def __call__(self, path, body):
        self.calls.append((path, body))
        if path == "/api/show":
            return {
                "details": {"parameter_size": "7.6B", "quantization_level": "Q4_K_M"},
                "digest": "abc",
            }
        return {
            "message": {"content": self.reply},
            "prompt_eval_count": self.prompt_tokens,
            "eval_count": 40,
            "prompt_eval_duration": 8_000_000_000,
            "eval_duration": 2_000_000_000,
            "total_duration": 11_000_000_000,
        }


def test_a_run_records_tokens_time_and_quantization(local):
    ollama = FakeOllama()

    reply, meta = local.run_one("qwen2.5:7b", "the request", num_ctx=32768, post=ollama)

    assert reply == REPLY
    assert meta["model"] == "qwen2.5:7b"
    assert meta["quantization"] == "Q4_K_M"
    assert (meta["prompt_tokens"], meta["output_tokens"]) == (900, 40)
    assert meta["seconds"] == {"prompt": 8.0, "output": 2.0, "total": 11.0}
    assert meta["truncated"] is False
    (_, body) = ollama.calls[-1]
    assert body["options"]["num_ctx"] == 32768 and body["stream"] is False


def test_a_prompt_that_fills_the_context_window_is_flagged_as_truncated(local):
    _, meta = local.run_one("qwen2.5:7b", "x", num_ctx=1000, post=FakeOllama(prompt_tokens=1000))

    assert meta["truncated"] is True


def test_requests_use_neutral_names_and_the_linter_report_only_when_asked(local, tmp_path):
    drafts = {"draft-1.md": "heldout-secret.md"}
    source = tmp_path / "src"
    source.mkdir()
    (source / "heldout-secret.md").write_text("Note that this matters.\n")

    with local.neutral_inputs(drafts, source) as inputs:
        plain = local.request_for(inputs, "draft-1.md", linter=False)
        with_report = local.request_for(inputs, "draft-1.md", linter=True)

    assert "heldout-secret" not in plain and "draft-1.md" in plain
    assert "1 | Note that this matters." in plain
    assert "No linter report" in plain
    assert '"reader-instruction"' in with_report


def test_runs_are_written_beside_their_metadata_and_existing_runs_are_skipped(local, tmp_path):
    ollama = FakeOllama()
    drafts = {"draft-1.md": "heldout-secret.md"}
    source = tmp_path / "src"
    source.mkdir()
    (source / "heldout-secret.md").write_text("It collapsed.\n")
    runs = tmp_path / "runs"

    written = local.run_setup(
        "qwen7", "qwen2.5:7b", drafts, source, runs, [1], linter=False, num_ctx=4096, post=ollama
    )
    again = local.run_setup(
        "qwen7", "qwen2.5:7b", drafts, source, runs, [1], linter=False, num_ctx=4096, post=ollama
    )

    out = runs / "qwen7" / "heldout-secret"
    assert (out / "run-1.md").read_text() == REPLY
    assert json.loads((out / "run-1.meta.json").read_text())["draft"] == "heldout-secret.md"
    assert written == 1 and again == 0
    assert sum(1 for path, _ in ollama.calls if path == "/api/chat") == 1


def test_the_scorer_ignores_metadata_files(eval_script, tmp_path):
    score = eval_script("score")
    (tmp_path / "run-1.md").write_text(REPLY)
    (tmp_path / "run-1.meta.json").write_text("{}")

    assert [p.name for p in score.run_files(tmp_path)] == ["run-1.md"]


def test_a_chunked_run_writes_one_merged_reply_and_sums_its_cost(local, eval_script, tmp_path):
    ollama = FakeOllama(
        reply='```json\n{"findings": [{"line": 1, "habit": "hedge", "severity": "low", '
        '"quote": "Plenty of", "why": ""}]}\n```\n\nOne.'
    )
    source = tmp_path / "src"
    source.mkdir()
    body = "\n\n".join(["Plenty of words. " * 150, "## Two", "Plenty of words. " * 150]) + "\n"
    (source / "heldout-secret.md").write_text(body)
    runs = tmp_path / "runs"

    local.run_setup(
        "qwen7+chunks", "qwen2.5:7b", {"draft-1.md": "heldout-secret.md"}, source, runs, [1],
        linter=False, num_ctx=4096, post=ollama, chunk=True,
    )  # fmt: skip

    out = runs / "qwen7+chunks" / "heldout-secret"
    meta = json.loads((out / "run-1.meta.json").read_text())
    findings, ok = eval_script("score").read_run(out / "run-1.md")
    assert meta["chunks"] == 2
    assert (meta["prompt_tokens"], meta["output_tokens"]) == (1800, 80)
    assert ok and len(findings) == 2
